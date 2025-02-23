# wallet/keys.py

import bitcoin
from mnemonic import Mnemonic
from bitcoin.wallet import CBitcoinSecret, P2PKHBitcoinAddress
from bitcoinlib.keys import HDKey
from typing import Tuple, List, Optional, Union

def get_bitcoinlib_network(network: str) -> str:
    """
    Convert python-bitcoinlib network names to bitcoinlib network names.
    
    Args:
        network: Network name in python-bitcoinlib format
    
    Returns:
        Network name in bitcoinlib format
    """
    network_mapping = {
        "mainnet": "bitcoin",
        "testnet": "testnet",
        "signet": "signet"
    }
    return network_mapping.get(network, "testnet")

def generate_wallet(privkey: Optional[str] = None, 
                   network: str = "testnet") -> Tuple[str, str, str, List[Tuple]]:
    """
    Generate or import a Bitcoin wallet, producing 10 derived addresses.
    
    This function either creates a new HD wallet from a generated seed or imports
    an existing wallet from a private key. For new wallets, it generates 10
    derived addresses following BIP-44 standards.
    
    Args:
        privkey: Optional private key in WIF format for importing
        network: Bitcoin network to use (default: testnet)
    
    Returns:
        Tuple containing:
        - Base private key (WIF format)
        - Base public key (hex format)
        - Mnemonic words (or "N/A" for imported keys)
        - List of derived addresses (index, privkey, pubkey, address)
    """
    try:
        if privkey is None:
            # Generate new wallet with mnemonic
            mnemo = Mnemonic("english")
            mnemonic_words = mnemo.generate(strength=256)
            seed = mnemo.to_seed(mnemonic_words)
            
            bitcoinlib_network = get_bitcoinlib_network(network)
            master_key = HDKey.from_seed(seed, network=bitcoinlib_network)
            
            # Set derivation path based on network (BIP-44)
            coin_type = "0" if network == "mainnet" else "1"
            path = f"m/44'/{coin_type}'/0'/0"
            
            # Derive the account key
            account_key = master_key.subkey_for_path(path)
            
            # Generate 10 derived addresses
            derived_addresses = []
            for i in range(10):
                derived_key = account_key.subkey_for_path(str(i))
                secret_bytes = derived_key.secret
                if isinstance(secret_bytes, int):
                    secret_bytes = secret_bytes.to_bytes(32, 'big')
                
                derived_private_key = CBitcoinSecret.from_secret_bytes(secret_bytes)
                derived_public_key = derived_private_key.pub
                derived_address = P2PKHBitcoinAddress.from_pubkey(derived_public_key)
                
                derived_addresses.append((
                    i,
                    str(derived_private_key),
                    derived_public_key.hex(),
                    str(derived_address)
                ))
            
            # Use the first derived key as our base key
            base_private_key = CBitcoinSecret(derived_addresses[0][1])
            base_pubkey = base_private_key.pub
            
        else:
            # Import existing private key
            base_private_key = CBitcoinSecret(privkey)
            mnemonic_words = "N/A (provided private key)"
            
            base_pubkey = base_private_key.pub
            base_address = P2PKHBitcoinAddress.from_pubkey(base_pubkey)
            
            derived_addresses = [(0, str(base_private_key), 
                                base_pubkey.hex(), str(base_address))]

        return (str(base_private_key), base_pubkey.hex(), 
                mnemonic_words, derived_addresses)
    
    except ValueError as e:
        return None, None, None, f"Error: {str(e)}"
    except Exception as e:
        return None, None, None, f"Error: Invalid private key format or unexpected issue ({str(e)})"