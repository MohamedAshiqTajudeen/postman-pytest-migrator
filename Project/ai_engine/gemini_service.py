import os
import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from google import genai
from google.genai import types
from google.genai.errors import APIError

# Setup logger
logger = logging.getLogger("GeminiService")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


class RuleBasedConverter:
    """
    Translates common Postman JavaScript assertions directly to executable Python Pytest statements
    using pattern-matching rules. Enables faster conversions, avoids API rate limits,
    and works Offline/Local.
    """

    def __init__(self) -> None:
        # Define sequential rule regex matchers and their corresponding lambda translators
        self.rules = [
            # 1. Status Code: pm.response.to.have.status(200) or pm.response.to.have.status(201)
            (
                r"pm\.response\.to\.have\.status\(\s*(\d+)\s*\)",
                lambda match: f"assert response.status_code == {match.group(1)}"
            ),
            # 2. Status Code expect: pm.expect(pm.response.code).to.equal(200)
            (
                r"pm\.expect\(\s*pm\.response\.code\s*\)\.to\.(?:equal|be|eq)\(\s*(\d+)\s*\)",
                lambda match: f"assert response.status_code == {match.group(1)}"
            ),
            # 3. Status Code (Legacy): responseCode.code === 200 / == 200
            (
                r"responseCode\.code\s*===\s*(\d+)",
                lambda match: f"assert response.status_code == {match.group(1)}"
            ),
            (
                r"responseCode\.code\s*==\s*(\d+)",
                lambda match: f"assert response.status_code == {match.group(1)}"
            ),
            # 4. Status success checking (Legacy): tests["Status"] = responseCode.code === 200
            (
                r"tests\s*\[\s*['\"]([^'\"]+)['\"]\s*\]\s*=\s*(?:responseCode\.code|pm\.response\.code)\s*(?:===|==)\s*(\d+)",
                lambda match: f"assert response.status_code == {match.group(2)}"
            ),
            # 5. Header checking (Presence): pm.response.to.have.header("Content-Type")
            (
                r"pm\.response\.to\.have\.header\(\s*['\"]([^'\"]+)['\"]\s*\)",
                lambda match: f"assert '{match.group(1)}' in response.headers"
            ),
            # 6. Header checking (Value): pm.expect(pm.response.headers.get("Content-Type")).to.equal("application/json")
            (
                r"pm\.expect\(\s*pm\.response\.headers\.get\(\s*['\"]([^'\"]+)['\"]\s*\)\s*\)\.to\.(?:equal|be|eq)\(\s*['\"]([^'\"]+)['\"]\s*\)",
                lambda match: f"assert response.headers.get('{match.group(1)}') == '{match.group(2)}'"
            ),
            # 7. Header checking v2: pm.response.to.have.header("Content-Encoding", "gzip")
            (
                r"pm\.response\.to\.have\.header\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)",
                lambda match: f"assert response.headers.get('{match.group(1)}') == '{match.group(2)}'"
            ),
            # 8. JSON Body Response presence: pm.response.to.have.jsonBody()
            (
                r"pm\.response\.to\.have\.jsonBody\(\)",
                lambda match: "assert response.json() is not None"
            ),
            # 9. JSON value eql: pm.expect(jsonData.id).to.eql(123) / equal(123)
            (
                r"pm\.expect\(\s*jsonData\.(\w+)\s*\)\.to\.(?:eql|equal|be|eq)\(\s*([^\s)]+)\s*\)",
                lambda match: f"assert jsonData.get('{match.group(1)}') == {match.group(2)}"
            ),
            # 10. JSON nested index value eql: pm.expect(jsonData.user.id).to.eql(123)
            (
                r"pm\.expect\(\s*jsonData\.(\w+)\.(\w+)\s*\)\.to\.(?:eql|equal|be|eq)\(\s*([^\s)]+)\s*\)",
                lambda match: f"assert jsonData.get('{match.group(1)}', {{}}).get('{match.group(2)}') == {match.group(3)}"
            ),
            # 11. Array/List length: pm.expect(jsonData.items).to.have.lengthOf(5)
            (
                r"pm\.expect\(\s*jsonData\.(\w+)\s*\)\.to\.have\.lengthOf\(\s*(\d+)\s*\)",
                lambda match: f"assert len(jsonData.get('{match.group(1)}', [])) == {match.group(2)}"
            ),
            # 12. Response time: pm.expect(pm.response.responseTime).to.be.below(500)
            (
                r"pm\.expect\(\s*pm\.response\.responseTime\s*\)\.to\.be\.below\(\s*(\d+)\s*\)",
                lambda match: f"assert response.elapsed.total_seconds() * 1000 < {match.group(1)}"
            )
        ]

    def convert_line(self, raw_line: str) -> Optional[str]:
        """
        Attempts to translate a single JS assertion statement using pattern matching.
        """
        clean_line = raw_line.strip()
        
        # Strip trailing semicolon for simplified matched states
        if clean_line.endswith(";"):
            clean_line = clean_line[:-1].strip()

        for pattern, action in self.rules:
            match = re.search(pattern, clean_line)
            if match:
                try:
                    return action(match)
                except Exception as e:
                    logger.warning(f"Error executing rule matching translator: {str(e)}")
                    continue
        return None


