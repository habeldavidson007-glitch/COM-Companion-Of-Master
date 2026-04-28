"""
Python Expert Harness - Run function for signal execution
Generates Python code based on signal payload
"""

def run(payload: str) -> str:
    """
    Execute Python code generation signal
    
    Payload format: language:description
    Examples:
      - python:function to calculate fibonacci
      - python:class for data validation
      - python:script to parse CSV files
    """
    # Parse payload
    parts = payload.split(':', 1)
    language = parts[0].lower() if parts else "python"
    description = parts[1] if len(parts) > 1 else (parts[0] if parts else "generic code")
    
    # Generate code based on description keywords
    if "fibonacci" in description.lower():
        code = _generate_fibonacci()
    elif "csv" in description.lower() or "parse" in description.lower():
        code = _generate_csv_parser()
    elif "class" in description.lower() and ("valid" in description.lower() or "data" in description.lower()):
        code = _generate_validator_class()
    elif "api" in description.lower() or "request" in description.lower():
        code = _generate_api_client()
    elif "file" in description.lower():
        code = _generate_file_handler()
    else:
        code = _generate_generic(description)
    
    return f"🐍 Python code generated:\n\n```python\n{code}\n```\n\n💡 Description: {description}"

def _generate_fibonacci() -> str:
    return """def fibonacci(n: int) -> list[int]:
    \"\"\"Generate Fibonacci sequence up to n terms.\"\"\"
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    
    sequence = [0, 1]
    while len(sequence) < n:
        next_val = sequence[-1] + sequence[-2]
        sequence.append(next_val)
    
    return sequence

# Example usage
if __name__ == "__main__":
    print(fibonacci(10))  # [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
"""

def _generate_csv_parser() -> str:
    return """import csv
from typing import List, Dict

def parse_csv(filename: str) -> List[Dict[str, str]]:
    \"\"\"Parse CSV file and return list of dictionaries.\"\"\"
    data = []
    with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(dict(row))
    return data

def write_csv(filename: str, data: List[Dict], fieldnames: List[str]):
    \"\"\"Write list of dictionaries to CSV file.\"\"\"
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

# Example usage
if __name__ == "__main__":
    # Read CSV
    data = parse_csv('example.csv')
    print(data)
"""

def _generate_validator_class() -> str:
    return """from typing import Any, Optional
import re

class DataValidator:
    \"\"\"Validates common data types and formats.\"\"\"
    
    @staticmethod
    def is_email(value: str) -> bool:
        \"\"\"Validate email format.\"\"\"
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, value))
    
    @staticmethod
    def is_phone(value: str) -> bool:
        \"\"\"Validate phone number (basic format).\"\"\"
        pattern = r'^\\+?[1-9]\\d{1,14}$'
        return bool(re.match(pattern, value.replace('-', '').replace(' ', '')))
    
    @staticmethod
    def is_strong_password(value: str, min_length: int = 8) -> bool:
        \"\"\"Validate password strength.\"\"\"
        if len(value) < min_length:
            return False
        has_upper = any(c.isupper() for c in value)
        has_lower = any(c.islower() for c in value)
        has_digit = any(c.isdigit() for c in value)
        has_special = any(c in '!@#$%^&*(),.?":{}|<>' for c in value)
        return all([has_upper, has_lower, has_digit, has_special])
    
    @staticmethod
    def validate_dict(data: dict, schema: dict) -> tuple[bool, Optional[str]]:
        \"\"\"Validate dictionary against schema.\"\"\"
        for key, expected_type in schema.items():
            if key not in data:
                return False, f"Missing required key: {key}"
            if not isinstance(data[key], expected_type):
                return False, f"Invalid type for {key}: expected {expected_type.__name__}"
        return True, None

# Example usage
if __name__ == "__main__":
    validator = DataValidator()
    print(validator.is_email("test@example.com"))  # True
    print(validator.is_strong_password("SecurePass123!"))  # True
"""

def _generate_api_client() -> str:
    return """import requests
from typing import Dict, Any, Optional

class APIClient:
    \"\"\"Simple HTTP client for REST APIs.\"\"\"
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        \"\"\"Make GET request.\"\"\"
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Make POST request.\"\"\"
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Make PUT request.\"\"\"
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.put(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def delete(self, endpoint: str) -> bool:
        \"\"\"Make DELETE request.\"\"\"
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.delete(url)
        response.raise_for_status()
        return response.status_code == 204

# Example usage
if __name__ == "__main__":
    client = APIClient('https://api.example.com')
    # data = client.get('/users', {'page': 1})
    # print(data)
"""

def _generate_file_handler() -> str:
    return """import os
import json
from pathlib import Path
from typing import Union, List, Dict, Any

class FileHandler:
    \"\"\"Utility class for file operations.\"\"\"
    
    @staticmethod
    def read_text(filepath: Union[str, Path]) -> str:
        \"\"\"Read text file content.\"\"\"
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    def write_text(filepath: Union[str, Path], content: str):
        \"\"\"Write text to file.\"\"\"
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    @staticmethod
    def read_json(filepath: Union[str, Path]) -> Dict[str, Any]:
        \"\"\"Read JSON file.\"\"\"
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def write_json(filepath: Union[str, Path], data: Dict[str, Any], indent: int = 2):
        \"\"\"Write data to JSON file.\"\"\"
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent)
    
    @staticmethod
    def list_files(directory: Union[str, Path], extension: str = None) -> List[Path]:
        \"\"\"List files in directory, optionally filtered by extension.\"\"\"
        path = Path(directory)
        if extension:
            return list(path.glob(f'*{extension}'))
        return [f for f in path.iterdir() if f.is_file()]

# Example usage
if __name__ == "__main__":
    handler = FileHandler()
    # handler.write_text('output.txt', 'Hello, World!')
    # print(handler.read_text('output.txt'))
"""

def _generate_generic(description: str) -> str:
    return f'''"""
Generated Python module
Description: {description}
"""

def main():
    """Main entry point."""
    print("Starting execution...")
    # TODO: Implement your logic here
    pass

if __name__ == "__main__":
    main()
'''

if __name__ == "__main__":
    # Test
    print(run("python:function to calculate fibonacci"))
    print("\n" + "="*60 + "\n")
    print(run("python:class for data validation"))
