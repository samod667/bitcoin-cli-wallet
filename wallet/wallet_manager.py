import os
import json
import time
import getpass
from typing import Dict, Optional, Tuple, List
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class WalletManager:
    """
    Manages the active wallet state between CLI commands.
    
    This class provides a secure way to store and retrieve wallet information,
    so users don't need to provide their private key for every command.
    """
    
    # Constants
    STATE_DIR = os.path.expanduser("~/.bitcoin_wallet")
    STATE_FILE = os.path.join(STATE_DIR, "wallet_state.json")
    SESSION_TIMEOUT = 30 * 60  # 30 minutes in seconds
    
    def __init__(self):
        """Initialize wallet manager and create state directory if needed."""
        os.makedirs(self.STATE_DIR, exist_ok=True)
        self.active_wallet = None
        self.password = None
        self._load_state()
    
    def _load_state(self) -> None:
        """Load active wallet state from file if it exists."""
        if not os.path.exists(self.STATE_FILE):
            return
            
        try:
            with open(self.STATE_FILE, 'r') as f:
                state = json.load(f)
            
            # Check if session has expired
            if time.time() - state.get('timestamp', 0) > self.SESSION_TIMEOUT:
                print("Wallet session has expired. Please load your wallet again.")
                self._clear_state()
                return
                
            self.active_wallet = state
                
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error loading wallet state: {str(e)}")
            self._clear_state()
    
    def _save_state(self) -> None:
        """Save active wallet state to file."""
        if not self.active_wallet:
            return
            
        # Update timestamp
        self.active_wallet['timestamp'] = time.time()
        
        try:
            with open(self.STATE_FILE, 'w') as f:
                json.dump(self.active_wallet, f)
                
            # Set secure permissions
            os.chmod(self.STATE_FILE, 0o600)  # Only owner can read/write
                
        except Exception as e:
            print(f"Error saving wallet state: {str(e)}")
    
    def _clear_state(self) -> None:
        """Clear active wallet state and remove state file."""
        self.active_wallet = None
        self.password = None
        
        if os.path.exists(self.STATE_FILE):
            try:
                os.remove(self.STATE_FILE)
            except Exception as e:
                print(f"Error clearing wallet state: {str(e)}")
    
    def _encrypt_privkey(self, privkey: str) -> str:
        """Encrypt private key using a derived key."""
        if not self.password:
            raise ValueError("No password set for encryption")
            
        # Generate salt and derive key
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.password.encode()))
        
        # Encrypt private key
        f = Fernet(key)
        encrypted_data = f.encrypt(privkey.encode())
        
        # Return salt and encrypted data
        return base64.b64encode(salt + encrypted_data).decode()
    
    def _decrypt_privkey(self, encrypted_data: str) -> str:
        """Decrypt private key using the derived key."""
        if not self.password:
            raise ValueError("No password set for decryption")
            
        # Decode the combined salt+data
        raw_data = base64.b64decode(encrypted_data)
        salt, encrypted_privkey = raw_data[:16], raw_data[16:]
        
        # Derive key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.password.encode()))
        
        # Decrypt private key
        f = Fernet(key)
        decrypted_data = f.decrypt(encrypted_privkey)
        
        return decrypted_data.decode()
    
    def load_wallet(self, privkey: str, network: str = "testnet", 
               addresses: List = None, address_type: str = "segwit", pubkey: str = None, 
               encrypt: bool = True) -> bool:
        """
        Load a wallet and make it active for future commands.
        
        Args:
            privkey: The private key in WIF format
            network: Bitcoin network (mainnet, testnet, signet)
            addresses: Optional list of pre-generated addresses
            pubkey: Optional public key
            encrypt: Whether to encrypt the private key
            
        Returns:
            True if wallet was loaded successfully
        """
        try:
            # Encrypt private key if requested
            if encrypt:
                # Encryption code...
                stored_privkey = self._encrypt_privkey(privkey)
                encrypted = True
            else:
                stored_privkey = privkey
                encrypted = False
            
            # Create wallet state
            self.active_wallet = {
                'private_key': stored_privkey,
                'network': network,
                'encrypted': encrypted,
                'timestamp': time.time(),
                'address_type': address_type

            }
            
            # Add optional data if available
            if pubkey:
                self.active_wallet['public_key'] = pubkey
                
            if addresses:
                # Only store addresses, not private keys
                self.active_wallet['addresses'] = [
                    {'index': addr[0], 'address': addr[3]} 
                    for addr in addresses
                ]
            
            # Save to disk
            self._save_state()
            return True
            
        except Exception as e:
            print(f"Error loading wallet: {str(e)}")
            return False
    
    def load_wallet_from_file(self, filename: str) -> bool:
        """
        Load a wallet from a saved wallet file.
        
        Args:
            filename: Path to the wallet JSON file
            
        Returns:
            True if wallet was loaded successfully
        """
        try:
            with open(filename, 'r') as f:
                wallet_data = json.load(f)
            
            # Extract key information
            privkey = wallet_data.get('private_key')
            network = wallet_data.get('network', 'testnet')
            address_type = "both"  # Default for loaded wallets
            
            # Check if private key exists
            if not privkey:
                print("Error: No private key found in the wallet file.")
                return False
            
            # Ask for password for encryption
            while not self.password:
                password = getpass.getpass("Enter password to secure wallet: ")
                confirm = getpass.getpass("Confirm password: ")
                
                if password == confirm and password:
                    self.password = password
                else:
                    print("Passwords don't match or are empty. Try again.")
                    
            # Extract addresses if available
            addresses = None
            if 'addresses' in wallet_data:
                addresses = [
                    (addr.get('index', i), None, None, addr.get('address'))
                    for i, addr in enumerate(wallet_data['addresses'])
                ]
            
            # Load the wallet
            return self.load_wallet(
                privkey=privkey,
                network=network,
                address_type=address_type,
                addresses=addresses,
                pubkey=wallet_data.get('public_key'),
                encrypt=True
            )
            
        except FileNotFoundError:
            print(f"Error: Wallet file '{filename}' not found.")
            return False
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in wallet file '{filename}'.")
            return False
        except Exception as e:
            print(f"Failed to load wallet: {str(e)}")
            return False
    
    def unload_wallet(self) -> bool:
        """
        Unload the active wallet for security.
        
        Returns:
            True if a wallet was unloaded
        """
        if not self.active_wallet:
            print("No wallet is currently loaded.")
            return False
            
        self._clear_state()
        print("Wallet unloaded successfully.")
        return True
    
    def get_active_wallet(self) -> Optional[Dict]:
        """
        Get the currently active wallet with decrypted private key.
        
        Returns:
            Dict with wallet information or None if no wallet is active
        """
        if not self.active_wallet:
            return None
            
        # Create a copy to avoid modifying the stored state
        wallet = dict(self.active_wallet)
        
        # Decrypt private key if necessary
        if wallet.get('encrypted', False):
            if not self.password:
                # Prompt for password if not set
                self.password = getpass.getpass("Enter wallet password: ")
                
            try:
                wallet['private_key'] = self._decrypt_privkey(wallet['private_key'])
                wallet['encrypted'] = False  # Mark as decrypted for this instance
            except Exception as e:
                print(f"Error decrypting private key: {str(e)}")
                return None
                
        # Update access timestamp
        self._save_state()
            
        return wallet
    
    def is_wallet_loaded(self) -> bool:
        """Check if a wallet is currently loaded."""
        return self.active_wallet is not None
    
    def get_network(self) -> str:
        """Get the network of the active wallet."""
        if not self.active_wallet:
            return "testnet"  # Default
        return self.active_wallet.get('network', 'testnet')
    
    def get_address_type(self) -> str:
        """Get the address type of the active wallet."""
        if not self.active_wallet:
            return "segwit"  # Default
        return self.active_wallet.get('address_type', 'segwit')
    
    def get_addresses(self) -> List[str]:
        """Get addresses from the active wallet."""
        if not self.active_wallet or 'addresses' not in self.active_wallet:
            return []
        return [addr.get('address') for addr in self.active_wallet.get('addresses', [])]
    
    def update_wallet_info(self, addresses: List = None) -> None:
        """
        Update wallet information with new addresses.
        
        Args:
            addresses: New address list to store
        """
        if not self.active_wallet:
            return
            
        if addresses:
            self.active_wallet['addresses'] = [
                {'index': addr[0], 'address': addr[3]} 
                for addr in addresses
            ]
            
        self._save_state()
    

# Create global instance
wallet_manager = WalletManager()