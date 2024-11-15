from typing import Optional


class IntegrationError(Exception):
    def __init__(self, message: str, status_code: int = None, error_code: str = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


class IntegrationAuthError(IntegrationError):
    pass


class IntegrationAPIError(IntegrationError):
    def __init__(self, integration_name: str, message: str, error_code: str = None):
        super().__init__(f"{integration_name}: {message}", error_code=error_code)


class IntegrationWebhookError(IntegrationError):
    pass
