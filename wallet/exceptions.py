"""
Custom exceptions for the Bitcoin wallet application.
These exceptions provide more specific error handling and better error messages.
"""

class WalletError(Exception):
    """Base exception class for all wallet-related errors."""
    def __init__(self, message: str = "An error occurred in the wallet"):
        self.message = message
        super().__init__(self.message)

class NetworkError(WalletError):
    """Raised when network operations fail."""
    def __init__(self, message: str = "Network operation failed", details: str = None):
        self.details = details
        super_message = f"{message}: {details}" if details else message
        super().__init__(super_message)

class InsufficientFundsError(WalletError):
    """Raised when trying to send more than available balance."""
    def __init__(self, required: float, available: float):
        self.required = required
        self.available = available
        message = f"Insufficient funds: needed {required} BTC but only {available} BTC available"
        super().__init__(message)

class InvalidAddressError(WalletError):
    """Raised when an invalid Bitcoin address is used."""
    def __init__(self, address: str, reason: str = None):
        self.address = address
        message = f"Invalid Bitcoin address: {address}"
        if reason:
            message += f" ({reason})"
        super().__init__(message)

class InvalidPrivateKeyError(WalletError):
    """Raised when an invalid private key is provided."""
    def __init__(self, reason: str = None):
        message = "Invalid private key"
        if reason:
            message += f": {reason}"
        super().__init__(message)

class FeeEstimationError(WalletError):
    """Raised when fee estimation fails."""
    def __init__(self, fee_type: str = None):
        message = "Failed to estimate transaction fee"
        if fee_type:
            message += f" for {fee_type} priority"
        super().__init__(message)

class TransactionError(WalletError):
    """Raised when transaction creation or broadcasting fails."""
    def __init__(self, operation: str, reason: str = None):
        self.operation = operation
        message = f"Transaction {operation} failed"
        if reason:
            message += f": {reason}"
        super().__init__(message)

class ConfigurationError(WalletError):
    """Raised when there's an error in configuration."""
    def __init__(self, parameter: str = None, reason: str = None):
        message = "Configuration error"
        if parameter:
            message += f" for {parameter}"
        if reason:
            message += f": {reason}"
        super().__init__(message)

class WalletStorageError(WalletError):
    """Raised when wallet storage operations fail."""
    def __init__(self, operation: str, reason: str = None):
        self.operation = operation
        message = f"Wallet storage {operation} failed"
        if reason:
            message += f": {reason}"
        super().__init__(message)

class PrivacyError(WalletError):
    """Raised when privacy-related operations fail."""
    def __init__(self, feature: str = None, reason: str = None):
        message = "Privacy feature failed"
        if feature:
            message += f" ({feature})"
        if reason:
            message += f": {reason}"
        super().__init__(message)

class InvalidAmountError(WalletError):
    """Raised when an invalid amount is specified."""
    def __init__(self, amount: str, reason: str = None):
        self.amount = amount
        message = f"Invalid amount: {amount}"
        if reason:
            message += f" ({reason})"
        super().__init__(message)

class APIError(NetworkError):
    """Raised when an API request fails."""
    def __init__(self, endpoint: str, status_code: int = None, response: str = None):
        self.endpoint = endpoint
        self.status_code = status_code
        self.response = response
        
        message = f"API request failed for {endpoint}"
        if status_code:
            message += f" (Status: {status_code})"
        if response:
            message += f": {response}"
        
        super().__init__(message)