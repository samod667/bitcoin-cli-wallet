Bitcoin Address Generation CLI

A simple Python command-line tool for generating testnet Bitcoin addresses.

This tool enables you to:

Generate a Random Key: Create a random base private key with a 24-word BIP-39 mnemonic when no input is provided.
Input a Specific Key: Accept a user-supplied testnet private key in Wallet Import Format (WIF).
Derive Additional Addresses: Generate 10 child addresses from the base private key.
Display Results Clearly: Present private keys, public keys, addresses, and mnemonic words (when applicable) in a formatted table.
Features

Mnemonic Generation: Produces a 24-word BIP-39 mnemonic (using 256-bit entropy) for random key creation.
Formatted Output: Outputs private keys (WIF), public keys (hex), and testnet addresses in a clean CLI table.
Simplified Derivation: Derives 10 child keys by incrementing the base private key (note: this is a simplified approach, not full BIP-32 compliant).
Robust Error Handling: Checks for invalid WIF formats, rejects mainnet keys, and manages derivation issues gracefully.
Prerequisites

Python 3.8 or later
(Optional) A virtual environment for dependency isolation
Installation

Follow these steps to set up the project locally:

Clone the Repository:
git clone https://github.com/samod667/bitcoin-address-generation-cli.git
cd bitcoin-address-generation-cli
Set Up a Virtual Environment:
# Linux/MacOS:
python3 -m venv venv
source venv/bin/activate

# Windows:
python -m venv venv
venv\Scripts\activate
Install Dependencies:
pip install -r requirements.txt
Usage

You can run the script with or without a private key argument.

Generate a Random Key with Mnemonic
python generate_address.py
Use a Specific Testnet Private Key
python generate_address.py <your_testnet_private_key>
Example Output

Random Key with Mnemonic
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
Base Private Key (WIF): cN9s...
Base Public Key (hex): 02...
Mnemonic Words: N/A (provided private key)

Derived Addresses:
--------------------------------------------------------------------------------
Index  Private Key (WIF)                  Public Key (hex)                   Address
--------------------------------------------------------------------------------
0      cN9s...                            02...                              m...
1      cN9t...                            03...                              n...
...    ...                                ...                                ...
9      cNa2...                            03...                              n...
--------------------------------------------------------------------------------
Error Example
Error: Invalid private key format or unexpected issue (Invalid base58 string)
Notes

Derivation Method: The tool uses a simplified derivation method (incrementing the base private key) for educational purposes. This approach is not cryptographically secure or BIP-32 compliant. For production applications, implement proper HD wallet derivation (e.g., m/44'/1'/0'/0/[0-9]).
Testnet Only: Only testnet private keys (typically starting with c) are supported. Using mainnet keys (e.g., keys starting with 5, K, or L) will trigger an error.
Security Notice: This is a learning project—do not use generated keys for actual Bitcoin funds.
Contributing

Contributions are welcome! Feel free to fork the repository, suggest modifications, or submit pull requests. All feedback is appreciated, especially from beginners looking to learn and improve.

License

This project is licensed under the MIT License. You are free to use, modify, and distribute it as per the license terms.

Tags

#BitcoinDev #Python #CLI #Cryptocurrency #LearningProject

Acknowledgments

Built with python-bitcoinlib and mnemonic.
