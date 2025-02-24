# Bitcoin CLI Wallet

A simple, command-line Bitcoin wallet for learning and experimentation, built as a beginner's dive into Bitcoin open-source development. Supports generating wallets, checking balances, creating payment requests, sending transactions, and more—focused on the testnet network for safe exploration.

This is my first project after completing the Chaincode Labs BOSS program, so it’s a work in progress! I’ve leaned on AI tools to help me learn faster, but I’m proud of putting it all together into something functional.

## Features
- Generate new wallets with mnemonic phrases or import existing private keys
- Support for both SegWit (`tb1q...`) and Legacy (`m...`) addresses
- Check address balances and transaction history (via Blockstream API)
- Create payment requests with QR codes (ASCII in terminal)
- Send Bitcoin transactions with configurable fee priorities
- View blockchain and mempool info
- Basic privacy options (new address generation, amount randomization—WIP)
- Save/load wallet data to/from JSON files
- Pretty terminal output with optional color and ASCII art

## Prerequisites
- Python 3.8+
- Dependencies listed in `requirements.txt` (see [Installation](#installation))

## Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/bitcoin-cli-wallet.git
   cd bitcoin-cli-wallet```

2. Set up a virtual environment (optional but recommended):
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
3. Install dependencies:
```
pip install -r requirements.txt
```

## Usage
Run the wallet with python main.py and use the command-line options below. By default, it operates on Bitcoin’s testnet—perfect for testing without real funds.
# Example 
1. Generate Wallet:
```
python main.py --network testnet
```
Outputs a mnemonic phrase, private/public keys, and addresses.

2. Check balances:
```
python main.py --network testnet --check-balance
```
3. Create a payment request:
```
python main.py --network testnet --receive --amount 0.001 --message "Coffee fund" --show-qr
```
4. Send Bitcoin (requires a private key with testnet funds):
```
python main.py --network testnet --send tb1q... --amount 0.0005 --privkey 93...
```
5. Check fee rates:
```
python main.py --network testnet --check-fees
```
6. View blockchain info:
```
python main.py --network testnet --blockchain-info
```
### Command-Line Options

| Option             | Description                                      | Example                  |
|--------------------|--------------------------------------------------|--------------------------|
| `--network`        | Bitcoin network (mainnet, testnet, signet)       | `--network testnet`      |
| `--address-type`   | Address type (legacy, segwit, both)              | `--address-type segwit`  |
| `--check-balance`  | Show balances for all addresses                  | `--check-balance`        |
| `--receive`        | Generate a payment request                       | `--receive`              |
| `--amount`         | Amount in BTC for send/receive                   | `--amount 0.001`         |
| `--send`           | Send BTC to an address                           | `--send tb1q...`         |
| `--privkey`        | Use a specific private key (WIF format)          | `--privkey 93...`        |
| `--fee-priority`   | Transaction fee priority (high, medium, low)     | `--fee-priority high`    |
| `--privacy`        | Enable privacy features (WIP)                    | `--privacy`              |
| `--show-qr`        | Display ASCII QR codes                           | `--show-qr`              |
| `--output`         | Save wallet to a JSON file                       | `--output wallet.json`   |
| `--load`           | Load wallet from a JSON file                     | `--load wallet.json`     |
| `--check-fees`     | Show current fee rates                           | `--check-fees`           |
| `--blockchain-info`| Display blockchain info                          | `--blockchain-info`      |
| `--mempool-info`   | Display mempool info                             | `--mempool-info`         |

> **Note**: Use testnet funds (get some from a faucet like [testnet-faucet.com](https://testnet-faucet.com)) to experiment safely.

## Running Tests
Tests verify core functionality like address generation and API calls. Run them with:

```bash
pytest tests/
```
## Project Structure
main.py: CLI entry point and argument parsing
wallet.py: Wallet generation logic
display.py: Terminal output formatting
network.py: API interactions (Blockstream, etc.)
privacy.py: Privacy-related utilities
tests/: Test suite

## Contributing
This is a learning project, but contributions are alwayse welcome and feedback is welcome! Feel free to open an issue or reach out if you spot bugs or have ideas.

## Disclaimer
This is an educational tool—not for production use with real funds. Always secure your private keys and mnemonic phrases, and double-check everything when dealing with Bitcoin

### Steps to Use It
1. Open your editor, create or open `README.md` in your project root.
2. Copy the entire block above (from `# Bitcoin CLI Wallet` to the end).
3. Paste it into `README.md`.
4. Replace `yourusername` in the `git clone` command with your actual GitHub username.
5. Save, then push to GitHub:
   ```bash
   git add README.md
   git commit -m "Add README"
   git push origin main