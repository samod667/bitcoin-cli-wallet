import os
import sys
from mnemonic import Mnemonic
from bitcoin import SelectParams
from bitcoin.wallet import CBitcoinSecret, P2PKHBitcoinAddress
from bitcoin.core import x
from bitcoin.core.key import CPubKey
import hashlib
import binascii

SelectParams('testnet')

def generate_address(privkey=None):
    try:
        if privkey is None:
            # Generate a BIP-39 mnemonic if no private key is provided
            mnemo = Mnemonic("english")
            mnemonic_words = mnemo.generate(strength=256)  # 24 words
            seed = mnemo.to_seed(mnemonic_words)
            
            # Derive a master key from the seed (simplified, not full BIP-32)
            # Use SHA-256 of seed for simplicity (in practice, use BIP-32 HD)
            base_key_bytes = hashlib.sha256(seed).digest()  # 32 bytes
            base_private_key = CBitcoinSecret.from_secret_bytes(base_key_bytes)
        else:
            # Use the provided private key
            base_private_key = CBitcoinSecret(privkey)
            if not base_private_key.is_testnet():
                raise ValueError("Provided private key is for mainnet, not testnet.")
            mnemonic_words = "N/A (provided private key)"  # No mnemonic for input key
        
        # Store the base private key and public key
        base_privkey_str = str(base_private_key)
        base_pubkey = base_private_key.pub
        
        # Generate 10 derived addresses
        derived_addresses = []
        base_key_int = int.from_bytes(base_private_key.to_bytes(), 'big')
        N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141  # Curve order
        for i in range(10):
            # Derive a new private key by adding an index, keeping it within curve order
            derived_key_int = (base_key_int + i) % N
            derived_key_bytes = derived_key_int.to_bytes(32, 'big')
            try:
                derived_private_key = CBitcoinSecret.from_secret_bytes(derived_key_bytes)
                derived_public_key = derived_private_key.pub
                derived_address = P2PKHBitcoinAddress.from_pubkey(derived_public_key)
                derived_addresses.append((i, str(derived_private_key), derived_public_key.hex(), str(derived_address)))
            except Exception as e:
                derived_addresses.append((i, "N/A", "N/A", f"Failed to derive: {str(e)}"))
        
        # Return base keys, mnemonic, and derived addresses
        return base_privkey_str, base_pubkey.hex(), mnemonic_words, derived_addresses
    
    except ValueError as e:
        return None, None, None, f"Error: {str(e)}"
    except Exception as e:
        return None, None, None, f"Error: Invalid private key format or unexpected issue ({str(e)})"

def print_table(base_privkey, base_pubkey, mnemonic_words, derived_addresses):
    # Nice CLI table output
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

if __name__ == "__main__":
    # Check if a private key was provided as an argument
    if len(sys.argv) > 1:
        privkey_input = sys.argv[1]
    else:
        privkey_input = None
    
    # Generate the keys and addresses
    privkey, pubkey, mnemonic, result = generate_address(privkey_input)
    
    # Check if there was an error
    if privkey is None and pubkey is None:
        print(result)  # Error message
    else:
        print_table(privkey, pubkey, mnemonic, result)