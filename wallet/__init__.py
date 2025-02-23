# wallet/__init__.py

# Import main functionality to make it easily accessible
from .keys import generate_wallet
from .transactions import (
    create_payment_request,
    create_and_sign_transaction,
    broadcast_transaction
)
from .network import fetch_address_balance, fetch_utxos, get_recommended_fee_rate
from .display import WalletDisplay
from .qrcode import generate_ascii_qr

# Define what should be available when someone imports our package
__all__ = [
    'generate_wallet',
    'create_payment_request',
    'create_and_sign_transaction',
    'broadcast_transaction',
    'fetch_address_balance',
    'fetch_utxos',
    'WalletDisplay',
    'generate_ascii_qr',
    'get_recommended_fee_rate'
]

# Package metadata
__version__ = '0.1.0'
__author__ = 'Your Name'
__description__ = 'A Bitcoin wallet CLI implementation for learning purposes'