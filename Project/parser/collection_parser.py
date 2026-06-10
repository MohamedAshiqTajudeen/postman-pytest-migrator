import json
import re
import logging
from typing import Dict, Any, List, Optional

# Setup logger
logger = logging.getLogger("CollectionParser")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


class CollectionParser:
    """
    Parser for Postman Collection JSON files (v2.1).
    Extracts collection metadata, variables, request details, headers, query parameters,
    body payloads, authorization schemes, and raw Javascript test scripts to detect assertions.
    """

    def __init__(self) -> None:
        self.assertions_patterns = [
            # pm.response.to.have.status(200)
            (r"pm\.response\.to\.have\.status\(\s*(\d+)\s*\)", "Status Code Assertion"),
            # pm.expect(pm.response.code).to.equal(200) or .to.be(200)
            (r"pm\.expect\(\s*pm\.response\.code\s*\)\.to\.(?:equal|be|eq)\(\s*(\d+)\s*\)", "Status Code Expectation"),
            # responseCode.code === 200 or responseCode.code == 200
            (r"responseCode\.code\s*===\s*(\d+)", "Legacy Status Code Assertion"),
            (r"responseCode\.code\s*==\s*(\d+)", "Legacy Status Code Assertion"),
            # pm.response.to.have.header("Content-Type")
            (r"pm\.response\.to\.have\.header\(\s*['\"]([^'\"]+)['\"]\s*\)", "Header Presence Assertion"),
            # pm.response.to.have.jsonBody()
            (r"pm\.response\.to\.have\.jsonBody\(\s*['\"]?([^'\")]+)?['\"]?\s*\)", "JSON Body Assertion"),
            # pm.expect(jsonData.id).to.eql(123)
            (r"pm\.expect\(([^)]+)\)\.to\.(?:equal|eql|be|include|have)\(([^)]+)\)", "Generic Value Expectation"),
            # tests["Status code is 200"] = responseCode.code === 200
            (r"tests\s*\[\s*['\"]([^'\"]+)['\"]\s*\]\s*=", "Legacy tests[] Assertion")
        ]

    def parse_collection(self, collection_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parses a Postman Collection dict representation and returns structured API details.

        Args:
            collection_data: Raw JSON dictionary imported from Postman Collection.

        Returns:
            Structured dictionary of the extracted data.
        """
        logger.info("Starting collection import parsing.")

        info_block = collection_data.get("info", {})
        collection_name = info_block.get("name", "Unnamed Postman Collection")
        schema_url = info_block.get("schema", "")
        
        # Parse collection level variables
        collection_variables = []
        for var in collection_data.get("variable", []):
            collection_variables.append({
                "key": var.get("key", ""),
                "value": str(var.get("value", "")),
                "type": var.get("type", "string")
            })

        apis_extracted: List[Dict[str, Any]] = []
        
        # Postman item arrays can have folders nested inside folder recursively.
        items = collection_data.get("item", [])
        self._extract_items_recursive(items, apis_extracted, parent_auth=collection_data.get("auth"))

        # Calculate statistics
        total_apis = len(apis_extracted)
        total_assertions = sum(len(api["assertions"]) for api in apis_extracted)

        logger.info(f"Parsing complete. Extracted {total_apis} API requests with {total_assertions} overall assertions.")

        return {
            "collection_name": collection_name,
            "schema_version": "v2.1" if "v2.1.0" in schema_url else "v2.0/Unknown",
            "total_apis": total_apis,
            "total_assertions": total_assertions,
            "variables": collection_variables,
            "apis": apis_extracted
        }

    def _extract_items_recursive(self, items: List[Dict[str, Any]], apis_list: List[Dict[str, Any]], parent_auth: Optional[Dict[str, Any]] = None) -> None:
        """
        Recursively steps through the tree structure of Postman collection folder items.
        """
        for item in items:
            # If item contains nested items, it is a Folder
            if "item" in item:
                folder_auth = item.get("auth", parent_auth)
                self._extract_items_recursive(item["item"], apis_list, parent_auth=folder_auth)
            # Else it's an API request object
            elif "request" in item:
                request_data = item.get("request", {})
                
                # Fetch basic properties
                api_name = item.get("name", "Unnamed Request")
                method = request_data.get("method", "GET").upper()
                
                # Extract URL/Endpoint
                endpoint = self._extract_endpoint(request_data.get("url", ""))

                # Fetch Headers
                headers = self._extract_headers(request_data.get("header", []))

                # Fetch Query Params
                query_params = self._extract_query_params(request_data.get("url", {}))

                # Fetch Request Body
                request_body = self._extract_request_body(request_data.get("body", {}))

                # Fetch Auth (Request level takes priority over item/collection level)
                auth_details = request_data.get("auth") or parent_auth

                # Parse event scripts (Pre-request and Tests)
                test_scripts, pre_scripts = self._extract_events(item.get("event", []))

                # Analyze test scripts to identify assertions
                assertions = self._analyze_assertions(test_scripts)

                apis_list.append({
                    "api_name": api_name,
                    "method": method,
                    "endpoint": endpoint,
                    "headers": json.dumps(headers),
                    "request_body": request_body,
                    "query_params": json.dumps(query_params),
                    "auth": json.dumps(auth_details) if auth_details else None,
                    "raw_test_scripts": test_scripts,
                    "raw_pre_scripts": pre_scripts,
                    "assertions": assertions
                })

    def _extract_endpoint(self, url_field: Any) -> str:
        """
        Extracts raw endpoint string from diverse Postman URL representation formats.
        """
        if isinstance(url_field, str):
            return url_field
        
        if isinstance(url_field, dict):
            raw_url = url_field.get("raw")
            if raw_url:
                return str(raw_url)
            
            # Reconstruct from host and path lists if raw is not present
            host_list = url_field.get("host", [])
            path_list = url_field.get("path", [])
            
            host = ".".join(host_list) if isinstance(host_list, list) else str(host_list)
            path = "/".join(path_list) if isinstance(path_list, list) else str(path_list)
            
            protocol = url_field.get("protocol", "http")
            port = url_field.get("port", "")
            
            port_suffix = f":{port}" if port else ""
            return f"{protocol}://{host}{port_suffix}/{path}"
            
        return ""

    def _extract_headers(self, header_list: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Extracts headers from Postman request object list.
        """
        extracted = []
        for header in header_list:
            # Skip disabled headers
            if header.get("disabled", False):
                continue
            extracted.append({
                "key": header.get("key", ""),
                "value": header.get("value", ""),
                "description": header.get("description", "")
            })
        return extracted

    def _extract_query_params(self, url_field: Any) -> List[Dict[str, str]]:
        """
        Extract query parameters explicitly specified in the Postman URL structure.
        """
        extracted = []
        if isinstance(url_field, dict):
            query_list = url_field.get("query", [])
            for q in query_list:
                if q.get("disabled", False):
                    continue
                extracted.append({
                    "key": q.get("key", ""),
                    "value": q.get("value", ""),
                    "description": q.get("description", "")
                })
        return extracted

    def _extract_request_body(self, body_field: Dict[str, Any]) -> str:
        """
        Extracts and converts request bodies into serialized JSON or raw representation.
        """
        if not body_field:
            return ""

        mode = body_field.get("mode")
        if not mode:
            return ""

        if mode == "raw":
            return body_field.get("raw", "")
        elif mode == "urlencoded":
            params = body_field.get("urlencoded", [])
            kv_pairs = {p.get("key"): p.get("value") for p in params if not p.get("disabled")}
            return json.dumps(kv_pairs)
        elif mode == "formdata":
            params = body_field.get("formdata", [])
            form_list = []
            for p in params:
                if p.get("disabled"):
                    continue
                form_list.append({
                    "key": p.get("key", ""),
                    "value": p.get("value", "") if p.get("type") != "file" else "[File: " + p.get("src", "") + "]"
                })
            return json.dumps(form_list)
        return ""

    def _extract_events(self, events: List[Dict[str, Any]]) -> tuple[List[str], List[str]]:
        """
        Extracts JavaScript source blocks representing pre-request and test activities.
        """
        test_scripts: List[str] = []
        pre_scripts: List[str] = []

        for event in events:
            listen = event.get("listen")
            script_block = event.get("script", {})
            exec_lines = script_block.get("exec", [])

            # Postman scripts can be single string or array of script lines
            final_lines: List[str] = []
            if isinstance(exec_lines, str):
                final_lines = [exec_lines]
            elif isinstance(exec_lines, list):
                final_lines = [str(line) for line in exec_lines]

            if listen == "test":
                test_scripts.extend(final_lines)
            elif listen == "prerequest":
                pre_scripts.extend(final_lines)

        return test_scripts, pre_scripts

    def _analyze_assertions(self, script_lines: List[str]) -> List[Dict[str, Any]]:
        """
        Processes JS script blocks line-by-line using regexes to extract Postman assertions.
        """
        assertions = []
        combined_script = "\n".join(script_lines)

        # 1. Look for pm.test block structures to identify test suites/case boundaries
        # Pattern: pm.test("Test title", function(...) { assertions })
        pm_test_matches = re.finditer(r"pm\.test\(\s*['\"]([^'\"]+)['\"]\s*,\s*function", combined_script)
        
        # Map out individual script boundaries around pm.test statements for precise matching
        test_blocks = []
        starts = [m.start() for m in pm_test_matches]
        
        # If there are named test blocks, isolate them
        if starts:
            for i in range(len(starts)):
                start_pointer = starts[i]
                end_pointer = starts[i+1] if i + 1 < len(starts) else len(combined_script)
                block_content = combined_script[start_pointer:end_pointer]
                # Extract the test title again
                title_match = re.search(r"pm\.test\(\s*['\"]([^'\"]+)['\"]\s*", block_content)
                title = title_match.group(1) if title_match else "Unnamed Test Assertions Block"
                test_blocks.append((title, block_content))
        else:
            # No pm.test statements found, search matches on entire unified script
            test_blocks = [("Global Assertions", combined_script)]

        # Search patterns inside isolated blocks
        for block_name, code in test_blocks:
            for pattern, assertion_type in self.assertions_patterns:
                matches = re.findall(pattern, code)
                for match in matches:
                    expected_value = None
                    if isinstance(match, tuple):
                        # Multi-group capture
                        expected_value = ", ".join(match)
                    elif match:
                        expected_value = str(match)

                    assertions.append({
                        "testcase_name": block_name,
                        "assertion_type": assertion_type,
                        "raw_assertion": f"Detected matching assertion pattern in code block",
                        "expected_value": expected_value
                    })

        return assertions
