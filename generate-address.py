import os
import argparse
import bitcoin
from mnemonic import Mnemonic
from bitcoin import SelectParams
from bitcoin.wallet import CBitcoinSecret, P2PKHBitcoinAddress
from bitcoin.core import x
import requests
from typing import Dict, Union, List, Tuple
import json
import datetime
from bitcoinlib.keys import HDKey
import qrcode
from art import text2art

# test address with bitcoins = cPCAMF3uPQJQfMvsqfzXTcH7Gm9buiYQZb3gaxjD5PZkCyFF3ADL

def parse_args():
    parser = argparse.ArgumentParser(description="Generate Bitcoin wallet keys and addresses.")
    parser.add_argument(
        "--network",
        choices=["mainnet", "testnet", "signet"],
        default="testnet",
        help="Bitcoin network to use (default: testnet)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Save wallet information to specified JSON file"
    )
    parser.add_argument(
        "--check-balance",
        action="store_true",
        help="Check balances for all generated addresses"
    )
    parser.add_argument(
        "--show-qr",
        action="store_true",
        help="Show QR codes for addresses in terminal"
    )
    parser.add_argument(
        "privkey",
        nargs="?",
        default=None,
        help="Optional private key in WIF format"
    )

    tx_group = parser.add_argument_group('transaction operations')
    tx_group.add_argument(
        "--receive",
        action="store_true",
        help="Generate a payment request with amount and message"
    )
    tx_group.add_argument(
        "--amount",
        type=float,
        help="Amount in BTC for receive/send operation"
    )
    tx_group.add_argument(
        "--message",
        type=str,
        help="Optional message for the payment request"
    )
    tx_group.add_argument(
        "--send",
        type=str,
        help="Send BTC to the specified address"
    )
    
    return parser.parse_args()

def get_bitcoinlib_network(network):
    """
    Convert python-bitcoinlib network names to bitcoinlib network names.
    
    python-bitcoinlib uses: mainnet, testnet, signet
    bitcoinlib uses: bitcoin, testnet, signet
    """
    network_mapping = {
        "mainnet": "bitcoin",
        "testnet": "testnet",
        "signet": "signet"
    }
    return network_mapping.get(network, "testnet")

def save_to_json(file_path, base_privkey, base_pubkey, mnemonic_words, derived_addresses, network):
    """
    Save wallet information to a JSON file.
    
    Args:
        file_path (str): Path where the JSON file will be saved
        base_privkey (str): Base private key in WIF format
        base_pubkey (str): Base public key in hex format
        mnemonic_words (str): Mnemonic seed phrase
        derived_addresses (list): List of derived address tuples
        network (str): Network type (mainnet, testnet, or signet)
    """
    try:
        # Create a dictionary to store wallet information
        wallet_data = {
            "network": network,
            "created_at": datetime.datetime.now().isoformat(),
            "base_wallet": {
                "private_key": base_privkey,
                "public_key": base_pubkey,
                "mnemonic": mnemonic_words
            },
            "derived_addresses": [
                {
                    "index": addr[0],
                    "private_key": addr[1],
                    "public_key": addr[2],
                    "address": addr[3]
                }
                for addr in derived_addresses
            ]
        }

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

        # Write the data to the file with pretty formatting
        with open(file_path, 'w') as f:
            json.dump(wallet_data, f, indent=2)
            
        print(f"\nWallet information saved to: {file_path}")
        
    except Exception as e:
        print(f"\nError saving wallet information: {str(e)}")

def print_table_with_balances_and_qr(base_privkey: str, base_pubkey: str, 
                                    mnemonic_words: str, derived_addresses: List[Tuple], 
                                    network: str, show_balance: bool, show_qr: bool):
    """
    Print wallet information with a clean, organized layout including QR codes and balances.
    Each address is shown once with its QR code and relevant information.
    """
    # Print wallet header with ASCII art styling
    print("\n" + text2art("Bitcoin Wallet", font="small"))
    
    # Print basic wallet information
    print("\nBase Private Key (WIF):", base_privkey)
    print("Base Public Key (hex):", base_pubkey)
    print("Mnemonic Words:", mnemonic_words)
    
    print("\nDerived Addresses:")
    print("=" * 50)  # Section separator
    
    # Process each address
    for index, privkey, pubkey, address in derived_addresses:
        # Print address header
        print(f"\nAddress {index}:")
        print("-" * 40)
        
        # Show QR code if requested
        if show_qr:
            print(generate_ascii_qr(address, f"Address {index}", "address", compact=True))
        
        # Print address details
        print(f"Address: {address}")
        
        # Show balance if requested
        if show_balance:
            balance_info = fetch_address_balance(address, network)
            if balance_info["error"]:
                print(f"Balance: Error - {balance_info['error']}")
            else:
                print(f"Balance: {balance_info['balance_btc']:.8f} BTC")
                print(f"Transactions: {balance_info['tx_count']}")
        
        # Print separator between addresses
        print("-" * 40)

