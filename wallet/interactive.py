import os
import sys
import json
from typing import List, Tuple, Optional, Dict, Any

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.styles import Style
    from rich.console import Console
    HAS_PROMPT_TOOLKIT = True
    console = Console()
except ImportError:
    HAS_PROMPT_TOOLKIT = False
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False

from .commands import (
    GenerateWalletCommand, CheckFeesCommand, BlockchainInfoCommand,
    MempoolInfoCommand, LoadWalletCommand, ReceiveCommand, SendCommand,
    ExchangeRatesCommand, TransactionHistoryCommand, WalletInfoCommand
)
from .cli import CommandArguments
from .display import WalletDisplay
from . import generate_wallet

class InteractiveWallet:
    """
    Interactive mode for Bitcoin wallet CLI.
    
    This class provides a REPL (Read-Eval-Print-Loop) interface for
    interacting with the wallet through commands and subcommands.
    """
    
    def __init__(self, network: str = "testnet"):
        self.network = network
        self.privkey = None
        self.addresses = None
        self.address_type = "segwit"
        self.current_wallet_file = None
        self.session = None
        self.completer = None
        
        # Set up history file
        history_dir = os.path.expanduser("~/.bitcoin_wallet")
        os.makedirs(history_dir, exist_ok=True)
        history_file = os.path.join(history_dir, "command_history")
        
        if HAS_PROMPT_TOOLKIT:
            style = Style.from_dict({
                'prompt': '#00aa00 bold',
            })
            
            self.completer = WordCompleter([
                'create', 'balance', 'send', 'receive', 'history',
                'fees', 'rates', 'blockchain', 'mempool', 'load', 
                'use', 'unload', 'wallet',  # Added new commands
                'help', 'exit', 'quit', 'clear'
            ])
            
            self.session = PromptSession(
                history=FileHistory(history_file),
                auto_suggest=AutoSuggestFromHistory(),
                completer=self.completer,
                style=style
            )
    
    def run(self) -> None:
        """
        Start the interactive wallet interface.
        """
        self._print_welcome()
        
        while True:
            try:
                if HAS_PROMPT_TOOLKIT and self.session:
                    command = self.session.prompt('wallet> ', completer=self.completer)
                else:
                    command = input('wallet> ')
                
                command = command.strip()
                if not command:
                    continue
                
                if command in ('quit', 'exit'):
                    print("Exiting wallet. Goodbye!")
                    break
                elif command == 'clear':
                    os.system('cls' if os.name == 'nt' else 'clear')
                    continue
                
                self._process_command(command)
                
            except KeyboardInterrupt:
                print("\nPress Ctrl+D or type 'exit' to exit.")
            except EOFError:
                print("\nExiting wallet. Goodbye!")
                break
            except Exception as e:
                print(f"Error: {str(e)}")
    
    def _process_command(self, command_line: str) -> None:
        """
        Process a command entered by the user.
        
        Args:
            command_line: Full command line entered by the user
        """
        # Split into command and arguments
        parts = command_line.split()
        if not parts:
            return
        
        command = parts[0].lower()
        args = parts[1:]
        
        # Process based on command
        if command == 'help':
            self._show_help(args[0] if args else None)
        elif command == 'create':
            self._create_wallet(args)
        elif command == 'load':
            self._load_wallet(args)
        elif command == 'use':
            self._use_wallet(args)  # New command
        elif command == 'unload':
            self._unload_wallet()   # New command
        elif command == 'wallet':
            self._show_wallet_info()  # New command
        elif command == 'balance':
            self._check_balance()
        elif command == 'receive':
            self._receive_payment(args)
        elif command == 'send':
            self._send_payment(args)
        elif command == 'history':
            self._show_history(args)
        elif command == 'fees':
            self._check_fees()
        elif command == 'rates':
            self._show_rates()
        elif command == 'blockchain':
            self._show_blockchain_info()
        elif command == 'mempool':
            self._show_mempool_info()
        else:
            print(f"Unknown command: '{command}'. Type 'help' for available commands.")

    # [Existing methods remain unchanged]
    
    def _use_wallet(self, args: List[str]) -> None:
        """Load a wallet for subsequent commands."""
        if not args:
            print("Please specify a private key or a wallet file.")
            print("Usage: use PRIVATE_KEY")
            print("   or: use --file WALLET_FILE")
            return
        
        # Check if loading from file
        if args[0] == '--file' and len(args) > 1:
            wallet_file = args[1]
            from .wallet_manager import wallet_manager
            
            success = wallet_manager.load_wallet_from_file(wallet_file)
            if success:
                active_wallet = wallet_manager.get_active_wallet()
                self.network = active_wallet.get('network', 'testnet')
                self.address_type = active_wallet.get('address_type', 'segwit')
                self.privkey = active_wallet.get('private_key')
                
                # Regenerate wallet data
                result = generate_wallet(self.privkey, self.network)
                if None not in result[:3]:
                    _, _, _, self.addresses = result
                    
                print(f"Wallet loaded from {wallet_file} and will be used for subsequent commands.")
                self._show_wallet_info()
        else:
            # Assume first argument is private key
            privkey = args[0]
            
            # Process optional arguments
            i = 1
            network = self.network
            address_type = self.address_type
            
            while i < len(args):
                if args[i] == '--network' and i + 1 < len(args):
                    if args[i + 1] in ('mainnet', 'testnet', 'signet'):
                        network = args[i + 1]
                    i += 2
                elif args[i] == '--type' and i + 1 < len(args):
                    if args[i + 1] in ('segwit', 'legacy', 'both'):
                        address_type = args[i + 1]
                    i += 2
                else:
                    i += 1
            
            # Generate wallet
            result = generate_wallet(privkey, network)
            
            if None in result[:3]:
                error_message = result[3]
                print(error_message)
                return
                
            self.privkey, pubkey, mnemonic, self.addresses = result
            self.network = network
            self.address_type = address_type
            
            # Store in wallet manager
            from .wallet_manager import wallet_manager
            
            success = wallet_manager.load_wallet(
                privkey=self.privkey,
                network=self.network,
                address_type=self.address_type,
                addresses=self.addresses,
                pubkey=pubkey
            )
            
            if success:
                print(f"Wallet loaded successfully and will be used for subsequent commands.")
                self._show_wallet_info()

    def _unload_wallet(self) -> None:
        """Unload the currently active wallet."""
        from .wallet_manager import wallet_manager
        
        success = wallet_manager.unload_wallet()
        
        if success:
            # Clear local wallet data as well
            self.privkey = None
            self.addresses = None
            print("Wallet unloaded. No wallet is currently active.")
        else:
            print("No wallet was loaded.")

    def _show_wallet_info(self) -> None:
        """Display information about the current wallet."""
        from .wallet_manager import wallet_manager
        
        # First check if we have a local wallet in the interactive session
        if self.privkey and self.addresses:
            print("Using wallet from interactive session:")
            
            # Create command arguments
            args = CommandArguments(
                network=self.network,
                output=None,
                check_balance=True,
                show_qr=False,
                address_type=self.address_type,
                privkey=self.privkey,
                receive=False,
                new_address=False,
                amount=None,
                message=None,
                send=None,
                fee_priority='medium',
                privacy=False,
                check_fees=False,
                blockchain_info=False,
                mempool_info=False,
                load=None,
                history=False,
                limit=10,
                rates=False,
                interactive=True,
                use_wallet=None,
                use_wallet_file=None,
                unload_wallet=False,
                wallet_info=True,
                utxos=False
            )
            
            # Execute wallet info command
            cmd = WalletInfoCommand(args)
            cmd.execute()
            return
            
        # Check the wallet manager
        active_wallet = wallet_manager.get_active_wallet()
        
        if not active_wallet:
            print("No wallet is currently active.")
            print("Use 'use PRIVATE_KEY' or 'load WALLET_FILE' to activate a wallet.")
            return
        
        # Create command arguments
        args = CommandArguments(
            network=active_wallet.get('network', 'testnet'),
            output=None,
            check_balance=True,
            show_qr=False,
            address_type=active_wallet.get('address_type', 'segwit'),
            privkey=active_wallet.get('private_key'),
            receive=False,
            new_address=False,
            amount=None,
            message=None,
            send=None,
            fee_priority='medium',
            privacy=False,
            check_fees=False,
            blockchain_info=False,
            mempool_info=False,
            load=None,
            history=False,
            limit=10,
            rates=False,
            interactive=True,
            use_wallet=None,
            use_wallet_file=None,
            unload_wallet=False,
            wallet_info=True,
            utxos=False
        )
        
        # Execute wallet info command
        cmd = WalletInfoCommand(args)
        cmd.execute()
    
    # [Original methods remain unchanged]

    def _create_wallet(self, args: List[str]) -> None:
        """Create a new wallet or import from private key."""
        privkey = None
        output_file = None
        
        # Process arguments
        i = 0
        while i < len(args):
            if args[i] == '--privkey' and i + 1 < len(args):
                privkey = args[i + 1]
                i += 2
            elif args[i] == '--output' and i + 1 < len(args):
                output_file = args[i + 1]
                i += 2
            elif args[i] == '--type' and i + 1 < len(args):
                # Keep this for backward compatibility but ignore the value
                i += 2
            elif args[i] == '--network' and i + 1 < len(args):
                if args[i + 1] in ('mainnet', 'testnet', 'signet'):
                    self.network = args[i + 1]
                i += 2
            else:
                i += 1
        
        try:
            # Generate wallet - note we don't pass address_type anymore
            result = generate_wallet(privkey, self.network)
            
            if None in result[:3]:
                error_message = result[3]
                print(error_message)
                return
            
            # Store wallet information
            self.privkey, pubkey, mnemonic, self.addresses = result
            
            # Create command arguments for display
            args = CommandArguments(
                network=self.network,
                output=output_file,
                check_balance=False,
                show_qr=False,
                address_type=self.address_type,
                privkey=self.privkey,
                receive=False,
                new_address=False,
                amount=None,
                message=None,
                send=None,
                fee_priority='medium',
                privacy=False,
                check_fees=False,
                blockchain_info=False,
                mempool_info=False,
                load=None,
                history=False,
                limit=10,
                rates=False,
                interactive=True,
                use_wallet=None,
                use_wallet_file=None,
                unload_wallet=False,
                wallet_info=False,
                utxos=False
            )
            
            # Execute display command
            cmd = GenerateWalletCommand(args)
            cmd.execute()
            
            # Save to file if requested
            if output_file:
                self.current_wallet_file = output_file
                print(f"Wallet saved to {output_file}")
            
        except Exception as e:
            print(f"Failed to create wallet: {str(e)}")
    
    def _load_wallet(self, args: List[str]) -> None:
        """Load wallet from file."""
        if not args:
            print("Please specify a wallet file to load.")
            return
        
        wallet_file = args[0]
        
        try:
            # Load wallet from JSON file
            with open(wallet_file, 'r') as f:
                wallet_data = json.load(f)
            
            # Display wallet information
            WalletDisplay.show_wallet_file_info(wallet_data)
            
            # Extract necessary information
            self.privkey = wallet_data.get('private_key')
            self.network = wallet_data.get('network', 'testnet')
            
            if not self.privkey:
                print("Error: No private key found in the wallet file.")
                return
            
            # Regenerate wallet using the private key
            result = generate_wallet(self.privkey, self.network)
            
            # Store wallet information
            self.privkey, pubkey, mnemonic, self.addresses = result
            self.current_wallet_file = wallet_file
            
            # Create command arguments for display
            args = CommandArguments(
                network=self.network,
                output=None,
                check_balance=True,  # Check balance when loading
                show_qr=False,
                address_type=self.address_type,
                privkey=self.privkey,
                receive=False,
                new_address=False,
                amount=None,
                message=None,
                send=None,
                fee_priority='medium',
                privacy=False,
                check_fees=False,
                blockchain_info=False,
                mempool_info=False,
                load=wallet_file,
                history=False,
                limit=10,
                rates=False,
                interactive=True,
                use_wallet=None,
                use_wallet_file=None,
                unload_wallet=False,
                wallet_info=False,
                utxos=False
            )
            
            # Execute display command
            cmd = GenerateWalletCommand(args)
            cmd.execute()
            
        except FileNotFoundError:
            print(f"Error: Wallet file '{wallet_file}' not found.")
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in wallet file '{wallet_file}'.")
        except Exception as e:
            print(f"Failed to load wallet: {str(e)}")
    
    def _check_balance(self) -> None:
        """Check balance of wallet addresses."""
        if not self.addresses:
            print("No wallet loaded. Use 'create' or 'load' first.")
            return
        
        # Create command arguments
        args = CommandArguments(
            network=self.network,
            output=None,
            check_balance=True,
            show_qr=False,
            address_type=self.address_type,
            privkey=self.privkey,
            receive=False,
            new_address=False,
            amount=None,
            message=None,
            send=None,
            fee_priority='medium',
            privacy=False,
            check_fees=False,
            blockchain_info=False,
            mempool_info=False,
            load=None,
            history=False,
            limit=10,
            rates=False,
            interactive=True,
            use_wallet=None,
            use_wallet_file=None,
            unload_wallet=False,
            wallet_info=False,
            utxos=False
        )
        
        # Execute command
        cmd = GenerateWalletCommand(args)
        cmd.execute()
    
    def _receive_payment(self, args: List[str]) -> None:
        """Generate a payment request."""
        if not self.addresses:
            print("No wallet loaded. Use 'create' or 'load' first.")
            return
        
        amount = None
        message = None
        new_address = False
        
        # Process arguments
        i = 0
        while i < len(args):
            if args[i] == '--amount' and i + 1 < len(args):
                try:
                    amount = float(args[i + 1])
                except ValueError:
                    print(f"Invalid amount: {args[i + 1]}")
                    return
                i += 2
            elif args[i] == '--message' and i + 1 < len(args):
                message = args[i + 1]
                i += 2
            elif args[i] == '--new':
                new_address = True
                i += 1
            else:
                i += 1
        
        # Create command arguments
        args = CommandArguments(
            network=self.network,
            output=None,
            check_balance=False,
            show_qr=True,
            address_type=self.address_type,
            privkey=self.privkey,
            receive=True,
            new_address=new_address,
            amount=amount,
            message=message,
            send=None,
            fee_priority='medium',
            privacy=False,
            check_fees=False,
            blockchain_info=False,
            mempool_info=False,
            load=None,
            history=False,
            limit=10,
            rates=False,
            interactive=True,
            use_wallet=None,
            use_wallet_file=None,
            unload_wallet=False,
            wallet_info=False,
            utxos=False
        )
        
        # Execute command
        cmd = ReceiveCommand(args, self.addresses)
        cmd.execute()
    
    def _print_welcome(self) -> None:
        """Print welcome message and basic help."""
        from .display import WalletDisplay
        
        # Display enhanced title
        WalletDisplay.display_title(
            "Bitcoin Wallet CLI", 
            "Interactive Mode", 
            network=self.network
        )
        
        if HAS_RICH:
            console.print("Type [bold green]help[/bold green] to see available commands.")
            console.print("Type [bold green]exit[/bold green] to quit.\n")
        else:
            print("Type 'help' to see available commands.")
            print("Type 'exit' to quit.\n")

    def _send_payment(self, args: List[str]) -> None:
        """Send a payment."""
        from .wallet_manager import wallet_manager
        import bitcoin
        from bitcoin.core import CMutableTransaction, CMutableTxIn, CMutableTxOut, COutPoint, CTxWitness, CTxInWitness
        from bitcoin.core.script import CScript, SignatureHash, SIGHASH_ALL, OP_0, SIGVERSION_WITNESS_V0
        from bitcoin.wallet import CBitcoinSecret
        from bitcoin.core import Hash160
        from .network import fetch_utxos, get_recommended_fee_rate
        import requests
        
        # Check local wallet first, then wallet manager
        if not self.addresses:
            active_wallet = wallet_manager.get_active_wallet()
            if active_wallet:
                # Use wallet from manager
                self.privkey = active_wallet.get('private_key')
                self.network = active_wallet.get('network', 'testnet')
                self.address_type = active_wallet.get('address_type', 'segwit')
                
                # Generate addresses
                result = generate_wallet(self.privkey, self.network)
                if None not in result[:3]:
                    _, _, _, self.addresses = result
                else:
                    print("Failed to load wallet from manager.")
                    return
            else:
                print("No wallet loaded. Use 'create', 'load', or 'use' first.")
                return
        
        to_address = None
        amount = None
        fee_priority = 'medium'
        privacy = False
        
        # Process arguments
        i = 0
        while i < len(args):
            if args[i] == '--to' and i + 1 < len(args):
                to_address = args[i + 1]
                i += 2
            elif args[i] == '--amount' and i + 1 < len(args):
                try:
                    amount = float(args[i + 1])
                except ValueError:
                    print(f"Invalid amount: {args[i + 1]}")
                    return
                i += 2
            elif args[i] == '--fee' and i + 1 < len(args):
                if args[i + 1] in ('high', 'medium', 'low'):
                    fee_priority = args[i + 1]
                i += 2
            elif args[i] == '--privacy':
                privacy = True
                i += 1
            else:
                i += 1
        
        if not to_address:
            print("Please specify a recipient address with --to.")
            return
        
        if amount is None:
            print("Please specify an amount with --amount.")
            return

        try:
            # Show fee rates
            fee_rates = get_recommended_fee_rate(self.network)
            print("\nCurrent Fee Rates (satoshis/vB):")
            print(f"High Priority: {fee_rates['high']} sat/vB")
            print(f"Medium Priority: {fee_rates['medium']} sat/vB")
            print(f"Low Priority: {fee_rates['low']} sat/vB")
            print(f"\nUsing {fee_priority} priority: {fee_rates[fee_priority]} sat/vB")
            
            # Set network
            if self.network == "mainnet":
                bitcoin.SelectParams("mainnet")
            else:
                bitcoin.SelectParams("testnet")
            
            # Get sender address
            from_address = self.addresses[0][3]
            
            print(f"\nPreparing to send {amount} BTC")
            print(f"From: {from_address}")
            print(f"To: {to_address}")
            
            # For testing/debugging, create a transaction command to use CLI instead
            args = CommandArguments(
                network=self.network,
                output=None,
                check_balance=False,
                show_qr=False,
                address_type=self.address_type,
                privkey=self.privkey,
                receive=False,
                new_address=False,
                amount=amount,
                message=None,
                send=to_address,
                fee_priority=fee_priority,
                privacy=privacy,
                check_fees=False,
                blockchain_info=False,
                mempool_info=False,
                load=None,
                history=False,
                limit=10,
                rates=False,
                interactive=True,
                use_wallet=None,
                use_wallet_file=None,
                unload_wallet=False,
                wallet_info=False,
                utxos=False,
                address=None,
                help=False,
                help_command=None
            )
            
            # Execute using the existing command implementation
            cmd = SendCommand(args, self.addresses)
            cmd.execute()
            
        except Exception as e:
            print(f"Failed to send transaction: {str(e)}")

    def _show_history(self, args: List[str]) -> None:
        """Show transaction history."""
        from .wallet_manager import wallet_manager
        
        # Check local wallet first, then wallet manager
        if not self.addresses:
            active_wallet = wallet_manager.get_active_wallet()
            if active_wallet:
                # Use wallet from manager
                self.privkey = active_wallet.get('private_key')
                self.network = active_wallet.get('network', 'testnet')
                self.address_type = active_wallet.get('address_type', 'segwit')
                
                # Generate addresses
                result = generate_wallet(self.privkey, self.network)
                if None not in result[:3]:
                    _, _, _, self.addresses = result
                else:
                    print("Failed to load wallet from manager.")
                    return
            else:
                print("No wallet loaded. Use 'create', 'load', or 'use' first.")
                return
        
        limit = 10
        
        # Process arguments
        if args and args[0].isdigit():
            limit = int(args[0])
        
        # Create command arguments
        args = CommandArguments(
            network=self.network,
            output=None,
            check_balance=False,
            show_qr=False,
            address_type=self.address_type,
            privkey=self.privkey,
            receive=False,
            new_address=False,
            amount=None,
            message=None,
            send=None,
            fee_priority='medium',
            privacy=False,
            check_fees=False,
            blockchain_info=False,
            mempool_info=False,
            load=None,
            history=True,
            limit=limit,
            rates=False,
            interactive=True,
            use_wallet=None,
            use_wallet_file=None,
            unload_wallet=False,
            wallet_info=False,
            utxos=False
        )
        
        # Execute command
        cmd = TransactionHistoryCommand(args, self.addresses)
        cmd.execute()

    def _check_fees(self) -> None:
        """Check current recommended fees."""
        # For fee checking, we don't need an active wallet, but we use network from active wallet if available
        from .wallet_manager import wallet_manager
        
        network = self.network
        active_wallet = wallet_manager.get_active_wallet()
        if active_wallet:
            network = active_wallet.get('network', network)
        
        # Create command arguments
        args = CommandArguments(
            network=network,
            output=None,
            check_balance=False,
            show_qr=False,
            address_type=self.address_type,
            privkey=self.privkey if hasattr(self, 'privkey') else None,
            receive=False,
            new_address=False,
            amount=None,
            message=None,
            send=None,
            fee_priority='medium',
            privacy=False,
            check_fees=True,
            blockchain_info=False,
            mempool_info=False,
            load=None,
            history=False,
            limit=10,
            rates=False,
            interactive=True,
            use_wallet=None,
            use_wallet_file=None,
            unload_wallet=False,
            wallet_info=False,
            utxos=False
        )
        
        # Execute command
        cmd = CheckFeesCommand(args)
        cmd.execute()

    def _show_rates(self) -> None:
        """Show current exchange rates."""
        # Network doesn't matter for exchange rates, but we'll use the active wallet's network for consistency
        from .wallet_manager import wallet_manager
        from .display import WalletDisplay
        
        network = self.network
        active_wallet = wallet_manager.get_active_wallet()
        if active_wallet:
            network = active_wallet.get('network', network)
        
        # Display title
        WalletDisplay.display_title("Bitcoin Wallet CLI", command_name="Exchange Rates", network=network)
        
        # Create command arguments
        args = CommandArguments(
            network=network,
            output=None,
            check_balance=False,
            show_qr=False,
            address_type=self.address_type,
            privkey=self.privkey if hasattr(self, 'privkey') else None,
            receive=False,
            new_address=False,
            amount=None,
            message=None,
            send=None,
            fee_priority='medium',
            privacy=False,
            check_fees=False,
            blockchain_info=False,
            mempool_info=False,
            load=None,
            history=False,
            limit=10,
            rates=True,
            interactive=True,
            use_wallet=None,
            use_wallet_file=None,
            unload_wallet=False,
            wallet_info=False,
            utxos=False
        )
        
        # Execute command
        cmd = ExchangeRatesCommand(args)
        cmd.execute()

    def _show_blockchain_info(self) -> None:
        """Show current blockchain information."""
        # For blockchain info, use network from active wallet if available
        from .wallet_manager import wallet_manager
        from .display import WalletDisplay
        
        network = self.network
        active_wallet = wallet_manager.get_active_wallet()
        if active_wallet:
            network = active_wallet.get('network', network)
        
        # Display title
        WalletDisplay.display_title("Bitcoin Wallet CLI", command_name="Blockchain Info", network=network)
        
        # Create command arguments
        args = CommandArguments(
            network=network,
            output=None,
            check_balance=False,
            show_qr=False,
            address_type=self.address_type,
            privkey=self.privkey if hasattr(self, 'privkey') else None,
            receive=False,
            new_address=False,
            amount=None,
            message=None,
            send=None,
            fee_priority='medium',
            privacy=False,
            check_fees=False,
            blockchain_info=True,
            mempool_info=False,
            load=None,
            history=False,
            limit=10,
            rates=False,
            interactive=True,
            use_wallet=None,
            use_wallet_file=None,
            unload_wallet=False,
            wallet_info=False,
            utxos=False
        )
        
        # Execute command
        cmd = BlockchainInfoCommand(args)
        cmd.execute()

    def _show_mempool_info(self) -> None:
        """Show current mempool information."""
        # For mempool info, use network from active wallet if available
        from .wallet_manager import wallet_manager
        from .display import WalletDisplay
        
        network = self.network
        active_wallet = wallet_manager.get_active_wallet()
        if active_wallet:
            network = active_wallet.get('network', network)
        
        # Display title
        WalletDisplay.display_title("Bitcoin Wallet CLI", command_name="Mempool Info", network=network)
        
        # Create command arguments
        args = CommandArguments(
            network=network,
            output=None,
            check_balance=False,
            show_qr=False,
            address_type=self.address_type,
            privkey=self.privkey if hasattr(self, 'privkey') else None,
            receive=False,
            new_address=False,
            amount=None,
            message=None,
            send=None,
            fee_priority='medium',
            privacy=False,
            check_fees=False,
            blockchain_info=False,
            mempool_info=True,
            load=None,
            history=False,
            limit=10,
            rates=False,
            interactive=True,
            use_wallet=None,
            use_wallet_file=None,
            unload_wallet=False,
            wallet_info=False,
            utxos=False
        )
        
        # Execute command
        cmd = MempoolInfoCommand(args)
        cmd.execute()

    def _show_help(self, command: Optional[str] = None) -> None:
        """
        Show help information for commands.
        
        Args:
            command: Optional specific command to show help for
        """
        if HAS_RICH:
            from rich.table import Table
            
            if command:
                self._show_command_help_rich(command)
            else:
                # General help
                table = Table(title="Bitcoin Wallet CLI Commands")
                table.add_column("Command", style="cyan")
                table.add_column("Description", style="green")
                table.add_column("Usage", style="yellow")
                
                commands = [
                    ("create", "Create a new wallet or import from private key", "create [--privkey KEY] [--output FILE] [--type TYPE] [--network NETWORK]"),
                    ("load", "Load wallet from file", "load WALLET_FILE"),
                    ("use", "Load/use wallet for subsequent commands", "use PRIVATE_KEY or use --file WALLET_FILE"),
                    ("wallet", "Show information about active wallet", "wallet"),
                    ("unload", "Unload the currently active wallet", "unload"),
                    ("balance", "Check wallet balance", "balance"),
                    ("receive", "Generate payment request", "receive [--amount AMOUNT] [--message MESSAGE] [--new]"),
                    ("send", "Send payment", "send --to ADDRESS --amount AMOUNT [--fee PRIORITY] [--privacy]"),
                    ("history", "Show transaction history", "history [LIMIT]"),
                    ("fees", "Check current fees", "fees"),
                    ("rates", "Show exchange rates", "rates"),
                    ("blockchain", "Show blockchain info", "blockchain"),
                    ("mempool", "Show mempool info", "mempool"),
                    ("help", "Show help information", "help [COMMAND]"),
                    ("clear", "Clear the screen", "clear"),
                    ("exit", "Exit the wallet", "exit")
                ]
                
                for cmd, desc, usage in commands:
                    table.add_row(cmd, desc, usage)
                
                console.print(table)
                console.print("\nFor detailed help on a specific command, type 'help COMMAND'")
        else:
            if command:
                self._show_command_help_basic(command)
            else:
                print("\nBitcoin Wallet CLI Commands:")
                print("=" * 80)
                print("create    - Create a new wallet or import from private key")
                print("load      - Load wallet from file")
                print("use       - Load/use wallet for subsequent commands")
                print("wallet    - Show information about active wallet")
                print("unload    - Unload the currently active wallet")
                print("balance   - Check wallet balance")
                print("receive   - Generate payment request")
                print("send      - Send payment")
                print("history   - Show transaction history")
                print("fees      - Check current fees")
                print("rates     - Show exchange rates")
                print("blockchain - Show blockchain info")
                print("mempool   - Show mempool info")
                print("help      - Show help information")
                print("clear     - Clear the screen")
                print("exit      - Exit the wallet")
                print("=" * 80)
                print("\nFor detailed help on a specific command, type 'help COMMAND'")

    def _show_command_help_rich(self, command: str) -> None:
        """
        Show detailed help for a specific command with rich formatting.
        
        Args:
            command: Command to show help for
        """
        from rich.panel import Panel
        from rich.table import Table
        
        help_text = ""
        examples = []
        options = []
        
        if command == "create":
            help_text = "Create a new wallet or import from an existing private key."
            options = [
                ("--privkey KEY", "Use an existing private key in WIF format"),
                ("--output FILE", "Save wallet information to a JSON file"),
                ("--type TYPE", "Type of address to generate (segwit, legacy, both)"),
                ("--network NETWORK", "Bitcoin network to use (mainnet, testnet, signet)")
            ]
            examples = [
                "create",
                "create --type legacy",
                "create --privkey cPCAMF3uPQJQfMvsqfzXTcH7Gm9buiYQZb3gaxjD5PZkCyFF3ADL --output my_wallet.json"
            ]
        elif command == "load":
            help_text = "Load wallet from a JSON file."
            options = [
                ("WALLET_FILE", "Path to the wallet JSON file")
            ]
            examples = [
                "load my_wallet.json"
            ]
        elif command == "use":
            help_text = "Load/use a wallet for subsequent commands without having to specify the private key each time."
            options = [
                ("PRIVATE_KEY", "Private key in WIF format to use"),
                ("--file WALLET_FILE", "Load wallet from a JSON file"),
                ("--type TYPE", "Type of address to generate (segwit, legacy, both)"),
                ("--network NETWORK", "Bitcoin network to use (mainnet, testnet, signet)")
            ]
            examples = [
                "use cPCAMF3uPQJQfMvsqfzXTcH7Gm9buiYQZb3gaxjD5PZkCyFF3ADL",
                "use --file my_wallet.json",
                "use cPCAMF3uPQJQfMvsqfzXTcH7Gm9buiYQZb3gaxjD5PZkCyFF3ADL --network testnet --type segwit"
            ]
        elif command == "wallet":
            help_text = "Show information about the currently active wallet."
            examples = [
                "wallet"
            ]
        elif command == "unload":
            help_text = "Unload the currently active wallet for security."
            examples = [
                "unload"
            ]
        elif command == "balance":
            help_text = "Check the balance of wallet addresses."
            examples = [
                "balance"
            ]
        elif command == "receive":
            help_text = "Generate a payment request with optional amount and message."
            options = [
                ("--amount AMOUNT", "Amount in BTC for the payment request"),
                ("--message MESSAGE", "Optional message for the payment request"),
                ("--new", "Generate a new unused address for receiving")
            ]
            examples = [
                "receive",
                "receive --amount 0.001",
                "receive --amount 0.001 --message \"Payment for coffee\""
            ]
        elif command == "send":
            help_text = "Send a payment to a Bitcoin address."
            options = [
                ("--to ADDRESS", "Recipient Bitcoin address"),
                ("--amount AMOUNT", "Amount in BTC to send"),
                ("--fee PRIORITY", "Fee priority (high, medium, low)"),
                ("--privacy", "Enable enhanced privacy features")
            ]
            examples = [
                "send --to tb1qx94k397yua2lu5hkjtgar396ph4l8uce24g9hv --amount 0.001",
                "send --to tb1qx94k397yua2lu5hkjtgar396ph4l8uce24g9hv --amount 0.001 --fee high"
            ]
        elif command == "history":
            help_text = "Show transaction history for wallet addresses."
            options = [
                ("LIMIT", "Maximum number of transactions to show (default: 10)")
            ]
            examples = [
                "history",
                "history 20"
            ]
        elif command == "fees":
            help_text = "Check current recommended transaction fees."
            examples = [
                "fees"
            ]
        elif command == "rates":
            help_text = "Show current Bitcoin exchange rates in various currencies."
            examples = [
                "rates"
            ]
        elif command == "blockchain":
            help_text = "Show current blockchain information."
            examples = [
                "blockchain"
            ]
        elif command == "mempool":
            help_text = "Show current mempool information."
            examples = [
                "mempool"
            ]
        else:
            console.print(f"[red]Unknown command: '{command}'[/red]")
            return
        
        # Display command help
        console.print(Panel(help_text, title=f"Command: {command}", border_style="blue"))
        
        if options:
            options_table = Table(title="Options")
            options_table.add_column("Option", style="cyan")
            options_table.add_column("Description", style="green")
            
            for option, desc in options:
                options_table.add_row(option, desc)
            
            console.print(options_table)
        
        if examples:
            examples_table = Table(title="Examples")
            examples_table.add_column("Command", style="yellow")
            
            for example in examples:
                examples_table.add_row(example)
            
            console.print(examples_table)

    def _show_command_help_basic(self, command: str) -> None:
        """
        Show detailed help for a specific command with basic formatting.
        
        Args:
            command: Command to show help for
        """
        help_text = ""
        examples = []
        options = []
        
        if command == "create":
            help_text = "Create a new wallet or import from an existing private key."
            options = [
                ("--privkey KEY", "Use an existing private key in WIF format"),
                ("--output FILE", "Save wallet information to a JSON file"),
                ("--type TYPE", "Type of address to generate (segwit, legacy, both)"),
                ("--network NETWORK", "Bitcoin network to use (mainnet, testnet, signet)")
            ]
            examples = [
                "create",
                "create --type legacy",
                "create --privkey cPCAMF3uPQJQfMvsqfzXTcH7Gm9buiYQZb3gaxjD5PZkCyFF3ADL --output my_wallet.json"
            ]
        elif command == "use":
            help_text = "Load/use a wallet for subsequent commands without having to specify the private key each time."
            options = [
                ("PRIVATE_KEY", "Private key in WIF format to use"),
                ("--file WALLET_FILE", "Load wallet from a JSON file"),
                ("--type TYPE", "Type of address to generate (segwit, legacy, both)"),
                ("--network NETWORK", "Bitcoin network to use (mainnet, testnet, signet)")
            ]
            examples = [
                "use cPCAMF3uPQJQfMvsqfzXTcH7Gm9buiYQZb3gaxjD5PZkCyFF3ADL",
                "use --file my_wallet.json",
                "use cPCAMF3uPQJQfMvsqfzXTcH7Gm9buiYQZb3gaxjD5PZkCyFF3ADL --network testnet --type segwit"
            ]
        # Add other commands as in the rich version...
        else:
            print(f"Unknown command: '{command}'")
            return
        
        # Display command help
        print(f"\nCommand: {command}")
        print("=" * 80)
        print(help_text)
        print()
        
        if options:
            print("Options:")
            print("-" * 80)
            for option, desc in options:
                print(f"{option:<20} {desc}")
            print()
        
        if examples:
            print("Examples:")
            print("-" * 80)
            for example in examples:
                print(f"wallet> {example}")
            print()