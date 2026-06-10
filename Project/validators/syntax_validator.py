import json
import logging
import ast
import re
from typing import Dict, Any, List, Set, Tuple

# Setup logger
logger = logging.getLogger("SyntaxValidator")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


class CollectionSyntaxValidator:
    """
    Syntax validator for validating Postman Collections, identifying compatibility concerns,
    detecting duplicate requests, locating missing variables, evaluating overall readiness,
    and outputting warnings, errors, and validation scores.
    """

    def __init__(self) -> None:
        pass

    def validate_collection_json(self, raw_json_str: str) -> Tuple[bool, List[str]]:
        """
        Validates if the provided payload is a valid JSON.
        """
        try:
            json.loads(raw_json_str)
            return True, []
        except json.JSONDecodeError as de:
            logger.error(f"Invalid JSON format detected: {str(de)}")
            return False, [f"Invalid JSON Format: {str(de)} at Line {de.lineno}, Column {de.colno}"]

    def validate_collection_structure(self, parsed_dict: Dict[str, Any]) -> Tuple[List[str], List[str], int]:
        """
        Validates Postman structures, empty conditions, variables, duplicates, and unsupported components.

        Args:
            parsed_dict: Dictionary returned from parsing raw Postman collection.

        Returns:
            Tuple of (errors, warnings, validation_score)
        """
        errors: List[str] = []
        warnings: List[str] = []
        score = 100

        # 1. Invalid Structure and Empty Collection Detection
        if not isinstance(parsed_dict, dict):
            errors.append("Invalid collection structure. Content is not an object.")
            return errors, warnings, 0

        info_block = parsed_dict.get("info", {})
        item_block = parsed_dict.get("item", [])

        if not info_block:
            errors.append("Invalid Structure: Missing core 'info' block descriptor.")
            score -= 30

        if not item_block or len(item_block) == 0:
            errors.append("Empty Collection: No request items, routes, or folders exist in the collection.")
            score -= 40
            return errors, warnings, max(0, score)

        # Retrieve parsed metadata for deeper assessment
        from parser.collection_parser import CollectionParser
        try:
            parser = CollectionParser()
            analysis = parser.parse_collection(parsed_dict)
        except Exception as ex:
            errors.append(f"Structure analysis failed during simulation parser run: {str(ex)}")
            return errors, warnings, 10

        apis = analysis.get("apis", [])
        if not apis:
            errors.append("Empty Collection: Collection parser did not extract any API request items.")
            score -= 40
            return errors, warnings, max(0, score)

        # 2. Duplicate Function / Request Detection
        api_names: Set[str] = set()
        api_endpoints: Set[Tuple[str, str]] = set()  # (method, endpoint)
        
        duplicate_names = 0
        duplicate_endpoints = 0

        for api in apis:
            api_name = api.get("api_name", "Unnamed Request")
            method = api.get("method", "GET")
            endpoint = api.get("endpoint", "")

            # Normalize endpoint variables to compare structurally similar routes
            normalized_endpoint = re.sub(r"\{\{[^}]+\}\}", "{{VAR}}", endpoint)

            if api_name in api_names:
                warnings.append(f"Duplicate Request Name: '{api_name}' is used multiple times. This will generate conflicting test function names.")
                duplicate_names += 1
            else:
                api_names.add(api_name)

            route_pattern = (method, normalized_endpoint)
            if route_pattern in api_endpoints:
                warnings.append(f"Duplicate Endpoint Route: Duplicate route request found for '{method} {endpoint}'.")
                duplicate_endpoints += 1
            else:
                api_endpoints.add(route_pattern)

        score -= (duplicate_names * 5)
        score -= (duplicate_endpoints * 8)

        # 3. Missing Variable Detection
        # Collect defined variable keys
        declared_var_keys = {var.get("key") for var in analysis.get("variables", []) if var.get("key")}
        
        # Parse references to double curly bracket format {{variable_name}}
        referenced_vars: Set[str] = set()
        for api in apis:
            # Check route urls
            for match in re.findall(r"\{\{([^}]+)\}\}", api.get("endpoint", "")):
                referenced_vars.add(match)
            # Check raw headers strings
            headers_str = api.get("headers", "[]")
            for match in re.findall(r"\{\{([^}]+)\}\}", headers_str):
                referenced_vars.add(match)
            # Check request bodies
            body = api.get("request_body", "")
            for match in re.findall(r"\{\{([^}]+)\}\}", body):
                referenced_vars.add(match)

        missing_vars = referenced_vars - declared_var_keys
        for missing in missing_vars:
            # Low severity warning as variables could refer to pre-injection environments
            warnings.append(f"Missing Variable Definition: Variable '{{{{{missing}}}}}' is referenced but not declared in collection globals.")
            score -= 5

        # 4. Unsupported Postman Assertion / Component Detection
        unsupported_calls = [
            ("xml2Json", "Postman XML parsing libraries are not natively supported in standard Python/Pytest suites."),
            ("tv4.validate", "TinyValidator V4 JSON schemas must be converted to python static schema validators."),
            ("postman.setNextRequest", "Dynamic postman workflows change execution state. Pytest plays sequentially."),
            ("pm.globals.set", "Setting collection globals at runtime translates into customized test state stores."),
            ("pm.environment.set", "Modifying environment setups on the fly is unsupported. Inject setups via CLI fixtures.")
        ]

        unsupported_count = 0
        for api in apis:
            raw_script_block = "\n".join(api.get("raw_test_scripts", []))
            for phrase, desc in unsupported_calls:
                if phrase in raw_script_block:
                    warnings.append(f"Unsupported Component in '{api.get('api_name')}': '{phrase}' was detected. {desc}")
                    unsupported_count += 1

        score -= (unsupported_count * 10)

        # Bound score logically to (10 to 100) or 0 if heavy structural errors exist
        if errors:
            score = min(score, 40)
        
        final_score = max(10, min(100, score)) if not errors else max(0, min(40, score))
        return errors, warnings, final_score


    def validate_generated_pytest_syntax(self, code_content: str) -> Tuple[bool, List[str]]:
        """
        Verifies syntax validity of generated Pytest python files before compiling.
        
        Args:
            code_content: Pure python source code.

        Returns:
            Tuple of validation outcome (bool) and compiler error messages.
        """
        try:
            ast.parse(code_content)
            return True, []
        except SyntaxError as se:
            logger.error(f"Python AST compile syntax error: {str(se)}")
            return False, [f"Pytest Code Compile Failed: Line {se.lineno}, Error: {se.msg}"]
        except Exception as e:
            return False, [f"Validation failed with unexpected exception: {str(e)}"]