def fetch_address_balance(address: str, network: str) -> Dict[str, Union[int, str, None]]:
    """
    Fetch the balance of a Bitcoin address using Blockstream's Esplora API.
    
    Args:
        address (str): The Bitcoin address to check
        network (str): Either 'mainnet' or 'testnet'
    
    Returns:
        dict: Dictionary containing balance information and status
    """
    # Define API base URLs for different networks
    api_urls = {
        "mainnet": "https://blockstream.info/api",
        "testnet": "https://blockstream.info/testnet/api",
        "signet": "https://blockstream.info/signet/api"
    }
    
    # Get the appropriate API URL
    base_url = api_urls.get(network)
    if not base_url:
        return {
            "balance": None,
            "error": f"Unsupported network: {network}"
        }

    try:
        # Make API request to get address information
        response = requests.get(f"{base_url}/address/{address}")
        response.raise_for_status()  # Raise an exception for bad status codes
        
        data = response.json()
        
        # Convert satoshis to BTC (1 BTC = 100,000,000 satoshis)
        balance_sat = data.get('chain_stats', {}).get('funded_txo_sum', 0) - \
                     data.get('chain_stats', {}).get('spent_txo_sum', 0)
        balance_btc = balance_sat / 100_000_000
        
        # Get the number of transactions
        tx_count = data.get('chain_stats', {}).get('tx_count', 0)
        
        return {
            "balance_sat": balance_sat,
            "balance_btc": balance_btc,
            "tx_count": tx_count,
            "error": None
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "balance_sat": None,
            "balance_btc": None,
            "tx_count": None,
            "error": f"API request failed: {str(e)}"
        }

def generate_address(privkey=None, network="testnet"):
    """
    Generate or import a Bitcoin address from a private key.
    
    Args:
        privkey (str, optional): Private key in WIF format
        network (str): Bitcoin network to use (default: testnet)
    
    Returns:
        tuple: (private_key, public_key, mnemonic_words, derived_addresses)
               or (None, None, None, error_message) if an error occurs
    """
    try:
        if privkey is None:
            # Generate new wallet with mnemonic
            mnemo = Mnemonic("english")
            mnemonic_words = mnemo.generate(strength=256)
            seed = mnemo.to_seed(mnemonic_words)
            
            # Convert network name for bitcoinlib
            bitcoinlib_network = get_bitcoinlib_network(network)
            
            # Create HD master key from seed
            master_key = HDKey.from_seed(seed, network=bitcoinlib_network)
            
            # Set derivation path based on network (BIP-44)
            coin_type = "0" if network == "mainnet" else "1"
            path = f"m/44'/{coin_type}'/0'/0"
            
            # Derive the key
            account_key = master_key.subkey_for_path(path)
            derived_key = account_key.subkey_for_path("0")
            
            # Convert the secret to the correct format
            secret_bytes = derived_key.secret
            if isinstance(secret_bytes, int):
                secret_bytes = secret_bytes.to_bytes(32, 'big')
            base_private_key = CBitcoinSecret.from_secret_bytes(secret_bytes)
            
        else:
            # Import existing private key
            base_private_key = CBitcoinSecret(privkey)
            mnemonic_words = "N/A (provided private key)"

        # Get the public key
        base_pubkey = base_private_key.pub
        
        # Generate the address from the public key
        base_address = P2PKHBitcoinAddress.from_pubkey(base_pubkey)
        
        # Create return values
        base_privkey_str = str(base_private_key)
        derived_addresses = [(0, base_privkey_str, base_pubkey.hex(), str(base_address))]
        
        return base_privkey_str, base_pubkey.hex(), mnemonic_words, derived_addresses
    
    except ValueError as e:
        return None, None, None, f"Error: {str(e)}"
    except Exception as e:
        return None, None, None, f"Error: Invalid private key format or unexpected issue ({str(e)})"
