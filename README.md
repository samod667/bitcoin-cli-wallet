# Bitcoin Wallet CLI

██████╗ ██╗████████╗ ██████╗ ██████╗ ██╗███╗   ██╗
██╔══██╗██║╚══██╔══╝██╔════╝██╔═══██╗██║████╗  ██║
██████╔╝██║   ██║   ██║     ██║   ██║██║██╔██╗ ██║
██╔══██╗██║   ██║   ██║     ██║   ██║██║██║╚██╗██║
██████╔╝██║   ██║   ╚██████╗╚██████╔╝██║██║ ╚████║
╚═════╝ ╚═╝   ╚═╝    ╚═════╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝
                                                  
██╗    ██╗ █████╗ ██╗     ██╗     ███████╗████████╗
██║    ██║██╔══██╗██║     ██║     ██╔════╝╚══██╔══╝
██║ █╗ ██║███████║██║     ██║     █████╗     ██║   
██║███╗██║██╔══██║██║     ██║     ██╔══╝     ██║   
╚███╔███╔╝██║  ██║███████╗███████╗███████╗   ██║   
 ╚══╝╚══╝ ╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝   ╚═╝   

[ Secure • Private • Command-Line ]

# Bitcoin Wallet CLI

A command-line Bitcoin wallet implementation for learning and using Bitcoin. This wallet allows you to manage Bitcoin addresses, check balances, send and receive transactions, and view blockchain information without relying on third-party services.

## Features

- **Secure Key Management**: Create new wallets or import existing ones using private keys
- **Balance Management**: Check balance across multiple addresses
- **Send Bitcoin**: Create and broadcast transactions with customizable fees
- **Receive Bitcoin**: Generate payment requests with QR codes
- **Transaction History**: View transaction history for your addresses
- **UTXO Management**: View and control your unspent transaction outputs
- **Privacy Features**: Address rotation, amount randomization, and more
- **Network Information**: View blockchain and mempool data
- **Exchange Rates**: Check current Bitcoin exchange rates
- **Interactive Mode**: User-friendly terminal interface
- **File Storage**: Save and load wallet information

## Supported Networks

- Bitcoin Mainnet
- Bitcoin Testnet
- Bitcoin Signet

## Installation

### System Requirements

- **Operating System**: Linux, macOS, or Windows
- **Python**: Version 3.6 or higher
- **Disk Space**: Approximately 50MB for installation (excluding blockchain data)
- **Memory**: Minimum 2GB RAM recommended

### Prerequisites

Ensure you have the following installed on your system:

- **Python 3.6+**: Check with `python3 --version`
- **pip**: The Python package manager, usually included with Python
- **git**: Optional, for cloning the repository
- **virtualenv**: Recommended for creating isolated Python environments

### Installation Methods

#### Method 1: Using Git (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/bitcoin-wallet-cli.git

# Navigate to the project directory
cd bitcoin-wallet-cli

# Create a virtual environment (recommended)
python3 -m venv venv

# Activate the virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Method 2: Direct Download