class GeminiServiceClient:
    """
    Submits complex, multi-line JS script assertions or unsupported structures
    to Gemini AI via prompt templates for logical migration to Pytest functions.
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = "gemini-3.5-flash"  # Default recommended model for text/reasoning migration tasks
        
        # Initialize Google GenAI client
        if self.api_key:
            try:
                # Instantiating client according to @google/genai guidelines
                self.client = genai.Client(api_key=self.api_key)
                logger.info("Successfully initialized Gemini GenAI Client.")
            except Exception as e:
                logger.error(f"Failed to instantiate Gemini GenAI Client: {str(e)}")
                self.client = None
        else:
            logger.warning("No GEMINI_API_KEY environment variable detected. Running in Offline-Only Mode.")
            self.client = None

    def convert_complex_script_via_ai(self, js_code_block: str, request_context: Dict[str, Any]) -> str:
        """
        Calls Gemini using a specialized translation prompt to translate JS to Pytest assert lines.
        """
        if not self.client:
            logger.warning("Gemini Client is uninitialized. Resorting to rule-based or empty fallbacks.")
            return "# [AI Offline Fallback] Could not convert complex logic due to missing API key."

        # Reconstruct specialized prompt
        prompt = f"""
You are an expert QA Automation Engineer, Python developer, and Postman to Pytest Migrator.
Convert the following Postman API request test code block (JavaScript) into high-quality, executable Python Pytest assertions.

### Request Context:
- Method: {request_context.get('method', 'GET')}
- Endpoint: {request_context.get('endpoint', '')}
- API Name: {request_context.get('api_name', 'Unnamed API')}

### JavaScript Postman Code to Convert:
```javascript
{js_code_block}
```

