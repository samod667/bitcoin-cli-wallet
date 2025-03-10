____  _ _            _        __        __    _ _      _      ___  _    ___ 
 | __ )(_) |_ ___ ___ (_)_ __   \ \      / /_ _| | | ___| |_   / __\/ |  /_ _\
 |  _ \| | __/ __/ _ \| | '_ \   \ \ /\ / / _` | | |/ _ \ __| / /   | |  //_\\
 | |_) | | || (_| (_) | | | | |   \ V  V / (_| | | |  __/ |_ / /___ | | /  _  \
 |____/|_|\__\___\___/|_|_| |_|    \_/\_/ \__,_|_|_|\___|\__|\____/ |_| \_/ \_/
                                                                               
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

### Prerequisites

- Python 3.6+
- Pip (Python package manager)

### Installation Steps

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/bitcoin-wallet-cli.git
   cd bitcoin-wallet-cli
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

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

## Usage

### Basic Usage

```
python main.py [options]
```

### Creating a Wallet

Create a new wallet and save to file:
```
python main.py --output my_wallet.json
```

Import from private key:
```
python main.py --privkey <private_key_in_wif_format> --output my_wallet.json
```

### Loading and Using a Wallet

Load wallet from file for a single command:
```
python main.py --load my_wallet.json --check-balance
```

Use wallet for multiple subsequent commands:
```
python main.py --use-wallet-file my_wallet.json
python main.py --check-balance
python main.py --receive --amount 0.001
```

### Wallet Operations

Check balance:
```
python main.py --check-balance
```

Show wallet information:
```
python main.py --wallet-info
```

Check balance of any address (without loading a wallet):
```
python main.py --address tb1qds6redgk9lk9zcspmc43a9a77p9gtrz8gney6l
```

Show QR codes for addresses:
```
python main.py --show-qr
```

### Transaction Operations

Receive payment:
```
python main.py --receive --amount 0.001 --message "Payment for coffee"
```

Use a new address for receiving:
```
python main.py --receive --new-address --amount 0.001
```

Send Bitcoin:
```
python main.py --send tb1qds6redgk9lk9zcspmc43a9a77p9gtrz8gney6l --amount 0.001
```

With custom fee priority:
```
python main.py --send tb1qds6redgk9lk9zcspmc43a9a77p9gtrz8gney6l --amount 0.001 --fee-priority high
```

Enable privacy features:
```
python main.py --send tb1qds6redgk9lk9zcspmc43a9a77p9gtrz8gney6l --amount 0.001 --privacy
```

### Network Information

Check current recommended fees:
```
python main.py --check-fees
```

Show blockchain information:
```
python main.py --blockchain-info
```

Show mempool information:
```
python main.py --mempool-info
```

Show Bitcoin exchange rates:
```
python main.py --rates
```

### Transaction History and UTXOs

Show transaction history:
```
python main.py --history
```

Limit the number of transactions shown:
```
python main.py --history --limit 5
```

Show unspent transaction outputs (UTXOs):
```
python main.py --utxos
```

### Interactive Mode

Start the interactive terminal interface:
```
python main.py --interactive
```

In interactive mode, you can use simplified commands:
- `create` - Create a new wallet
- `load FILENAME` - Load wallet from file
- `use PRIVKEY` - Use wallet with private key
- `wallet` - Show wallet information
- `balance` - Check wallet balance
- `receive` - Generate payment request
- `send` - Send Bitcoin
- `history` - Show transaction history
- `fees` - Check current fees
- `blockchain` - Show blockchain info
- `mempool` - Show mempool info
- `rates` - Show exchange rates
- `help` - Show help information
- `exit` - Exit the wallet

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