def print_table(base_privkey, base_pubkey, mnemonic_words, derived_addresses):
    print("\nBase Private Key (WIF):", base_privkey)
    print("Base Public Key (hex):", base_pubkey)
    print("Mnemonic Words:", mnemonic_words)
    print("\nDerived Addresses:")
    print("-" * 80)
    print(f"{'Index':<6} {'Private Key (WIF)':<34} {'Public Key (hex)':<34} {'Address':<26}")
    print("-" * 80)
    for index, privkey, pubkey, address in derived_addresses:
        print(f"{index:<6} {privkey:<34} {pubkey:<34} {address:<26}")
    print("-" * 80)


def generate_ascii_qr(data: str, label: str = "", data_type: str = "address", compact: bool = True) -> str:
    """
    Generate a compact ASCII QR code with clear labeling.
    
    Args:
        data (str): The data to encode in the QR code
        label (str): Label for this specific QR code
        data_type (str): Type of data being encoded ('address', 'privkey', or 'pubkey')
        compact (bool): Whether to generate a compact QR code
    """
    try:
        # Create QR code instance with optimized parameters for smaller size
        qr = qrcode.QRCode(
            version=None,  # Allow automatic version selection
            error_correction=qrcode.constants.ERROR_CORRECT_L,  # Use lower error correction for smaller codes
            box_size=1,    # Minimum box size
            border=1       # Minimum border size
        )
        
        # For addresses, we can use uppercase and remove any unnecessary characters
        if data_type == "address":
            data = data.upper().strip()
        
        qr.add_data(data)
        qr.make(fit=True)  # Ensure it fits in the smallest possible size
        
        # Convert to ASCII art with half-height characters for more compact display
        ascii_art = []
        
        # Add compact header
        if label:
            ascii_art.append(f"- {label} -")
        
        # Convert QR matrix to ASCII using half-height blocks for compact display
        matrix = qr.get_matrix()
        if compact:
            # Process two rows at a time for half-height output
            for i in range(0, len(matrix), 2):
                line = ""
                for j in range(len(matrix[i])):
                    # Combine two vertical pixels into one character
                    top = matrix[i][j]
                    bottom = matrix[i + 1][j] if i + 1 < len(matrix) else False
                    
                    if top and bottom:
                        line += "█"  # Full block
                    elif top:
                        line += "▀"  # Upper half block
                    elif bottom:
                        line += "▄"  # Lower half block
                    else:
                        line += " "  # Empty space
                ascii_art.append(line)
        else:
            # Original full-height display
            for row in matrix:
                line = ""
                for cell in row:
                    line += "██" if cell else "  "
                ascii_art.append(line)
        
        return "\n".join(ascii_art)
        
    except Exception as e:
        return f"Error generating QR code: {str(e)}"

def create_payment_request(address: str, amount: float = None, message: str = None, network: str = "testnet") -> str:
    """
    Create a Bitcoin payment request URI following BIP21.
    
    Args:
        address (str): Bitcoin address to receive payment
        amount (float): Optional amount in BTC
        message (str): Optional message/label for the payment
        network (str): Network type (mainnet, testnet, signet)
    
    Returns:
        str: Bitcoin URI for the payment request
    """
    # Base URI starts with bitcoin: for mainnet, bitcoin-testnet: for testnet
    scheme = "bitcoin:" if network == "mainnet" else "bitcoin-testnet:"
    uri = f"{scheme}{address}"
    
    # Add optional parameters
    params = []
    if amount is not None:
        params.append(f"amount={amount}")
    if message is not None:
        params.append(f"message={message}")
    
    # Combine parameters with the URI
    if params:
        uri += "?" + "&".join(params)
    
    return uri

