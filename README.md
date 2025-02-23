# Bitcoin Wallet CLI

A Python-based Bitcoin wallet command-line interface that demonstrates the fundamental concepts of Bitcoin wallet operations, key generation, and transaction handling. This educational project helps understand how Bitcoin wallets work while providing practical functionality for testnet experimentation.

## Features

- Generate new Bitcoin wallets with hierarchical deterministic (HD) key derivation
- Display multiple derived addresses with their corresponding private and public keys
- Generate QR codes for Bitcoin addresses
- Check address balances using the Blockstream API
- Send and receive Bitcoin transactions
- Dynamic fee calculation based on network conditions
- Support for multiple networks (mainnet, testnet, signet)
- Save wallet information to JSON files
- Display transaction history and balances

## Prerequisites

Before running this wallet, ensure you have Python 3.7 or higher installed. You'll also need to install the required dependencies:

```bash
pip install -r requirements.txt
The following Python packages are required:

bitcoin-python
bitcoinlib
mnemonic
qrcode
requests
art

Installation

Clone this repository:

bashCopygit clone https://github.com/yourusername/bitcoin-wallet-cli.git
cd bitcoin-wallet-cli

Create and activate a virtual environment:

bashCopypython -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate

Install dependencies:

bashCopypip install -r requirements.txt
Usage
Generate a New Wallet
bashCopypython main.py --network testnet
Check Address Balance
bashCopypython main.py --network testnet --check-balance YOUR_PRIVATE_KEY
Display QR Codes
bashCopypython main.py --network testnet --show-qr
Create a Payment Request
bashCopypython main.py --network testnet --receive --amount 0.001 --message "Payment for coffee"
Send Bitcoin
bashCopypython main.py --network testnet --send RECIPIENT_ADDRESS --amount 0.001 --fee-priority medium YOUR_PRIVATE_KEY
Check Current Fee Rates
bashCopypython main.py --network testnet --check-fees
Save Wallet Information to File
bashCopypython main.py --network testnet --output wallet.json
Project Structure
Copybitcoin-wallet-cli/
├── wallet/
│   ├── __init__.py
│   ├── keys.py           # Key and address generation
│   ├── transactions.py   # Transaction creation and broadcasting
│   ├── network.py        # Network interactions and fee calculation
│   ├── display.py        # Terminal output formatting
│   └── qrcode.py        # QR code generation
├── main.py               # Command-line interface
└── requirements.txt      # Project dependencies
Fee Priority Levels
The wallet supports three fee priority levels:

high: Targeting next block (approximately 10 minutes)
medium: Targeting within 3 blocks (approximately 30 minutes)
low: Targeting within 6 blocks (approximately 1 hour)

Security Considerations
This wallet is designed for educational purposes and testing on Bitcoin's testnet. When using on mainnet:

Always backup your seed phrase and private keys
Never share your private keys
Verify recipient addresses carefully
Test with small amounts first
Be cautious with network fee settings

# Testing
To get testnet coins for testing:

Generate a testnet address using the wallet
Visit a testnet faucet (e.g., https://bitcoinfaucet.uo1.net/)
Request test coins for your address
Wait for the transaction to be confirmed

# Contributing
Contributions are welcome! Please feel free to submit pull requests.
# License
This project is licensed under the MIT License - see the LICENSE file for details.
Acknowledgments

Bitcoin developers for their documentation
Blockstream for their API service
The Python Bitcoin community for their libraries

# Disclaimer
This wallet is for educational purposes only. Use at your own risk. Always verify transactions and addresses carefully. The authors are not responsible for any lost funds or incorrect transactions.
