# wallet/display.py

from typing import List, Tuple, Optional
from art import text2art
from .qrcode import generate_ascii_qr
from .network import fetch_address_balance

class WalletDisplay:
    """
    Handles the formatting and display of wallet information in the terminal.
    
    This class provides methods for displaying wallet information in a clear,
    organized manner. It handles different display modes (basic info, balances,
    QR codes) and ensures consistent formatting across the application.
    """
    
    @staticmethod
    def show_wallet_info(base_privkey: str, base_pubkey: str, 
                        mnemonic_words: str, derived_addresses: List[Tuple],
                        network: str, show_balance: bool = False, 
                        show_qr: bool = False) -> None:
        """
        Display complete wallet information with optional balances and QR codes.
        
        This method organizes and displays all wallet information in a clear,
        structured format. It can optionally include balance information and
        QR codes based on the user's requirements.
        
        Args:
            base_privkey: Base private key in WIF format
            base_pubkey: Base public key in hex format
            mnemonic_words: Mnemonic seed phrase
            derived_addresses: List of derived address tuples
            network: Network type (mainnet, testnet, signet)
            show_balance: Whether to display balance information
            show_qr: Whether to display QR codes
        """
        # Display wallet header
        print("\n" + text2art("Bitcoin Wallet", font="small"))
        
        # Show seed phrase for new wallets
        if mnemonic_words != "N/A (provided private key)":
            print("\nSeed Phrase (Keep Secret and Backup!):")
            print(mnemonic_words)
        
        # Display addresses and keys
        print("\nDerived Addresses and Keys:")
        print("=" * 50)
        
        # Create table header
        header = (f"{'Index':<6} {'Private Key (WIF)':<52} "
                 f"{'Public Key (hex)':<66} {'Address':<35}")
        print(header)
        print("-" * 160)
        
        # Display address information
        for index, privkey, pubkey, address in derived_addresses:
            line = f"{index:<6} {privkey:<52} {pubkey:<66} {address:<35}"
            print(line)
        
        print("-" * 160)
        
        # Show balance information if requested
        if show_balance:
            WalletDisplay._show_balances(derived_addresses, network)
        
        # Show QR codes if requested
        if show_qr:
            WalletDisplay._show_qr_codes(derived_addresses)
    
    @staticmethod
    def _show_balances(derived_addresses: List[Tuple], network: str) -> None:
        """
        Display balance information for all addresses.
        """
        print("\nBalance Information:")
        print("=" * 50)
        print(f"{'Index':<6} {'Address':<35} {'Balance (BTC)':<15} {'Transactions':<12}")
        print("-" * 70)
        
        for index, _, _, address in derived_addresses:
            balance_info = fetch_address_balance(address, network)
            if balance_info["error"]:
                balance_str = f"Error: {balance_info['error']}"
                tx_count_str = "N/A"
            else:
                balance_str = f"{balance_info['balance_btc']:.8f}"
                tx_count_str = str(balance_info['tx_count'])
            
            print(f"{index:<6} {address:<35} {balance_str:<15} {tx_count_str:<12}")
        
        print("-" * 70)
    
    @staticmethod
    def _show_qr_codes(derived_addresses: List[Tuple]) -> None:
        """
        Display QR codes for all addresses.
        """
        print("\nAddress QR Codes:")
        print("=" * 50)
        
        for index, _, _, address in derived_addresses:
            print(f"\nQR Code for Address {index}:")
            print(generate_ascii_qr(address, f"Address {index}", "address", compact=True))
            print(f"Address: {address}")
            print("-" * 40)
    