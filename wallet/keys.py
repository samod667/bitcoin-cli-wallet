import bitcoin
from mnemonic import Mnemonic
from bitcoin import SelectParams
from bitcoin.wallet import CBitcoinSecret, P2PKHBitcoinAddress, CBech32BitcoinAddress
from bitcoin.core import Hash160
from bitcoin.core.script import CScript, OP_0
from bitcoinlib.keys import HDKey
from typing import Tuple, List, Optional, Union

def get_bitcoinlib_network(network: str) -> str:
    """Convert python-bitcoinlib network names to bitcoinlib network names."""
    network_mapping = {
        "mainnet": "bitcoin",
        "testnet": "testnet",
        "signet": "signet"
    }
    return network_mapping.get(network, "testnet")

def create_p2wpkh_address(pubkey: bytes, network: str = "testnet") -> str:
    """
    Create a native SegWit (bech32) P2WPKH address from a public key.
    """
    # Get the hash160 of the public key
    pubkey_hash = Hash160(pubkey)
    
    # For P2WPKH, the witness version is 0 and witness program is the pubkey hash
    return str(CBech32BitcoinAddress.from_bytes(0, pubkey_hash))

def generate_wallet(privkey: Optional[str] = None, 
                   network: str = "testnet",
                   address_type: str = "both") -> Tuple[str, str, str, List[Tuple]]:
    """
    Generate or import a Bitcoin wallet with unique addresses.
    """
    try:
        # Initialize the network settings
        SelectParams(network)
        
        # Generate new wallet with mnemonic
        if privkey is None:
            # Generate new wallet with mnemonic
            mnemo = Mnemonic("english")
            mnemonic_words = mnemo.generate(strength=256)
            seed = mnemo.to_seed(mnemonic_words)
            
            # Convert network name for bitcoinlib
            bitcoinlib_network = get_bitcoinlib_network(network)
            master_key = HDKey.from_seed(seed, network=bitcoinlib_network)
            
            # Set derivation paths
            coin_type = "0" if network == "mainnet" else "1"
            derived_addresses = []
            
            # Determine which address types to generate
            address_types = []
            if address_type in ["both", "segwit"]:
                # BIP-84 path for native SegWit
                address_types.append(("segwit", f"m/84'/{coin_type}'/0'/0"))
            if address_type in ["both", "legacy"]:
                # BIP-44 path for legacy
                address_types.append(("legacy", f"m/44'/{coin_type}'/0'/0"))
            
            # Track unique addresses to prevent duplicates
            unique_addresses = set()
            
            for addr_type, derivation_path in address_types:
                account_key = master_key.subkey_for_path(derivation_path)
                
                for i in range(10):
                    try:
                        derived_key = account_key.subkey_for_path(str(i))
                        secret_bytes = derived_key.secret
                        if isinstance(secret_bytes, int):
                            secret_bytes = secret_bytes.to_bytes(32, 'big')
                        
                        derived_private_key = CBitcoinSecret.from_secret_bytes(secret_bytes)
                        derived_public_key = derived_private_key.pub
                        
                        if addr_type == "segwit":
                            derived_address = create_p2wpkh_address(derived_public_key, network)
                        else:
                            derived_address = str(P2PKHBitcoinAddress.from_pubkey(derived_public_key))
                        
                        # Only add if address is unique
                        if derived_address not in unique_addresses:
                            derived_addresses.append((
                                len(derived_addresses),  # Use sequential index
                                str(derived_private_key),
                                derived_public_key.hex(),
                                derived_address
                            ))
                            unique_addresses.add(derived_address)
                    except Exception as e:
                        print(f"Error deriving {addr_type} address {i}: {str(e)}")
                        continue
            
            if not derived_addresses:
                raise ValueError("Failed to generate any valid addresses")
                
            base_private_key = CBitcoinSecret(derived_addresses[0][1])
            base_pubkey = base_private_key.pub
            
        else:
            # Import existing private key
            base_private_key = CBitcoinSecret(privkey)
            mnemonic_words = "N/A (provided private key)"
            base_pubkey = base_private_key.pub
            
            derived_addresses = []
            unique_addresses = set()
            
            # Determine which address types to generate
            address_types = []
            if address_type in ["both", "segwit"]:
                # Generate SegWit address
                segwit_address = create_p2wpkh_address(base_pubkey, network)
                if segwit_address not in unique_addresses:
                    derived_addresses.append((
                        0, 
                        str(base_private_key),
                        base_pubkey.hex(), 
                        segwit_address
                    ))
                    unique_addresses.add(segwit_address)
            
            if address_type in ["both", "legacy"]:
                # Generate Legacy address
                legacy_address = str(P2PKHBitcoinAddress.from_pubkey(base_pubkey))
                if legacy_address not in unique_addresses:
                    derived_addresses.append((
                        len(derived_addresses),  # Use sequential index 
                        str(base_private_key),
                        base_pubkey.hex(), 
                        legacy_address
                    ))
                    unique_addresses.add(legacy_address)

        return (str(base_private_key), base_pubkey.hex(),
                mnemonic_words, derived_addresses)
                
    except Exception as e:
        raise ValueError(f"Wallet generation failed: {str(e)}")