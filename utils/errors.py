from typing import Optional


class IntegrationAuthError(Exception):
    """Raised when authentication/authorization fails"""

    def __init__(self, message: str = "Authentication failed", status_code: Optional[int] = None):
        self.status_code = status_code
        self.message = message
        super().__init__(self.message)


class IntegrationAPIError(Exception):
    """Raised when any API error occurs"""

    def __init__(self, integration_name: str, message: str = "API error", status_code: Optional[int] = None):
        self.integration_name = integration_name.lower()
        self.status_code = status_code
        self.message = f"{self.integration_name.capitalize()} API error: {message}"
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message} (Status code: {self.status_code})" if self.status_code else self.message
