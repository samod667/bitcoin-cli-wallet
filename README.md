# Bitcoin Address Generation CLI

A simple Python command-line tool to generate testnet Bitcoin addresses. It can:
- Generate a random base private key with a 24-word BIP-39 mnemonic when no input is provided.
- Accept a user-provided testnet private key in Wallet Import Format (WIF).
- Derive 10 additional testnet addresses from the base private key.
- Display results in a formatted table, including private keys, public keys, addresses, and mnemonic words (if applicable).


## Features
- Generates a 24-word BIP-39 mnemonic for random keys (256-bit entropy).
- Outputs private keys (WIF), public keys (hex), and testnet addresses in a clean CLI table.
- Derives 10 child keys by incrementing the base private key (simplified, not full BIP-32).
- Includes error handling for invalid WIF formats, mainnet keys, and derivation issues.

## Prerequisites
- Python 3.8 or later
- A virtual environment (recommended)

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/samod667/bitcoin-address-generation-cli.git
   cd bitcoin-address-generation-cli
Set up a virtual environment:
bash
Wrap
Copy
python3 -m venv venv
source venv/bin/activate  # Linux/MacOS
venv\Scripts\activate     # Windows
Install dependencies:
bash
Wrap
Copy
pip install -r requirements.txt
Usage
Run the script with or without a private key argument:

Generate a random key with mnemonic:
bash
Wrap
Copy
python generate_address.py
Use a specific testnet private key:
bash
Wrap
Copy
python generate_address.py cN9s...
Example Output

Random Key with Mnemonic

text
Wrap
Copy
Base Private Key (WIF): cN9s...
Base Public Key (hex): 02...
Mnemonic Words: apple banana cherry dog elephant fox grape horse igloo jelly kiwi lemon mango orange peach quince rabbit snake tiger umbrella violin whale xray zebra

Derived Addresses:
--------------------------------------------------------------------------------
Index  Private Key (WIF)                  Public Key (hex)                   Address
--------------------------------------------------------------------------------
0      cN9s...                            02...                              m...
1      cN9t...                            03...                              n...
2      cN9u...                            02...                              m...
3      cN9v...                            03...                              n...
4      cN9w...                            02...                              m...
5      cN9x...                            03...                              n...
6      cN9y...                            02...                              m...
7      cN9z...                            03...                              n...
8      cNa1...                            02...                              m...
9      cNa2...                            03...                              n...
--------------------------------------------------------------------------------
Specific Testnet Key

text
Wrap
Copy
Base Private Key (WIF): cN9s...
Base Public Key (hex): 02...
Mnemonic Words: N/A (provided private key)

Derived Addresses:
--------------------------------------------------------------------------------
Index  Private Key (WIF)                  Public Key (hex)                   Address
--------------------------------------------------------------------------------
0      cN9s...                            02...                              m...
1      cN9t...                            03...                              n...
...
9      cNa2...                            03...                              n...
--------------------------------------------------------------------------------
Error Example

text
Wrap
Copy
Error: Invalid private key format or unexpected issue (Invalid base58 string)
Notes
Derivation: The tool uses a simplified method (incrementing the base private key integer) for educational purposes. It’s not cryptographically secure or BIP-32 compliant. For real-world use, implement proper HD wallet derivation (e.g., m/44'/1'/0'/0/[0-9]).
Testnet Only: Supports testnet private keys (starting with c). Mainnet keys (e.g., starting with 5, K, or L) will trigger an error.
Security: This is a learning project—do not use generated keys for real Bitcoin funds.
Contributing
Feel free to fork, modify, or suggest improvements via pull requests! This is a beginner-friendly project, so all feedback is appreciated.

License
MIT License – free to use, modify, and distribute.

Tags
#BitcoinDev #Python #CLI #Cryptocurrency #LearningProject

Acknowledgments
Built with python-bitcoinlib and mnemonic.
