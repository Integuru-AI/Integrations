from utils.errors import IntegrationAPIError
from typing import Dict, Any

def safe_get(self, data: Dict[str, Any], key: str, method_name: str):
    try:
        return data[key]
    except KeyError:
        raise IntegrationAPIError(
            self.integration_name,
            f"Missing key '{key}' in response JSON for {method_name}."
        )