def fetch_utxos(address: str, network: str) -> List[Dict]:
    """
    Fetch unspent transaction outputs (UTXOs) for an address.
    """
    api_urls = {
        "mainnet": "https://blockstream.info/api",
        "testnet": "https://blockstream.info/testnet/api",
        "signet": "https://blockstream.info/signet/api"
    }
    base_url = api_urls.get(network)
    
    try:
        response = requests.get(f"{base_url}/address/{address}/utxo")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch UTXOs: {str(e)}")
        
def create_raw_transaction(utxos: List[Dict], to_address: str, amount_sat: int, from_privkey: str) -> bitcoin.core.CTransaction:
    """
    Create a raw Bitcoin transaction from UTXOs.
    
    Args:
        utxos (List[Dict]): List of unspent transaction outputs to use as inputs
        to_address (str): Destination Bitcoin address
        amount_sat (int): Amount to send in satoshis
        from_privkey (str): Private key in WIF format to sign the transaction
    
    Returns:
        CTransaction: The created and signed transaction
    """
    from bitcoin.core import CMutableTransaction, CMutableTxIn, CMutableTxOut, COutPoint
    from bitcoin.core.script import CScript, SignatureHash, SIGHASH_ALL
    from bitcoin.core.scripteval import SCRIPT_VERIFY_P2SH
    
    # Convert private key from WIF format
    private_key = CBitcoinSecret(from_privkey)
    public_key = private_key.pub
    
    # Create the basic P2PKH scriptPubKey
    script_pubkey = CScript([public_key, bitcoin.core.opcodes.OP_CHECKSIG])
    
    # Create transaction inputs from UTXOs
    tx_inputs = []
    total_input = 0
    
    for utxo in utxos:
        # Create input pointing to the UTXO
        outpoint = COutPoint(
            bitcoin.core.lx(utxo['txid']),  # Convert txid to internal format
            utxo['vout']
        )
        tx_in = CMutableTxIn(outpoint)
        tx_inputs.append(tx_in)
        total_input += utxo['value']
        
        # Stop adding inputs if we have enough funds
        if total_input >= amount_sat:
            break
    
    # Calculate change amount (assuming 1000 satoshis fee for simplicity)
    # In a real implementation, you'd want to calculate the fee based on tx size
    fee = 1000
    change_amount = total_input - amount_sat - fee
    
    # Create transaction outputs
    tx_outputs = []
    
    # Output for the recipient
    recipient_script = bitcoin.core.standard.CScript.to_p2pkh(
        bitcoin.core.standard.P2PKHBitcoinAddress(to_address).to_scriptPubKey()
    )
    tx_outputs.append(CMutableTxOut(amount_sat, recipient_script))
    
    # Add change output if there's change to return
    if change_amount > 0:
        change_script = bitcoin.core.standard.CScript.to_p2pkh(
            public_key.to_p2pkh_scriptPubKey()
        )
        tx_outputs.append(CMutableTxOut(change_amount, change_script))
    
    # Create the unsigned transaction
    tx = CMutableTransaction(tx_inputs, tx_outputs)
    
    # Sign each input
    for i, utxo in enumerate(utxos):
        # Create the signature hash for this input
        sighash = SignatureHash(
            script_pubkey,
            tx,
            i,
            SIGHASH_ALL
        )
        
        # Sign the input
        sig = private_key.sign(sighash) + bytes([SIGHASH_ALL])
        
        # Set the signature and public key in the input script
        tx.vin[i].scriptSig = CScript([sig, public_key])
    
    return tx

def broadcast_transaction(tx_hex: str, network: str) -> str:
    """
    Broadcast a signed transaction to the Bitcoin network.
    
    Args:
        tx_hex (str): The raw transaction in hexadecimal format
        network (str): The Bitcoin network to use (mainnet, testnet, signet)
    
    Returns:
        str: The transaction ID if successful
    """
    # Define API endpoints for different networks
    api_urls = {
        "mainnet": "https://blockstream.info/api",
        "testnet": "https://blockstream.info/testnet/api",
        "signet": "https://blockstream.info/signet/api"
    }
    
    base_url = api_urls.get(network)
    if not base_url:
        raise ValueError(f"Unsupported network: {network}")
    
    try:
        # Convert transaction to hex
        if isinstance(tx_hex, bytes):
            tx_hex = tx_hex.hex()
        
        # Send the transaction to the network
        response = requests.post(
            f"{base_url}/tx",
            data=tx_hex
        )
        
        # Check if broadcast was successful
        if response.status_code == 200:
            # The response is the transaction ID
            return response.text.strip()
        else:
            error_msg = response.text if response.text else f"HTTP {response.status_code}"
            raise Exception(f"Failed to broadcast transaction: {error_msg}")
            
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error while broadcasting transaction: {str(e)}")