1. Download the latest release from the [Releases page](https://github.com/yourusername/bitcoin-wallet-cli/releases)
2. Extract the archive to your preferred location
3. Open a terminal and navigate to the extracted directory
4. Follow the same steps to create a virtual environment and install dependencies as in Method 1

#### Method 3: Using pip (Coming soon)

```bash
# Install directly from PyPI (when available)
pip install bitcoin-wallet-cli
```

### Verification

After installation, verify that everything is working correctly:

```bash
# Run the help command to verify installation
python main.py --help
```

You should see the help message displaying available commands and options.

### Troubleshooting

- If you encounter dependency issues, ensure you're using a supported Python version
- On some systems, you may need to use `python` instead of `python3`
- For permission errors during installation, try using `pip install --user -r requirements.txt`
- See the [FAQ section](#faq) for more common issues

## Dependencies

This wallet relies on the following Python libraries:

- `bitcoin` - Bitcoin protocol implementation
- `bitcoinlib` - Bitcoin library for key management
- `bitcoinutils` - Utilities for Bitcoin operations
- `cryptography` - For secure wallet encryption
- `requests` - For API calls
- `qrcode` - For generating QR codes
- `art` - For ASCII art in the terminal
- `rich` (optional) - For enhanced terminal output
- `termcolor` (optional) - Fallback for colored output if Rich is not available
- `prompt_toolkit` (optional) - For enhanced interactive mode

## Command Overview

Below is a hierarchical view of the available commands:

```
bitcoin-wallet-cli/
├── Wallet Management
│   ├── --output FILE            # Create and save a new wallet to file
│   ├── --privkey KEY            # Import wallet from private key
│   ├── --load FILE              # Load wallet from file for single command
│   ├── --use-wallet KEY         # Use wallet for subsequent commands
│   ├── --use-wallet-file FILE   # Use wallet file for subsequent commands
│   ├── --wallet-info            # Display active wallet information
│   ├── --check-balance          # Check wallet balances
│   ├── --address ADDR           # Check any address balance
│   ├── --show-qr                # Show QR codes for addresses
│   └── --unload-wallet          # Unload the active wallet
│
├── Transaction Operations
│   ├── Receiving
│   │   ├── --receive            # Generate payment request
│   │   ├── --new-address        # Use new address for receiving
│   │   ├── --amount VALUE       # Specify amount in BTC
│   │   └── --message TEXT       # Add message to payment request
│   │
│   ├── Sending
│   │   ├── --send ADDRESS       # Send to specified address
│   │   ├── --amount VALUE       # Amount to send in BTC
│   │   ├── --fee-priority LEVEL # Set fee priority (high/medium/low)
│   │   └── --privacy            # Enable privacy features
│   │
│   └── Analysis
│       ├── --history            # Show transaction history
│       ├── --limit N            # Limit number of transactions in history
│       └── --utxos              # Show unspent transaction outputs
│
├── Network Information
│   ├── --check-fees             # Check recommended transaction fees
│   ├── --blockchain-info        # Display blockchain information
│   ├── --mempool-info           # Display mempool information
│   ├── --rates                  # Show Bitcoin exchange rates
│   └── --network TYPE           # Set network (mainnet/testnet/signet)
│
└── Utility
    ├── --help                   # Show help information
    ├── --help COMMAND           # Show help for specific command
    └── --interactive            # Start interactive mode
```

### Basic Command Syntax

```
python main.py [OPTIONS]
```

In interactive mode:
```
wallet> COMMAND [OPTIONS]
```

## Example Workflows

### First-time Setup

1. Create a new wallet and save to file:
   ```
   python main.py --output my_wallet.json
   ```

2. Check balance:
   ```
   python main.py --load my_wallet.json --check-balance
   ```

3. Receive Bitcoin:
   ```
   python main.py --load my_wallet.json --receive --amount 0.001 --message "First payment"
   ```

### Sending Bitcoin

1. Load wallet:
   ```
   python main.py --load my_wallet.json
   ```

2. Check balance:
   ```
   python main.py --check-balance
   ```

3. Check current fees:
   ```
   python main.py --check-fees
   ```

4. Send Bitcoin:
   ```
   python main.py --send tb1qds6redgk9lk9zcspmc43a9a77p9gtrz8gney6l --amount 0.0001 --fee-priority medium
   ```

5. Check transaction history:
   ```
   python main.py --history
   ```

### Using Interactive Mode

1. Start interactive mode:
   ```
   python main.py --interactive
   ```

2. Create a new wallet:
   ```
   wallet> create --output my_wallet.json
   ```

3. Check balance:
   ```
   wallet> balance
   ```

4. Generate payment request:
   ```
   wallet> receive --amount 0.001 --message "Payment"
   ```

5. Send Bitcoin:
   ```
   wallet> send --to tb1qds6redgk9lk9zcspmc43a9a77p9gtrz8gney6l --amount 0.0001 --fee medium
   ```

6. Exit:
   ```
   wallet> exit
   ```

## Security Considerations

- **Backup Your Wallet**: Always keep backups of your wallet files and/or private keys in secure locations.
- **Network Selection**: Use testnet or signet for learning and testing before using real funds on mainnet.
- **Private Keys**: Never share your private keys or seed phrases with anyone.
- **Terminal History**: Your command history might contain private keys if you input them directly. Clear your terminal history after using this wallet.

## Development

This wallet was created for educational purposes to demonstrate Bitcoin wallet functionality. Feel free to fork, modify, and improve it.

### Adding New Features

The modular architecture makes it easy to add new features:
1. Add new command-line arguments in `cli.py`
2. Create corresponding command classes in `commands.py`
3. Implement the functionality in the appropriate module

## License

This project is available under the MIT License. See the LICENSE file for details.

## Disclaimer

This wallet is provided for educational purposes. Use at your own risk. The authors are not responsible for any loss of funds.

---

*Made with ❤️ for the Bitcoin community.*