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
        Display complete wallet information with improved formatting.
        """
        # Display wallet header
        print("\n" + text2art("Bitcoin Wallet", font="small"))
        
        # Show seed phrase for new wallets
        if mnemonic_words != "N/A (provided private key)":
            print("\nSeed Phrase (Keep Secret and Backup!):")
            print(mnemonic_words)
        
        # Separate SegWit and Legacy addresses
        segwit_addresses = []
        legacy_addresses = []
        
        for addr in derived_addresses:
            if addr[3].startswith(('tb1', 'bc1')):
                segwit_addresses.append(addr)
            elif addr[3].startswith(('m', 'n', '2', '1')):
                legacy_addresses.append(addr)
        
        # Display SegWit Addresses
        print("\n" + "=" * 50)
        print(f"{'SEGWIT ADDRESSES (Native bech32)':.^50}")
        print("=" * 50)
        
        # Create table header
        header = (f"{'Index':<6} {'Private Key (WIF)':<52} "
                f"{'Public Key (hex)':<66} {'Address':<35}")
        print(header)
        print("-" * 160)
        
        # Display SegWit address information
        for index, privkey, pubkey, address in segwit_addresses:
            line = f"{index:<6} {privkey:<52} {pubkey:<66} {address:<35}"
            print(line)
        
        # Display Legacy Addresses
        print("\n" + "=" * 50)
        print(f"{'LEGACY ADDRESSES (P2PKH)':.^50}")
        print("=" * 50)
        
        # Reuse the same header
        print(header)
        print("-" * 160)
        
        # Display Legacy address information
        for index, privkey, pubkey, address in legacy_addresses:
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
        Display balance information for all addresses with improved formatting.
        """
        try:
            from termcolor import colored
            use_color = True
        except ImportError:
            use_color = False

        # Separate addresses by type
        segwit_addresses = []
        legacy_addresses = []
        
        for index, privkey, pubkey, address in derived_addresses:
            balance_info = fetch_address_balance(address, network)
            
            # Determine address type
            if address.startswith(('tb1', 'bc1')):
                addr_type = 'SegWit'
            elif address.startswith(('m', 'n', '2', '1')) or address.startswith(('mk', 'mn', '2m', '2n')):
                addr_type = 'Legacy'
            else:
                addr_type = 'Unknown'
            
            # Prepare address details
            addr_details = {
                'index': index,
                'address': address,
                'type': addr_type,
                'balance_info': balance_info
            }
            
            # Sort into appropriate list
            if addr_type == 'SegWit':
                segwit_addresses.append(addr_details)
            elif addr_type == 'Legacy':
                legacy_addresses.append(addr_details)
        
        # Function to display address section
        def display_address_section(addresses, section_title):
            if not addresses:
                return
            
            # Print section header with color if available
            if use_color:
                print(colored(f"\n{section_title} Addresses:", 'blue', attrs=['bold']))
            else:
                print(f"\n{section_title} Addresses:")
            
            print("=" * 80)
            print(f"{'Index':<6} {'Address':<35} {'Confirmed (BTC)':<15} {'Pending (BTC)':<15} {'Transactions':<12}")
            print("-" * 80)
            
            for addr in addresses:
                balance_info = addr['balance_info']
                
                if balance_info["error"]:
                    balance_str = f"Error: {balance_info['error']}"
                    unconfirmed_str = "N/A"
                    tx_count_str = "N/A"
                else:
                    confirmed_balance = balance_info.get('confirmed_balance_btc', 0)
                    unconfirmed_balance = balance_info.get('unconfirmed_balance_btc', 0)
                    tx_count = balance_info.get('tx_count', 0)
                    unconf_count = balance_info.get('unconfirmed_tx_count', 0)
                    
                    # Color code balance if color is available
                    if use_color and confirmed_balance > 0:
                        balance_str = colored(f"{confirmed_balance:.8f}", 'green', attrs=['bold'])
                    else:
                        balance_str = f"{confirmed_balance:.8f}"
                    
                    unconfirmed_str = f"{unconfirmed_balance:.8f}"
                    tx_count_str = f"{tx_count} ({unconf_count} pending)"
                
                print(f"{addr['index']:<6} {addr['address']:<35} {balance_str:<15} {unconfirmed_str:<15} {tx_count_str:<12}")
            
            print("-" * 80)
        
        # Display both SegWit and Legacy address sections
        display_address_section(segwit_addresses, 'SegWit')
        display_address_section(legacy_addresses, 'Legacy')
    
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
    
    @staticmethod
    def show_payment_request(address: str, payment_uri: str, amount: Optional[float] = None, message: Optional[str] = None) -> None:
        """
        Display a formatted payment request with QR code.
        
        Args:
            address: Bitcoin address to receive payment
            payment_uri: Complete BIP21 payment URI
            amount: Optional payment amount in BTC
            message: Optional payment message/description
        """
        from .qrcode import generate_ascii_qr
        
        print("\nPayment Request Details:")
        print("=" * 50)
        
        # Show address
        print(f"\nReceiving Address: {address}")
        
        # Show amount if provided
        if amount is not None:
            print(f"Amount: {amount} BTC")
        
        # Show message if provided
        if message:
            print(f"Message: {message}")
        
        # Display the full payment URI
        print(f"\nPayment URI:\n{payment_uri}")
        
        # Generate and display QR code
        print("\nQR Code:")
        qr_code = generate_ascii_qr(payment_uri, "Payment Request", "address", compact=True)
        print(qr_code)