class BusinessError(Exception):
    def __init__(self, code: str, message: str, status: int = 422):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


class RateLimited(BusinessError):
    def __init__(self, seconds: int):
        super().__init__("RATE_LIMITED", "Muitas tentativas. Aguarde para tentar novamente.", 429)
        self.seconds = seconds
