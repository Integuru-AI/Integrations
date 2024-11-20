from typing import Dict, Any, List
from submodule_integrations.utils.errors import IntegrationAPIError
from functools import reduce


class Integration:
    def __init__(self, integration_name: str):
        self.integration_name = integration_name

    def safe_get(self, data: Dict[str, Any], keys: List[str], method_name: str):
        try:
            return reduce(lambda d, key: d[key], keys, data)
        except (KeyError, TypeError):
            raise IntegrationAPIError(
                self.integration_name,
                f"Missing key path '{' -> '.join(keys)}' in response JSON for {method_name}.",
            )
