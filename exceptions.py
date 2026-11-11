class BankingError(Exception):
    """Base exception for expected banking errors."""


class ValidationError(BankingError):
    pass


class NotFoundError(BankingError):
    pass


class InsufficientFundsError(BankingError):
    pass

