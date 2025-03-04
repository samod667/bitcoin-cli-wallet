from typing import List, Tuple, Optional, Dict
from art import text2art
from .qrcode import generate_ascii_qr
from .network import fetch_address_balance

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False
    try:
        from termcolor import colored
        HAS_TERMCOLOR = True
    except ImportError:
        HAS_TERMCOLOR = False

class WalletDisplay:
    """
    Handles the formatting and display of wallet information in the terminal.
    
    This class provides methods for displaying wallet information in a clear,
    organized manner. It handles different display modes (basic info, balances,
    QR codes) and ensures consistent formatting across the application.
    """
    
    @staticmethod
    def show_wallet_file_info(wallet_data: dict) -> None:
        """
        Display metadata about the loaded wallet file.
        """
        if HAS_RICH:
            WalletDisplay._show_wallet_file_info_rich(wallet_data)
        else:
            WalletDisplay._show_wallet_file_info_basic(wallet_data)

    @staticmethod
    def _show_wallet_file_info_rich(wallet_data: dict) -> None:
        """
        Display wallet file information using Rich formatting.
        """
        console.print(Panel(
            f"Wallet file loaded successfully",
            title="Wallet File Info",
            border_style="green"
        ))
        
        # Display network and version
        network = wallet_data.get('network', 'testnet')
        version = wallet_data.get('version', 'N/A')
        created_at = wallet_data.get('created_at', 'N/A')
        
        info_table = Table()
        info_table.add_column("Property", style="cyan")
        info_table.add_column("Value", style="yellow")
        
        info_table.add_row("Network", network.upper())
        info_table.add_row("Version", version)
        info_table.add_row("Created At", created_at)
        
        console.print(info_table)
        
        # Display metadata
        if 'metadata' in wallet_data:
            metadata = wallet_data['metadata']
            console.print(Panel(
                f"Total Addresses: {metadata.get('total_addresses', 'N/A')}\n"
                f"Address Types: {', '.join(metadata.get('address_types', ['Unknown']))}",
                title="Wallet Metadata",
                border_style="blue"
            ))
    
    @staticmethod
    def _show_wallet_info_basic(base_privkey: str, base_pubkey: str, 
                            mnemonic_words: str, derived_addresses: List[Tuple],
                            network: str, show_balance: bool = False, 
                            show_qr: bool = False, address_type: str = "segwit") -> None:
        """
        Original basic version of wallet info display.
        """
        # Display wallet header
        print("\n" + text2art("Bitcoin Wallet", font="small"))
        print(f"Network: {network.upper()}")
        
        # Show seed phrase for new wallets
        if mnemonic_words == "N/A (provided private key)":
            print("\nN/A (provided private key)")
        else:
            print("\nSeed Phrase (Keep Secret and Backup!):")
            print(mnemonic_words)
        
        # Filter addresses based on address_type
        segwit_addresses = []
        legacy_addresses = []
        
        for addr in derived_addresses:
            if addr[3].startswith(('tb1', 'bc1')):
                segwit_addresses.append(addr)
            elif addr[3].startswith(('m', 'n', '2', '1')):
                legacy_addresses.append(addr)
        
        # Display SegWit Addresses if requested
        if (address_type == "segwit" or address_type == "both") and segwit_addresses:
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
        
        # Display Legacy Addresses if requested
        if (address_type == "legacy" or address_type == "both") and legacy_addresses:
            print("\n" + "=" * 50)
            print(f"{'LEGACY ADDRESSES (P2PKH)':.^50}")
            print("=" * 50)
            
            # Reuse the same header
            header = (f"{'Index':<6} {'Private Key (WIF)':<52} "
                    f"{'Public Key (hex)':<66} {'Address':<35}")
            print(header)
            print("-" * 160)
            
            # Display Legacy address information
            for index, privkey, pubkey, address in legacy_addresses:
                line = f"{index:<6} {privkey:<52} {pubkey:<66} {address:<35}"
                print(line)
            
            print("-" * 160)
        
        # Show balance information if requested
        if show_balance:
            # Only pass addresses of the requested type
            if address_type == "both":
                addresses_to_check = derived_addresses
            elif address_type == "segwit":
                addresses_to_check = segwit_addresses
            else:  # legacy
                addresses_to_check = legacy_addresses
                
            WalletDisplay._show_balances(addresses_to_check, network)
        
        # Show QR codes if requested
        if show_qr:
            # Only show QR codes for addresses of the requested type
            if address_type == "both":
                addresses_for_qr = derived_addresses
            elif address_type == "segwit":
                addresses_for_qr = segwit_addresses
            else:  # legacy
                addresses_for_qr = legacy_addresses
                
            WalletDisplay._show_qr_codes(addresses_for_qr)

    @staticmethod
    def _show_wallet_info_rich(base_privkey: str, base_pubkey: str, 
                            mnemonic_words: str, derived_addresses: List[Tuple],
                            network: str, show_balance: bool = False, 
                            show_qr: bool = False, address_type: str = "segwit") -> None:
        """
        Rich version of wallet info display using the Rich library.
        """
        # Show seed phrase for new wallets
        if mnemonic_words == "N/A (provided private key)":
            console.print("\nN/A (provided private key)")
        else:
            console.print(Panel(
                f"[bold yellow]{mnemonic_words}[/bold yellow]",
                title="[red]Seed Phrase (Keep Secret and Backup!)[/red]",
                border_style="red"
            ))
        
        # Filter addresses based on address_type
        segwit_addresses = []
        legacy_addresses = []
        
        for addr in derived_addresses:
            if addr[3].startswith(('tb1', 'bc1')):
                segwit_addresses.append(addr)
            else:
                legacy_addresses.append(addr)
        
        # If we're showing balances, integrate them into the address display
        address_balances = {}
        
        if show_balance:
            # Only process addresses that match the requested type
            addresses_to_check = []
            if address_type == "both" or address_type == "segwit":
                addresses_to_check.extend(segwit_addresses)
            if address_type == "both" or address_type == "legacy":
                addresses_to_check.extend(legacy_addresses)
                
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True
            ) as progress:
                task = progress.add_task("[cyan]Fetching balances...", total=len(addresses_to_check))
                
                for index, _, _, address in addresses_to_check:
                    balance_info = fetch_address_balance(address, network)
                    address_balances[address] = balance_info
                    progress.update(task, advance=1)
        
        # Display SegWit Addresses if requested
        if (address_type == "segwit" or address_type == "both") and segwit_addresses:
            console.print("\n[bold]SEGWIT ADDRESSES (Native bech32)[/bold]")
            
            segwit_table = Table(show_header=True, header_style="bold")
            segwit_table.add_column("Index", style="cyan", no_wrap=True)
            segwit_table.add_column("Private Key (WIF)", style="red")
            segwit_table.add_column("Public Key (hex)", style="dim")
            segwit_table.add_column("Address", style="green")
            
            # Add balance columns if showing balances
            if show_balance:
                segwit_table.add_column("Confirmed (BTC)", justify="right", style="magenta")
                segwit_table.add_column("Pending (BTC)", justify="right", style="yellow")
                segwit_table.add_column("Transactions", justify="right")
            
            for index, privkey, pubkey, address in segwit_addresses:
                if show_balance:
                    balance_info = address_balances.get(address, {})
                    
                    if balance_info.get("error"):
                        confirmed_str = f"[red]Error[/red]"
                        pending_str = ""
                        tx_str = ""
                    else:
                        confirmed = balance_info.get('confirmed_balance_btc', 0)
                        unconfirmed = balance_info.get('unconfirmed_balance_btc', 0)
                        tx_count = balance_info.get('tx_count', 0)
                        unconf_count = balance_info.get('unconfirmed_tx_count', 0)
                        
                        confirmed_style = "green" if confirmed > 0 else "white"
                        unconfirmed_style = "yellow" if unconfirmed > 0 else "white"
                        
                        confirmed_str = f"[{confirmed_style}]{confirmed:.8f}[/{confirmed_style}]"
                        pending_str = f"[{unconfirmed_style}]{unconfirmed:.8f}[/{unconfirmed_style}]"
                        tx_str = f"{tx_count} ({unconf_count} pending)"
                    
                    segwit_table.add_row(
                        str(index), privkey, pubkey, address,
                        confirmed_str, pending_str, tx_str
                    )
                else:
                    segwit_table.add_row(str(index), privkey, pubkey, address)
            
            console.print(segwit_table)
        
        # Display Legacy Addresses if requested
        if (address_type == "legacy" or address_type == "both") and legacy_addresses:
            console.print("\n[bold]LEGACY ADDRESSES (P2PKH)[/bold]")
            
            legacy_table = Table(show_header=True, header_style="bold")
            legacy_table.add_column("Index", style="cyan", no_wrap=True)
            legacy_table.add_column("Private Key (WIF)", style="red")
            legacy_table.add_column("Public Key (hex)", style="dim")
            legacy_table.add_column("Address", style="yellow")
            
            # Add balance columns if showing balances
            if show_balance:
                legacy_table.add_column("Confirmed (BTC)", justify="right", style="magenta")
                legacy_table.add_column("Pending (BTC)", justify="right", style="yellow")
                legacy_table.add_column("Transactions", justify="right")
            
            for index, privkey, pubkey, address in legacy_addresses:
                if show_balance:
                    balance_info = address_balances.get(address, {})
                    
                    if balance_info.get("error"):
                        confirmed_str = f"[red]Error[/red]"
                        pending_str = ""
                        tx_str = ""
                    else:
                        confirmed = balance_info.get('confirmed_balance_btc', 0)
                        unconfirmed = balance_info.get('unconfirmed_balance_btc', 0)
                        tx_count = balance_info.get('tx_count', 0)
                        unconf_count = balance_info.get('unconfirmed_tx_count', 0)
                        
                        confirmed_style = "green" if confirmed > 0 else "white"
                        unconfirmed_style = "yellow" if unconfirmed > 0 else "white"
                        
                        confirmed_str = f"[{confirmed_style}]{confirmed:.8f}[/{confirmed_style}]"
                        pending_str = f"[{unconfirmed_style}]{unconfirmed:.8f}[/{unconfirmed_style}]"
                        tx_str = f"{tx_count} ({unconf_count} pending)"
                    
                    legacy_table.add_row(
                        str(index), privkey, pubkey, address,
                        confirmed_str, pending_str, tx_str
                    )
                else:
                    legacy_table.add_row(str(index), privkey, pubkey, address)
            
            console.print(legacy_table)
        
        # Display wallet balance summary if showing balances
        if show_balance and address_balances:
            # Calculate and display total balance
            total_confirmed = sum(
                balance.get('confirmed_balance_btc', 0) 
                for balance in address_balances.values() 
                if not balance.get('error')
            )
            total_unconfirmed = sum(
                balance.get('unconfirmed_balance_btc', 0) 
                for balance in address_balances.values() 
                if not balance.get('error')
            )
            
            console.print(Panel(
                f"Confirmed: [bold green]{total_confirmed:.8f} BTC[/bold green]\n"
                f"Pending: [bold yellow]{total_unconfirmed:.8f} BTC[/bold yellow]\n"
                f"Total: [bold blue]{total_confirmed + total_unconfirmed:.8f} BTC[/bold blue]",
                title="Wallet Balance Summary",
                border_style="green"
            ))
        
        # Show QR codes if requested
        if show_qr:
            # Only show QR codes for addresses of the requested type
            if address_type == "both":
                addresses_for_qr = derived_addresses
            elif address_type == "segwit":
                addresses_for_qr = segwit_addresses
            else:  # legacy
                addresses_for_qr = legacy_addresses
                
            WalletDisplay._show_qr_codes(addresses_for_qr)

    @staticmethod
    def _show_wallet_info_basic(base_privkey: str, base_pubkey: str, 
                            mnemonic_words: str, derived_addresses: List[Tuple],
                            network: str, show_balance: bool = False, 
                            show_qr: bool = False, address_type: str = "segwit") -> None:
        """
        Original basic version of wallet info display.
        """
        # Display wallet header
        print("\n" + text2art("Bitcoin Wallet", font="small"))
        print(f"Network: {network.upper()}")
        
        # Show seed phrase for new wallets
        if mnemonic_words == "N/A (provided private key)":
            print("\nN/A (provided private key)")
        else:
            print("\nSeed Phrase (Keep Secret and Backup!):")
            print(mnemonic_words)
        
        # Filter addresses based on address_type
        segwit_addresses = []
        legacy_addresses = []
        
        for addr in derived_addresses:
            if addr[3].startswith(('tb1', 'bc1')):
                segwit_addresses.append(addr)
            elif addr[3].startswith(('m', 'n', '2', '1')):
                legacy_addresses.append(addr)
        
        # Display SegWit Addresses if requested
        if (address_type == "segwit" or address_type == "both") and segwit_addresses:
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
        
        # Display Legacy Addresses if requested
        if (address_type == "legacy" or address_type == "both") and legacy_addresses:
            print("\n" + "=" * 50)
            print(f"{'LEGACY ADDRESSES (P2PKH)':.^50}")
            print("=" * 50)
            
            # Reuse the same header
            header = (f"{'Index':<6} {'Private Key (WIF)':<52} "
                    f"{'Public Key (hex)':<66} {'Address':<35}")
            print(header)
            print("-" * 160)
            
            # Display Legacy address information
            for index, privkey, pubkey, address in legacy_addresses:
                line = f"{index:<6} {privkey:<52} {pubkey:<66} {address:<35}"
                print(line)
            
            print("-" * 160)
        
        # Show balance information if requested
        if show_balance:
            # Only pass addresses of the requested type
            if address_type == "both":
                addresses_to_check = derived_addresses
            elif address_type == "segwit":
                addresses_to_check = segwit_addresses
            else:  # legacy
                addresses_to_check = legacy_addresses
                
            WalletDisplay._show_balances(addresses_to_check, network)
        
        # Show QR codes if requested
        if show_qr:
            # Only show QR codes for addresses of the requested type
            if address_type == "both":
                addresses_for_qr = derived_addresses
            elif address_type == "segwit":
                addresses_for_qr = segwit_addresses
            else:  # legacy
                addresses_for_qr = legacy_addresses
                
            WalletDisplay._show_qr_codes(addresses_for_qr)
    
    
    @staticmethod
    def show_wallet_info(base_privkey: str, base_pubkey: str, 
                        mnemonic_words: str, derived_addresses: List[Tuple],
                        network: str, show_balance: bool = False, 
                        show_qr: bool = False, address_type: str = "segwit",
                        command_name: str = None) -> None:
        """
        Display complete wallet information with improved formatting.
        
        Args:
            base_privkey: Base private key in WIF format
            base_pubkey: Base public key in hex format
            mnemonic_words: Mnemonic seed phrase
            derived_addresses: List of derived addresses (index, privkey, pubkey, address)
            network: Network type (mainnet, testnet, signet)
            show_balance: Whether to display balance information
            show_qr: Whether to display QR codes
            address_type: Type of addresses to display ("legacy", "segwit", or "both")
            command_name: Optional command name for title display
        """
        if HAS_RICH:
            # Display title with optional command name
            if command_name:
                WalletDisplay.display_title("Bitcoin Wallet", command_name=command_name, network=network)
            else:
                WalletDisplay.display_title("Bitcoin Wallet", network=network)
                
            # Show detailed wallet info
            WalletDisplay._show_wallet_info_rich(
                base_privkey, base_pubkey, mnemonic_words, 
                derived_addresses, network, show_balance, show_qr, address_type
            )
        else:
            WalletDisplay._show_wallet_info_basic(
                base_privkey, base_pubkey, mnemonic_words, 
                derived_addresses, network, show_balance, show_qr, address_type
            )
    
    @staticmethod
    def _show_balances(derived_addresses: List[Tuple], network: str) -> None:
        """
        Display balance information for all addresses with improved formatting.
        """
        if HAS_RICH:
            WalletDisplay._show_balances_rich(derived_addresses, network)
        else:
            WalletDisplay._show_balances_basic(derived_addresses, network)
    
    @staticmethod
    def _show_balances_rich(derived_addresses: List[Tuple], network: str) -> None:
        """
        Rich version of balance display.
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            task = progress.add_task("[cyan]Fetching balances...", total=len(derived_addresses))
            
            # Only process SegWit addresses now
            addresses_with_balances = []
            
            for index, privkey, pubkey, address in derived_addresses:
                balance_info = fetch_address_balance(address, network)
                
                addresses_with_balances.append({
                    'index': index,
                    'address': address,
                    'type': 'SegWit',
                    'balance_info': balance_info
                })
                
                progress.update(task, advance=1)
        
        # Create table for all addresses (now only SegWit)
        table = Table(title="SegWit Addresses")
        table.add_column("Index", style="cyan", no_wrap=True)
        table.add_column("Address", style="green")
        table.add_column("Confirmed (BTC)", justify="right", style="magenta")
        table.add_column("Pending (BTC)", justify="right", style="yellow")
        table.add_column("Transactions", justify="right")
        
        for addr in addresses_with_balances:
            balance_info = addr['balance_info']
            
            if balance_info.get("error"):
                table.add_row(
                    str(addr['index']),
                    addr['address'],
                    f"[red]Error: {balance_info['error']}[/red]",
                    "",
                    ""
                )
            else:
                # Format balances
                confirmed_balance = balance_info.get('confirmed_balance_btc', 0)
                unconfirmed_balance = balance_info.get('unconfirmed_balance_btc', 0)
                tx_count = balance_info.get('tx_count', 0)
                unconf_count = balance_info.get('unconfirmed_tx_count', 0)
                
                # Add color based on balance
                confirmed_style = "green" if confirmed_balance > 0 else "white"
                unconfirmed_style = "yellow" if unconfirmed_balance > 0 else "white"
                
                table.add_row(
                    str(addr['index']),
                    addr['address'],
                    f"[{confirmed_style}]{confirmed_balance:.8f}[/{confirmed_style}]",
                    f"[{unconfirmed_style}]{unconfirmed_balance:.8f}[/{unconfirmed_style}]",
                    f"{tx_count} ({unconf_count} pending)"
                )
        
        # Display the table with balances
        console.print(table)
        
        # Calculate and display total balance
        total_confirmed = sum(
            a['balance_info'].get('confirmed_balance_btc', 0) 
            for a in addresses_with_balances 
            if not a['balance_info'].get('error')
        )
        total_unconfirmed = sum(
            a['balance_info'].get('unconfirmed_balance_btc', 0) 
            for a in addresses_with_balances 
            if not a['balance_info'].get('error')
        )
        
        console.print(Panel(
            f"Confirmed: [bold green]{total_confirmed:.8f} BTC[/bold green]\n"
            f"Pending: [bold yellow]{total_unconfirmed:.8f} BTC[/bold yellow]\n"
            f"Total: [bold blue]{total_confirmed + total_unconfirmed:.8f} BTC[/bold blue]",
            title="Wallet Balance Summary",
            border_style="green"
        ))
    @staticmethod
    def _show_balances_basic(derived_addresses: List[Tuple], network: str) -> None:
        """
        Original basic version of balance display.
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
        if HAS_RICH:
            WalletDisplay._show_qr_codes_rich(derived_addresses)
        else:
            WalletDisplay._show_qr_codes_basic(derived_addresses)
    
    @staticmethod
    def _show_qr_codes_rich(derived_addresses: List[Tuple]) -> None:
        """
        Rich version of QR code display.
        """
        console.print("\n[bold]Address QR Codes:[/bold]")
        
        for index, _, _, address in derived_addresses:
            qr_code = generate_ascii_qr(address, f"Address {index}", "address", compact=True)
            
            console.print(Panel(
                qr_code,
                title=f"Address {index}",
                subtitle=address,
                border_style="blue",
                width=60
            ))
    
    @staticmethod
    def _show_qr_codes_basic(derived_addresses: List[Tuple]) -> None:
        """
        Original basic version of QR code display.
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
        if HAS_RICH:
            WalletDisplay._show_payment_request_rich(address, payment_uri, amount, message)
        else:
            WalletDisplay._show_payment_request_basic(address, payment_uri, amount, message)
    
    @staticmethod
    def _show_payment_request_rich(address: str, payment_uri: str, amount: Optional[float] = None, message: Optional[str] = None) -> None:
        """
        Rich version of payment request display.
        """
        qr_code = generate_ascii_qr(payment_uri, "Payment Request", "address", compact=True)
        
        content = []
        if amount is not None:
            content.append(f"Amount: [bold green]{amount} BTC[/bold green]")
        if message:
            content.append(f"Message: {message}")
        content.append(f"\nAddress: [bold cyan]{address}[/bold cyan]")
        content.append(f"\nPayment URI:\n[dim]{payment_uri}[/dim]")
        
        console.print(Panel(
            f"{qr_code}\n\n" + "\n".join(content),
            title="Payment Request",
            border_style="green",
            width=70
        ))
    
    @staticmethod
    def _show_payment_request_basic(address: str, payment_uri: str, amount: Optional[float] = None, message: Optional[str] = None) -> None:
        """
        Original basic version of payment request display.
        """
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
    
    @staticmethod
    def show_blockchain_info(blockchain_info: dict) -> None:
        """
        Display blockchain information in a clear, formatted manner.
        """
        if HAS_RICH:
            WalletDisplay._show_blockchain_info_rich(blockchain_info)
        else:
            WalletDisplay._show_blockchain_info_basic(blockchain_info)
    
    @staticmethod
    def _show_blockchain_info_rich(blockchain_info: dict) -> None:
        """
        Rich version of blockchain info display.
        """
        if "error" in blockchain_info:
            console.print(f"[bold red]Error retrieving blockchain info:[/bold red] {blockchain_info['error']}")
            return
        
        # Format block information
        content = [
            f"Block Height: [bold cyan]{blockchain_info.get('block_height', 'N/A')}[/bold cyan]",
            f"Current Block Hash: [dim]{blockchain_info.get('block_hash', 'N/A')}[/dim]"
        ]
        
        console.print(Panel(
            "\n".join(content),
            title="Blockchain Information",
            border_style="blue"
        ))
    
    @staticmethod
    def _show_blockchain_info_basic(blockchain_info: dict) -> None:
        """
        Original basic version of blockchain info display.
        """
        print("\n" + "=" * 50)
        print(f"{'BLOCKCHAIN INFORMATION':.^50}")
        print("=" * 50)
        
        if "error" in blockchain_info:
            print(f"Error retrieving blockchain info: {blockchain_info['error']}")
            return
        
        info_display = [
            ("Block Height", blockchain_info.get("block_height", "N/A")),
            ("Current Block Hash", blockchain_info.get("block_hash", "N/A"))
        ]
        
        for label, value in info_display:
            print(f"{label:<20}: {value}")
        
        print("=" * 50)

    @staticmethod
    def show_mempool_info(mempool_info: dict) -> None:
        """
        Display blockchain and network information in a clear, formatted manner.
        """
        if HAS_RICH:
            WalletDisplay._show_mempool_info_rich(mempool_info)
        else:
            WalletDisplay._show_mempool_info_basic(mempool_info)
    
    @staticmethod
    def _show_mempool_info_rich(mempool_info: dict) -> None:
        """
        Rich version of mempool info display.
        """
        if "error" in mempool_info:
            console.print(f"[bold red]Error retrieving network info:[/bold red] {mempool_info['error']}")
            
            if "details" in mempool_info:
                console.print(Panel(
                    "\n".join([f"{key}: {value}" for key, value in mempool_info.get("details", {}).items()]),
                    title="Error Details",
                    border_style="red"
                ))
            return
        
        # Format mempool information
        content = [
            f"Current Block Height: [bold cyan]{mempool_info.get('block_tip', 'N/A')}[/bold cyan]",
            f"Recent Blocks: {mempool_info.get('recent_blocks_count', 'N/A')}",
            f"Last Block Hash: [dim]{mempool_info.get('last_block_hash', 'N/A')}[/dim]",
            f"Fee Information: {mempool_info.get('fee_info', 'N/A')}"
        ]
        
        console.print(Panel(
            "\n".join(content),
            title="Network Information",
            border_style="blue"
        ))
    
    @staticmethod
    def _show_mempool_info_basic(mempool_info: dict) -> None:
        """
        Original basic version of mempool info display.
        """
        print("\n" + "=" * 50)
        print(f"{'NETWORK INFORMATION':.^50}")
        print("=" * 50)
        
        # Check for different error scenarios
        if "error" in mempool_info:
            print(f"Error retrieving network info: {mempool_info['error']}")
            
            # If additional details are available, print them
            if "details" in mempool_info:
                print("\nAdditional Details:")
                for key, value in mempool_info.get("details", {}).items():
                    print(f"{key}: {value}")
            
            return
        
        # Display network information
        info_display = [
            ("Current Block Height", mempool_info.get("block_tip", "N/A")),
            ("Recent Blocks", mempool_info.get("recent_blocks_count", "N/A")),
            ("Last Block Hash", mempool_info.get("last_block_hash", "N/A")),
            ("Fee Information", mempool_info.get("fee_info", "N/A"))
        ]
        
        for label, value in info_display:
            print(f"{label:<30}: {value}")
        
        print("=" * 50)
    
    @staticmethod
    def show_wallet_file_info(wallet_data: dict) -> None:
        """
        Display metadata about the loaded wallet file.
        """
        if HAS_RICH:
            WalletDisplay._show_wallet_file_info_rich(wallet_data)
        else:
            WalletDisplay._show_wallet_file_info_basic(wallet_data)
    
    @staticmethod
    def show_transaction_history(transactions: List[Dict], network: str) -> None:
        """
        Display transaction history with rich formatting.
        """
        if not transactions:
            print("No transactions found.")
            return
            
        if "error" in transactions[0]:
            print(f"Error: {transactions[0]['error']}")
            return
            
        if HAS_RICH:
            WalletDisplay._show_transaction_history_rich(transactions, network)
        else:
            WalletDisplay._show_transaction_history_basic(transactions, network)

    @staticmethod
    def _show_transaction_history_rich(transactions: List[Dict], network: str) -> None:
        """
        Rich version of transaction history display.
        """
        # Display enhanced title
        WalletDisplay.display_title("Bitcoin Wallet", command_name="Transaction History", network=network)
        
        table = Table(title="Recent Transactions")
        table.add_column("Date", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Amount (BTC)", justify="right")
        table.add_column("Fee (sat)", justify="right", style="dim")
        table.add_column("Status", style="yellow")
        table.add_column("Confirmations", justify="right")
        table.add_column("Transaction ID", style="blue")
            
        for tx in transactions:
            # Format amount with color based on transaction type
            amount = tx.get('amount_btc', 0)
            amount_style = "green" if tx.get('type') == 'received' else "red"
            amount_prefix = "" if tx.get('type') == 'received' else "-"
            amount_display = f"[{amount_style}]{amount_prefix}{abs(amount):.8f}[/{amount_style}]"
            
            # Format status with color
            status = tx.get('status', 'unknown')
            status_style = {
                'confirmed': 'green',
                'pending': 'yellow',
                'failed': 'red'
            }.get(status, 'white')
            
            # Format confirmations
            confirmations = tx.get('confirmations', 0)
            confirmations_display = str(confirmations) if confirmations else "Pending"
            
            # Format transaction ID (shortened)
            tx_id = tx.get('txid', '')
            short_tx_id = f"{tx_id[:8]}...{tx_id[-8:]}" if tx_id else "N/A"
            tx_id_display = f"[link={tx.get('explorer_url', '')}]{short_tx_id}[/link]"
            
            table.add_row(
                tx.get('date', 'Unknown'),
                tx.get('type', 'unknown').title(),
                amount_display,
                str(tx.get('fee_sat', 'N/A')),
                f"[{status_style}]{status.title()}[/{status_style}]",
                confirmations_display,
                tx_id_display
            )
        
        console.print(table)
        
        # Show summary statistics
        received = sum(tx.get('amount_btc', 0) for tx in transactions if tx.get('type') == 'received')
        sent = sum(abs(tx.get('amount_btc', 0)) for tx in transactions if tx.get('type') == 'sent')
        fees = sum(tx.get('fee_sat', 0) for tx in transactions) / 100_000_000  # Convert to BTC
        
        summary = Table.grid(padding=1)
        summary.add_column("Statistic")
        summary.add_column("Value")
        
        summary.add_row("Total Received:", f"[green]{received:.8f} BTC[/green]")
        summary.add_row("Total Sent:", f"[red]{sent:.8f} BTC[/red]")
        summary.add_row("Total Fees:", f"[yellow]{fees:.8f} BTC[/yellow]")
        summary.add_row("Net Amount:", f"[bold]{received - sent - fees:.8f} BTC[/bold]")
        
        console.print(Panel(summary, title="Transaction Summary", border_style="blue"))
        
    @staticmethod
    def _show_transaction_history_basic(transactions: List[Dict], network: str) -> None:
        """
        Basic version of transaction history display.
        """
        print("\nTransaction History:")
        print("=" * 100)
        print(f"{'Date':<16} {'Type':<10} {'Amount (BTC)':<16} {'Fee (sat)':<10} {'Status':<12} {'Confirmations':<14} {'Transaction ID':<20}")
        print("-" * 100)
        
        for tx in transactions:
            amount = tx.get('amount_btc', 0)
            amount_prefix = "" if tx.get('type') == 'received' else "-"
            amount_display = f"{amount_prefix}{abs(amount):.8f}"
            
            confirmations = tx.get('confirmations', 0)
            confirmations_display = str(confirmations) if confirmations else "Pending"
            
            tx_id = tx.get('txid', '')
            short_tx_id = f"{tx_id[:8]}...{tx_id[-8:]}" if tx_id else "N/A"
            
            print(f"{tx.get('date', 'Unknown'):<16} "
                f"{tx.get('type', 'unknown').title():<10} "
                f"{amount_display:<16} "
                f"{tx.get('fee_sat', 'N/A'):<10} "
                f"{tx.get('status', 'unknown').title():<12} "
                f"{confirmations_display:<14} "
                f"{short_tx_id:<20}")
        
        print("-" * 100)
        
        # Show summary statistics
        received = sum(tx.get('amount_btc', 0) for tx in transactions if tx.get('type') == 'received')
        sent = sum(abs(tx.get('amount_btc', 0)) for tx in transactions if tx.get('type') == 'sent')
        fees = sum(tx.get('fee_sat', 0) for tx in transactions) / 100_000_000  # Convert to BTC
        
        print("\nTransaction Summary:")
        print(f"Total Received: {received:.8f} BTC")
        print(f"Total Sent: {sent:.8f} BTC")
        print(f"Total Fees: {fees:.8f} BTC")
        print(f"Net Amount: {received - sent - fees:.8f} BTC")
        print("=" * 100)
    @staticmethod
    def show_exchange_rates(rates: Dict[str, float]) -> None:
        """
        Display current Bitcoin exchange rates.
        """
        if "error" in rates:
            print(f"Error: {rates['error']}")
            return
            
        if HAS_RICH:
            WalletDisplay._show_exchange_rates_rich(rates)
        else:
            WalletDisplay._show_exchange_rates_basic(rates)

    @staticmethod
    def _show_exchange_rates_rich(rates: Dict[str, float]) -> None:
        """
        Rich version of exchange rate display.
        """
        # Create a table for exchange rates
        table = Table(title="Bitcoin Exchange Rates")
        table.add_column("Currency", style="cyan")
        table.add_column("1 BTC =", style="green")
        table.add_column("1 Unit =", style="yellow")
        
        # Currency symbols for display
        symbols = {
            "usd": "$", 
            "eur": "€", 
            "gbp": "£",
            "jpy": "¥",
            "cad": "C$",
            "aud": "A$",
            "cny": "¥"
        }
        
        # Add rows for each currency
        for currency, rate in sorted(rates.items()):
            symbol = symbols.get(currency.lower(), "")
            inverse = 1 / rate if rate > 0 else 0
            
            table.add_row(
                currency.upper(),
                f"{symbol}{rate:,.2f}",
                f"{inverse:.8f} BTC"
            )
        
        console.print(table)
        console.print("[dim]Data provided by CoinGecko API[/dim]")

    @staticmethod
    def _show_exchange_rates_basic(rates: Dict[str, float]) -> None:
        """
        Basic version of exchange rate display.
        """
        print("\nBitcoin Exchange Rates:")
        print("=" * 50)
        print(f"{'Currency':<10} {'1 BTC =':<20} {'1 Unit =':<20}")
        print("-" * 50)
        
        # Currency symbols for display
        symbols = {
            "usd": "$", 
            "eur": "€", 
            "gbp": "£",
            "jpy": "¥",
            "cad": "C$",
            "aud": "A$",
            "cny": "¥"
        }
        
        # Add rows for each currency
        for currency, rate in sorted(rates.items()):
            symbol = symbols.get(currency.lower(), "")
            inverse = 1 / rate if rate > 0 else 0
            
            print(f"{currency.upper():<10} {symbol}{rate:,.2f}{'':.<20} {inverse:.8f} BTC")
        
        print("-" * 50)
        print("Data provided by CoinGecko API")
        
    @staticmethod
    def show_utxos(utxos: List[Dict], network: str) -> None:
        """
        Display UTXOs (unspent transaction outputs) for coin control.
        
        Args:
            utxos: List of UTXOs with details
            network: Network type
        """
        if not utxos:
            print("No UTXOs found for this address.")
            return
        
        if "error" in utxos[0]:
            print(f"Error: {utxos[0]['error']}")
            return
        
        if HAS_RICH:
            WalletDisplay._show_utxos_rich(utxos, network)
        else:
            WalletDisplay._show_utxos_basic(utxos, network)

    @staticmethod
    def _show_utxos_rich(utxos: List[Dict], network: str) -> None:
        """
        Rich version of UTXO display.
        """
        explorer_urls = {
            "mainnet": "https://blockstream.info",
            "testnet": "https://blockstream.info/testnet",
            "signet": "https://blockstream.info/signet"
        }
        
        table = Table(title="Unspent Transaction Outputs (UTXOs)")
        table.add_column("#", style="cyan", no_wrap=True)
        table.add_column("Amount (BTC)", justify="right", style="green")
        table.add_column("Confirmations", justify="right")
        table.add_column("Date", style="magenta")
        table.add_column("Transaction ID", style="blue")
        
        # Sort UTXOs by value (largest first) and confirmations (highest first)
        sorted_utxos = sorted(utxos, key=lambda u: (-u.get('value', 0), -u.get('confirmations', 0)))
        
        for i, utxo in enumerate(sorted_utxos):
            tx_id = utxo.get('txid', '')
            short_tx_id = f"{tx_id[:8]}...{tx_id[-8:]}" if tx_id else "N/A"
            explorer_url = f"{explorer_urls.get(network, explorer_urls['testnet'])}/tx/{tx_id}"
            tx_id_display = f"[link={explorer_url}]{short_tx_id}[/link]"
            
            # Format confirmations
            confirmations = utxo.get('confirmations', 0)
            if confirmations == 0:
                conf_display = "[yellow]Unconfirmed[/yellow]"
            else:
                conf_display = str(confirmations)
            
            table.add_row(
                str(i + 1),
                f"{utxo.get('value_btc', 0):.8f}",
                conf_display,
                utxo.get('date', 'Unknown'),
                tx_id_display
            )
        
        console.print(table)
        
        # Calculate total value
        total_value = sum(utxo.get('value_btc', 0) for utxo in utxos)
        
        console.print(f"Total Available: [bold green]{total_value:.8f} BTC[/bold green]")
        console.print("[dim]Note: UTXOs can be selected for spending using the coin control feature in interactive mode.[/dim]")

    @staticmethod
    def _show_utxos_basic(utxos: List[Dict], network: str) -> None:
        """
        Basic version of UTXO display.
        """
        print("\nUnspent Transaction Outputs (UTXOs):")
        print("=" * 100)
        print(f"{'#':<3} {'Amount (BTC)':<16} {'Confirmations':<14} {'Date':<18} {'Transaction ID':<65}")
        print("-" * 100)
        
        # Sort UTXOs by value (largest first) and confirmations (highest first)
        sorted_utxos = sorted(utxos, key=lambda u: (-u.get('value', 0), -u.get('confirmations', 0)))
        
        for i, utxo in enumerate(sorted_utxos):
            tx_id = utxo.get('txid', '')
            short_tx_id = f"{tx_id[:8]}...{tx_id[-8:]}" if tx_id else "N/A"
            
            # Format confirmations
            confirmations = utxo.get('confirmations', 0)
            if confirmations == 0:
                conf_display = "Unconfirmed"
            else:
                conf_display = str(confirmations)
            
            print(f"{i+1:<3} {utxo.get('value_btc', 0):<16.8f} {conf_display:<14} {utxo.get('date', 'Unknown'):<18} {tx_id}")
        
        print("-" * 100)
        
        # Calculate total value
        total_value = sum(utxo.get('value_btc', 0) for utxo in utxos)
        
        print(f"Total Available: {total_value:.8f} BTC")
        print("Note: UTXOs can be selected for spending using the coin control feature in interactive mode.")

    @staticmethod
    def display_title(title: str = "Bitcoin Wallet", subtitle: str = None, command_name: str = None, network: str = "testnet"):
        """
        Display an enhanced professional title for wallet commands.
        
        Args:
            title: Main title text
            subtitle: Optional subtitle
            command_name: Current command being executed
            network: Current network (mainnet, testnet, signet)
        """
        if HAS_RICH:
            from rich.console import Console
            from rich.panel import Panel
            from rich.align import Align
            from rich.text import Text
            
            # Create styled title with larger text effect
            title_text = Text(title.upper(), style="bold blue")
            
            # Create full content text object
            content_text = Text("⬢ ")
            content_text.append(title_text)
            content_text.append(" ⬢")
            
            # Add command info if provided
            if command_name:
                command_display = Text(f"\n{command_name} command", style="bold green")
                content_text.append(command_display)
            
            # Add version
            content_text.append(Text("\nv1.0.0", style="dim"))
            
            # Now wrap the complete text in an Align
            content = Align.center(content_text)
            
            # Create network indicator based on network type
            network_style = {
                "mainnet": "bold white on red",
                "testnet": "bold black on yellow",
                "signet": "bold white on blue"
            }.get(network.lower(), "bold black on yellow")
            
            network_display = f"[{network_style}] {network.upper()} [{network_style}]"
            
            # Create and display panel
            panel = Panel(
                content,
                border_style="blue",
                subtitle=subtitle or network_display,
                width=60,
                padding=(1, 15)
            )
            
            console.print("\n")
            console.print(panel)
            console.print("\n")
        else:
            # Fallback ASCII art version
            from art import text2art
            
            print("\n" + "=" * 60)
            print(text2art(title, font="small"))
            
            if command_name:
                print(f"Command: {command_name}")
            
            print(f"Network: {network.upper()}")
            print("=" * 60)
            print()