### Pytest Translation Guidelines:
1. Target response attributes directly using standard Python 'requests' style syntax (e.g., use `response.status_code`, `response.json()`, `response.headers`).
2. If the JS code declares references like `var jsonData = pm.response.json();`, assume that `jsonData = response.json()` is available.
3. Keep the checks Pythonic, clean, and exact. Include descriptive inline comments explain the conversion.
4. Output ONLY valid, executable Python lines of code. Do not output anything else (no markdown wraps, no conversational explanations, just the raw code lines).
"""

        try:
            logger.info("Submitting custom JS script to Gemini client for synthesis.")
            
            # Using client.models.generate_content (the correct Python GenAI layout)
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    system_instruction="You are a strict, ultra-precise Python compiler that outputs pure, clean, raw Pytest code blocks of assertion statements."
                )
            )

            result_text = response.text
            if not result_text:
                return "# [AI Failed] Model returned empty content translation."

            # Strip any markdown code fences if outputted accidentally
            clean_code = re.sub(r"```[pP]ython\n", "", result_text)
            clean_code = re.sub(r"```\n?", "", clean_code)
            return clean_code.strip()

        except APIError as ae:
            logger.error(f"Gemini API invocation failed: {str(ae)}")
            return f"# [AI Conversion Service Temporarily Unavailable] API Error: {str(ae)}"
        except Exception as ex:
            logger.error(f"Unexpected error when calling Gemini API: {str(ex)}")
            return f"# [AI Failure Error] {str(ex)}"


class HybridConversionEngine:
    """
    Orchestrates the conversion pipeline:
    Filters assertions sequentially through the high-speed local Rule-Based Engine first.
    If any complex loops or unknown functions are detected, it streams those to Gemini AI.
    Integrates results seamlessly back to form unified pytest assertion lists.
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.rules_engine = RuleBasedConverter()
        self.ai_engine = GeminiServiceClient(api_key=api_key)

    def convert_api_assertions(self, api_detail: Dict[str, Any]) -> List[str]:
        """
        Converts the JS scripts associated with an API detail into ready-to-run Pytest assertion string statements.

        Args:
            api_detail: Structured item dictionary containing extracted requests and test scripts.

        Returns:
            List of Python Pytest assertions as individual executable strings.
        """
        raw_scripts = api_detail.get("raw_test_scripts", [])
        if not raw_scripts:
            # Let's fallback to generating basic standard status code validation if none exist
            return ["assert response.status_code == 200  # Default assertion"]

        converted_statements: List[str] = []
        is_complex = False
        complex_accumulator: List[str] = []

        # Analyze line-by-line of postman test scripts
        for raw_line in raw_scripts:
            # Clean comments and trailing carriage returns
            clean_line = raw_line.strip()
            if not clean_line or clean_line.startswith("//") or clean_line.startswith("/*") or clean_line.startswith("*"):
                continue

            # Check complex patterns indicating JS control structures (loops, scopes, functions)
            if any(term in clean_line for term in ["for", "while", "if (", "function", "try {", ".forEach"]):
                is_complex = True
            
            # Attempt rule conversion
            statement = self.rules_engine.convert_line(clean_line)
            if statement:
                converted_statements.append(statement)
            else:
                # Collect remaining statements for compilation
                if clean_line:
                    complex_accumulator.append(clean_line)

        # Let's run a hybrid validation branch
        if is_complex and complex_accumulator:
            logger.info("Complex logical statements detected. Invoking Gemini AI for Hybrid reasoning.")
            request_context = {
                "method": api_detail.get("method", "GET"),
                "endpoint": api_detail.get("endpoint", ""),
                "api_name": api_detail.get("api_name", "API Request")
            }
            unified_js_block = "\n".join(complex_accumulator)
            ai_generated_code = self.ai_engine.convert_complex_script_via_ai(unified_js_block, request_context)
            
            if ai_generated_code:
                # Add comment and split assertions dynamically
                converted_statements.append("# AI-Powered Complex Assertions:")
                for line in ai_generated_code.split("\n"):
                    if line.strip():
                        converted_statements.append(line)
        elif complex_accumulator:
            # Code is not structurally complex but was not parsed by simple regex lines (unsupported format)
            # Send to Gemini to ensure 100% conversion correctness
            logger.info("Unidentified simple formats spotted. Submitting to Gemini to guarantee precision.")
            request_context = {
                "method": api_detail.get("method", "GET"),
                "endpoint": api_detail.get("endpoint", ""),
                "api_name": api_detail.get("api_name", "API Request")
            }
            unified_js_block = "\n".join(complex_accumulator)
            ai_generated_code = self.ai_engine.convert_complex_script_via_ai(unified_js_block, request_context)
            
            if ai_generated_code:
                converted_statements.append("# Converted via Gemini AI Conversion Module:")
                for line in ai_generated_code.split("\n"):
                    if line.strip():
                        converted_statements.append(line)

        return converted_statements