def create_and_send_transaction(from_address: str, from_privkey: str, 
                              to_address: str, amount: float, network: str) -> str:
    """
    Create and broadcast a Bitcoin transaction.
    
    Args:
        from_address (str): Sender's address
        from_privkey (str): Sender's private key in WIF format
        to_address (str): Recipient's address
        amount (float): Amount to send in BTC
        network (str): Network type (mainnet, testnet, signet)
    
    Returns:
        str: Transaction ID of the broadcast transaction
    """
    try:
        # Convert amount to satoshis
        amount_sat = int(amount * 100_000_000)
        
        # Fetch UTXOs
        utxos = fetch_utxos(from_address, network)
        if not utxos:
            raise Exception("No UTXOs found for this address")
        
        # Calculate total available balance
        total_available = sum(utxo['value'] for utxo in utxos)
        if total_available < amount_sat:
            raise Exception(f"Insufficient balance. Available: {total_available/100_000_000} BTC")
        
        # Create transaction using python-bitcoinlib
        # (We'll need to implement the actual transaction creation here)
        # This is a placeholder for the actual implementation
        tx = create_raw_transaction(utxos, to_address, amount_sat, from_privkey)
        
        # Broadcast transaction
        tx_id = broadcast_transaction(tx.serialize(), network)
        
        return tx_id
        
    except Exception as e:
        raise Exception(f"Transaction failed: {str(e)}")

if __name__ == "__main__":
    args = parse_args()
    SelectParams(args.network)
    
    try:
        if args.receive:
            # Handle receive operation
            if not args.amount and not args.message:
                print("Tip: You can add --amount and --message to create a complete payment request")
            
            # Generate new address if not importing a private key
            if not args.privkey:
                privkey, pubkey, mnemonic, addresses = generate_address(None, args.network)
                receive_address = addresses[0][3]  # Use first derived address
            else:
                # Use existing address if private key provided
                privkey, pubkey, mnemonic, addresses = generate_address(args.privkey, args.network)
                receive_address = addresses[0][3]
            
            # Create payment request
            payment_uri = create_payment_request(
                receive_address,
                args.amount,
                args.message,
                args.network
            )
            
            print("\nPayment Request Details:")
            print("-" * 40)
            print(f"Address: {receive_address}")
            if args.amount:
                print(f"Amount: {args.amount} BTC")
            if args.message:
                print(f"Message: {args.message}")
            print("\nPayment URI:")
            print(payment_uri)
            
            # Show QR code for the payment URI
            print("\nScan this QR code to pay:")
            print(generate_ascii_qr(payment_uri, "Payment Request", "uri"))
            
        elif args.send:
            if not args.amount:
                raise ValueError("Please specify amount to send using --amount")
            if not args.privkey:
                raise ValueError("Please provide a private key to send from")
            
            # Generate wallet info
            privkey, pubkey, mnemonic, addresses = generate_address(args.privkey, args.network)
            from_address = addresses[0][3]
            
            # Send transaction
            tx_id = create_and_send_transaction(
                from_address,
                args.privkey,
                args.send,
                args.amount,
                args.network
            )
            
            print("\nTransaction sent successfully!")
            print(f"Transaction ID: {tx_id}")
            print(f"You can track your transaction at: https://blockstream.info/{args.network}/tx/{tx_id}")
            
        else:
            # Regular wallet generation/display
            privkey, pubkey, mnemonic, result = generate_address(args.privkey, args.network)
            if privkey is None and pubkey is None:
                print(result)
            else:
                print_table_with_balances_and_qr(
                    privkey, pubkey, mnemonic, result,
                    args.network, args.check_balance, args.show_qr
                )
                
                if args.output:
                    save_to_json(args.output, privkey, pubkey, mnemonic, result, args.network)
                    
    except Exception as e:
        print(f"Error: {str(e)}")