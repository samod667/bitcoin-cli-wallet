from typing import Optional, List, Tuple
import json
import datetime
from bitcoinutils.setup import setup
from bitcoinutils.transactions import Transaction, TxInput, TxOutput
from bitcoinutils.keys import PrivateKey, P2wpkhAddress
from bitcoinutils.script import Script
import requests
import random
from .privacy import randomize_amount
from bitcoin.wallet import CBitcoinSecret, P2PKHBitcoinAddress, CBech32BitcoinAddress

# Add Rich library imports with fallback
try:
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table
    from rich.panel import Panel
    from rich.console import Console
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False

from .cli import Command, CommandArguments
from . import (
    generate_wallet,
    create_payment_request,
    create_and_sign_transaction,
    broadcast_transaction,
    WalletDisplay,
    get_recommended_fee_rate,
    address_manager,
    get_mempool_info,
    get_blockchain_info
)
from .network import (
    fetch_address_balance, 
    get_recommended_fee_rate, 
    get_exchange_rates,
    fetch_utxos_with_details,
    fetch_utxos  
)
from .wallet_manager import wallet_manager

# Add this new import for transaction history
def fetch_transaction_history(address: str, network: str, limit: int = 10) -> List[dict]:
    """
    Fetch transaction history for an address with detailed information.
    
    Args:
        address: Bitcoin address to check
        network: Network type (mainnet, testnet, signet)
        limit: Maximum number of transactions to fetch
        
    Returns:
        List of transaction details
    """
    import requests
    
    api_urls = {
        "mainnet": "https://blockstream.info/api",
        "testnet": "https://blockstream.info/testnet/api",
        "signet": "https://blockstream.info/signet/api"
    }
    
    base_url = api_urls.get(network)
    if not base_url:
        return [{"error": f"Unsupported network: {network}"}]
    
    try:
        # Get transactions for the address
        response = requests.get(f"{base_url}/address/{address}/txs")
        response.raise_for_status()
        txs = response.json()[:limit]  # Limit number of transactions
        
        # Process each transaction to get more details
        tx_details = []
        for tx in txs:
            tx_id = tx.get('txid')
            
            # Get full transaction details
            tx_response = requests.get(f"{base_url}/tx/{tx_id}")
            tx_response.raise_for_status()
            full_tx = tx_response.json()
            
            # Determine if this is incoming or outgoing
            is_incoming = True
            tx_value = 0
            
            # Check inputs to see if our address is there (outgoing)
            for vin in full_tx.get('vin', []):
                if vin.get('prevout', {}).get('scriptpubkey_address') == address:
                    is_incoming = False
                    break
            
            # Calculate value based on inputs/outputs
            if is_incoming:
                # Sum outputs to our address
                for vout in full_tx.get('vout', []):
                    if vout.get('scriptpubkey_address') == address:
                        tx_value += vout.get('value', 0)
            else:
                # For outgoing, calculate the net amount sent
                # This is more complex as we need to consider change outputs
                # For simplicity, we'll just report the fee and outputs to non-change addresses
                # A more accurate calculation would track all wallet addresses as potential change
                fee = full_tx.get('fee', 0)
                outgoing = 0
                
                for vout in full_tx.get('vout', []):
                    out_addr = vout.get('scriptpubkey_address')
                    if out_addr != address:  # Assume all other outputs are true sends
                        outgoing += vout.get('value', 0)
                
                tx_value = -(outgoing + fee)
            
            # Format transaction details
            tx_detail = {
                "txid": tx_id,
                "date": datetime.datetime.fromtimestamp(full_tx.get('status', {}).get('block_time', 0)).strftime('%Y-%m-%d %H:%M'),
                "confirmations": full_tx.get('status', {}).get('confirmed') and full_tx.get('status', {}).get('block_height', 0) or 0,
                "type": "received" if is_incoming else "sent",
                "amount_sat": tx_value,
                "amount_btc": tx_value / 100_000_000,
                "fee_sat": full_tx.get('fee', 0),
                "status": "confirmed" if full_tx.get('status', {}).get('confirmed') else "pending",
                "block_height": full_tx.get('status', {}).get('block_height'),
                "block_hash": full_tx.get('status', {}).get('block_hash'),
                "explorer_url": f"{api_urls.get(network).replace('/api', '')}/tx/{tx_id}"
            }
            
            tx_details.append(tx_detail)
            
        return tx_details
        
    except requests.exceptions.RequestException as e:
        return [{"error": f"Failed to fetch transaction history: {str(e)}"}]

class CheckFeesCommand(Command):
    def __init__(self, args: CommandArguments):
        self.network = args.network
        self.fee_priority = args.fee_priority

    def execute(self) -> None:
        fee_rates = get_recommended_fee_rate(self.network)
        print("\nCurrent Fee Rates (satoshis/vB):")
        print(f"High Priority: {fee_rates['high']} sat/vB")
        print(f"Medium Priority: {fee_rates['medium']} sat/vB")
        print(f"Low Priority: {fee_rates['low']} sat/vB")
        print(f"\nUsing {self.fee_priority} priority: {fee_rates[self.fee_priority]} sat/vB")

class BlockchainInfoCommand(Command):
    def __init__(self, args: CommandArguments):
        self.network = args.network

    def execute(self) -> None:
        blockchain_info = get_blockchain_info(self.network)
        WalletDisplay.show_blockchain_info(blockchain_info)

class MempoolInfoCommand(Command):
    def __init__(self, args: CommandArguments):
        self.network = args.network

    def execute(self) -> None:
        mempool_info = get_mempool_info(self.network)
        WalletDisplay.show_mempool_info(mempool_info)

class CheckBalanceCommand(Command):
    """Command to check balance of wallet addresses."""
    
    def __init__(self, args: CommandArguments, addresses: Optional[List[Tuple]] = None):
        self.args = args
        self.network = args.network
        
        # Double-check address type from wallet manager
        active_wallet = wallet_manager.get_active_wallet()
        if active_wallet and not args.address_type:
            # If no address type was explicitly provided, use the one from wallet manager
            self.address_type = active_wallet.get('address_type', 'segwit')
        else:
            # Otherwise use the explicit address type from command line
            self.address_type = args.address_type

    def execute(self) -> None:
        """Check balances of wallet addresses."""
        # Get active wallet from manager
        active_wallet = wallet_manager.get_active_wallet()
        if not active_wallet:
            print("No wallet loaded. Use 'create', 'load', or 'use-wallet' first.")
            return
            
        # Get wallet details from active wallet
        privkey = active_wallet.get('private_key')
        network = active_wallet.get('network', self.network)
        
        # Generate addresses from private key
        result = generate_wallet(privkey, network)
        if None in result[:3]:
            print(f"Error generating addresses: {result[3]}")
            return
            
        _, _, _, addresses = result
        
        # Display title
        WalletDisplay.display_title(
            "Bitcoin Wallet", 
            command_name="Balance", 
            network=network
        )
        
        # All addresses are SegWit now, no filtering needed
        filtered_addresses = addresses
        
        # Show balances for all addresses
        WalletDisplay._show_balances(filtered_addresses, network)

class LoadWalletCommand(Command):
    def __init__(self, args: CommandArguments):
        self.args = args
        self.wallet_file = args.load

    def execute(self) -> None:
        try:
            # Load wallet from JSON file
            with open(self.wallet_file, 'r') as f:
                wallet_data = json.load(f)
                
            # Display wallet information
            WalletDisplay.show_wallet_file_info(wallet_data)
            
            # Extract necessary information
            privkey = wallet_data.get('private_key')
            network = wallet_data.get('network', 'testnet')
            
            # Determine address type from metadata if available
            address_type = self.args.address_type  # Use command line if provided
            if not address_type and 'metadata' in wallet_data and 'address_types' in wallet_data['metadata']:
                # Use the file's address type if not specified on command line
                address_types = wallet_data['metadata']['address_types']
                if 'legacy' in address_types and 'segwit' not in address_types:
                    address_type = 'legacy'
                elif 'segwit' in address_types and 'legacy' not in address_types:
                    address_type = 'segwit'
                else:
                    address_type = 'both'
            
            if not privkey:
                print("Error: No private key found in the wallet file.")
                return
            
            # Regenerate wallet using the private key
            result = generate_wallet(privkey, network)
            
            # Display wallet information
            privkey, pubkey, mnemonic, addresses = result
            
            # Store in wallet manager with the correct address_type
            wallet_manager.load_wallet(
                privkey=privkey,
                network=network,
                address_type=address_type,  # Store the correct address type
                addresses=addresses,
                pubkey=pubkey,
                encrypt=False
            )
            
            WalletDisplay.show_wallet_info(
                privkey, pubkey, mnemonic, addresses,
                network, show_balance=True, 
                show_qr=self.args.show_qr,
                address_type=address_type  # Pass address_type to display
            )
                
        except FileNotFoundError:
            print(f"Error: Wallet file '{self.wallet_file}' not found.")
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in wallet file '{self.wallet_file}'.")
        except Exception as e:
            print(f"Failed to load wallet: {str(e)}")

class TransactionHistoryCommand(Command):
    def __init__(self, args: CommandArguments, addresses: List[Tuple]):
        self.args = args
        self.addresses = addresses
        self.network = args.network
        self.limit = args.limit
        self.address_type = args.address_type

    def execute(self) -> None:
        if not self.addresses:
            print("No addresses available. Generate or load a wallet first.")
            return

        # Filter addresses based on address_type
        filtered_addresses = [address[3] for address in self.addresses]
    
        if not filtered_addresses:
            print("No addresses found in wallet.")
            return
        
        # Fetch history for each address
        all_transactions = []
        
        if HAS_RICH:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True
            ) as progress:
                task = progress.add_task(
                    f"[cyan]Fetching transaction history for {len(filtered_addresses)} addresses...", 
                    total=len(filtered_addresses)
                )
                
                for address in filtered_addresses:
                    try:
                        transactions = fetch_transaction_history(address, self.network, self.limit)
                        all_transactions.extend(transactions)
                        progress.update(task, advance=1)
                    except Exception as e:
                        print(f"Error fetching history for {address}: {str(e)}")
        else:
            # Fallback for when rich is not installed
            print(f"Fetching transaction history for {len(filtered_addresses)} addresses...")
            for i, address in enumerate(filtered_addresses):
                try:
                    transactions = fetch_transaction_history(address, self.network, self.limit)
                    all_transactions.extend(transactions)
                    print(f"Progress: {i+1}/{len(filtered_addresses)}")
                except Exception as e:
                    print(f"Error fetching history for {address}: {str(e)}")
        
        # Sort by date (newest first) and limit
        all_transactions.sort(
            key=lambda tx: tx.get('date', ''), 
            reverse=True
        )
        
        # Display transaction history
        WalletDisplay.show_transaction_history(
            all_transactions[:self.limit], 
            self.network
        )

class GenerateWalletCommand(Command):
    """Command to generate or display wallet information."""
    
    def __init__(self, args: CommandArguments):
        self.args = args

    def execute(self) -> None:
        """Execute the command to display wallet info."""
        # Check if we should show balance by default
        check_balance = self.args.check_balance
        if not (self.args.check_fees or self.args.blockchain_info or
                self.args.mempool_info or self.args.load or self.args.rates or
                self.args.receive or self.args.send or self.args.history):
            check_balance = True
            
        # Check if we already have an active wallet
        active_wallet = wallet_manager.get_active_wallet()
        if not active_wallet:
            # If no active wallet, create a new one only if privkey provided
            if self.args.privkey:
                result = generate_wallet(
                    self.args.privkey,
                    self.args.network,
                    self.args.address_type
                )
                
                if None in result[:3]:
                    print(f"Error: {result[3]}")
                    return
                    
                privkey, pubkey, mnemonic, addresses = result
                
                # Store in wallet manager for persistence
                wallet_manager.load_wallet(
                    privkey=privkey,
                    network=self.args.network,
                    address_type=self.args.address_type,
                    addresses=addresses,
                    pubkey=pubkey,
                    encrypt=False
                )
                
                # Show wallet info
                WalletDisplay.show_wallet_info(
                    privkey, pubkey, mnemonic, addresses,
                    self.args.network, check_balance,
                    self.args.show_qr, self.args.address_type
                )
            else:
                # No active wallet and no privkey - show help message
                print("No wallet is currently active.")
                print("Use one of these options to get started:")
                print("  --output FILE         Create a new wallet and save to file")
                print("  --privkey KEY         Import wallet from private key")
                print("  --load FILE           Load wallet from file")
                print("  --use-wallet KEY      Use wallet from private key")
                return
        else:
            # We have an active wallet - show its info
            privkey = active_wallet.get('private_key')
            network = active_wallet.get('network', self.args.network)
            address_type = active_wallet.get('address_type', self.args.address_type)
            
            # Generate full wallet info from private key
            result = generate_wallet(privkey, network, address_type)
            if None in result[:3]:
                print(f"Error: {result[3]}")
                return
                
            _, pubkey, mnemonic, addresses = result
            
            # Display wallet info
            WalletDisplay.show_wallet_info(
                privkey, pubkey, mnemonic, addresses,
                network, check_balance,
                self.args.show_qr, address_type
            )
class ReceiveCommand(Command):
    def __init__(self, args: CommandArguments, addresses: List[Tuple]):
        self.args = args
        self.addresses = addresses

    def execute(self) -> None:
        if not self.args.amount and not self.args.message:
            print("Tip: You can add --amount and --message to create a complete payment request")
        
        # Get receive address (new or reuse)
        if self.args.new_address and len(self.addresses) > 1:
            receive_address = address_manager.get_new_address(self.addresses)
            print("\nUsing new unused address for better privacy")
        else:
            receive_address = self.addresses[0][3]
        
        try:
            payment_uri = create_payment_request(
                receive_address,
                self.args.amount,
                self.args.message,
                self.args.network
            )
            
            WalletDisplay.show_payment_request(
                receive_address,
                payment_uri,
                self.args.amount,
                self.args.message
            )
        except Exception as e:
            print(f"Failed to create payment request: {str(e)}")

class SendCommand(Command):
    def __init__(self, args: CommandArguments, addresses: Optional[List[Tuple]] = None):
        self.args = args
        self.addresses = addresses
        self.fee_priority = args.fee_priority

    def execute(self) -> None:
        """Execute the send payment command using direct API calls."""
        if not self.args.amount:
            print("Please specify amount to send using --amount")
            return
        
        # Get active wallet from wallet_manager
        active_wallet = wallet_manager.get_active_wallet()
        if not active_wallet:
            print("No wallet loaded. Please load a wallet first.")
            return
            
        privkey = active_wallet.get('private_key')
        if not privkey:
            print("No private key available in the active wallet.")
            return
            
        try:
            # Display current fee rates before sending
            CheckFeesCommand(self.args).execute()
            
            # Get addresses if not provided
            if not self.addresses:
                result = generate_wallet(privkey, self.args.network)
                if None not in result[:3]:
                    _, _, _, self.addresses = result
                else:
                    print(f"Error generating addresses: {result[3]}")
                    return
            
            # Get the from address
            from_address = self.addresses[0][3]
            
            if self.args.privacy:
                print("\nPrivacy features enabled:")
                print("- Using new address for change")
                print("- Adding amount randomization")
                print("- Randomizing fee slightly")
            
            print(f"\nPreparing to send {self.args.amount} BTC")
            print(f"From: {from_address}")
            print(f"To: {self.args.send}")
            
            # Setup network
            network = 'testnet' if self.args.network != 'mainnet' else 'bitcoin'
            setup(network)
            
            # Convert amount to satoshis with slight randomization for privacy
            amount_sat = int(self.args.amount * 100_000_000)
            if self.args.privacy:
                amount_sat = int(randomize_amount(self.args.amount) * 100_000_000)
            
            # Create private key from WIF
            priv_key = PrivateKey(wif=privkey)
            pub_key = priv_key.get_public_key()
            
            # Derive the SegWit address from our private key for verification
            derived_addr = pub_key.get_segwit_address()
            print(f"Derived address from private key: {derived_addr.to_string()}")
            
            # Get UTXOs for the address
            utxos = fetch_utxos(from_address, self.args.network)
            if not utxos:
                print("No UTXOs found for this address.")
                return
            
            # Sort UTXOs by value (largest first)
            utxos.sort(key=lambda x: x['value'], reverse=True)
            
            # Get fee rate with slight randomization
            fee_rates = get_recommended_fee_rate(self.args.network)
            fee_rate = fee_rates.get(self.fee_priority, fee_rates['medium'])
            if self.args.privacy:
                fee_rate += random.randint(-1, 1)
            
            # Select UTXOs
            selected_utxos = []
            total_input = 0
            
            for utxo in utxos:
                selected_utxos.append(utxo)
                total_input += utxo['value']
                
                # Estimate transaction size (vbytes for SegWit: ~68 per input, ~31 per output, plus overhead)
                estimated_vsize = 10 + (len(selected_utxos) * 68) + (2 * 31)  # 10 bytes overhead
                estimated_fee = estimated_vsize * fee_rate
                
                if total_input >= amount_sat + estimated_fee:
                    break
            
            if total_input < amount_sat + estimated_fee:
                print(f"Insufficient balance. Need {(amount_sat + estimated_fee)/100_000_000} BTC")
                return
            
            # Calculate change amount
            change_amount = total_input - amount_sat - estimated_fee
            print(f"Transaction details:")
            print(f"  Input: {total_input/100_000_000} BTC")
            print(f"  Output: {amount_sat/100_000_000} BTC")
            print(f"  Fee: {estimated_fee/100_000_000} BTC ({estimated_fee} sats, {fee_rate} sats/vB)")
            print(f"  Change: {change_amount/100_000_000} BTC")
            
            # Create transaction inputs
            tx_inputs = [
                TxInput(utxo['txid'], utxo['vout']) 
                for utxo in selected_utxos
            ]
            
            # Create transaction outputs
            tx_outputs = [
                TxOutput(amount_sat, P2wpkhAddress(self.args.send).to_script_pub_key())
            ]
            
            # Add change output if above dust threshold
            if change_amount > 546:
                change_addr = derived_addr if not self.args.privacy else P2wpkhAddress(address_manager.get_new_address(self.addresses))
                tx_outputs.append(TxOutput(change_amount, change_addr.to_script_pub_key()))
            
            # Create unsigned transaction
            tx = Transaction(tx_inputs, tx_outputs, has_segwit=True)
            
            # Sign each input
            for i, utxo in enumerate(selected_utxos):
                pubkey_hash = pub_key.to_hash160()
                if isinstance(pubkey_hash, bytes):
                    pubkey_hash_hex = pubkey_hash.hex()
                else:
                    pubkey_hash_hex = pubkey_hash  # Shouldn't happen, but safe fallback
                
                script_code = Script(['OP_0', pubkey_hash_hex])
                sig = priv_key.sign_segwit_input(
                    tx,
                    i,
                    script_code,
                    utxo['value']
                )
                # Append witness data as a list of items (signature and public key)
                tx.witnesses.append([sig, pub_key.to_hex()])
            
            # Serialize signed transaction
            signed_tx_hex = tx.serialize()
            print(f"\nSigned Transaction Hex: {signed_tx_hex}")
            
            # Broadcast the transaction
            api_urls = {
                "mainnet": "https://blockstream.info/api",
                "testnet": "https://blockstream.info/testnet/api",
                "signet": "https://blockstream.info/signet/api"
            }
            
            base_url = api_urls.get(self.args.network)
            if not base_url:
                print(f"Unsupported network: {self.args.network}")
                return
            
            response = requests.post(f"{base_url}/tx", data=signed_tx_hex)
            
            if response.status_code == 200:
                tx_id = response.text.strip()
                print("\nTransaction sent successfully!")
                print(f"Transaction ID: {tx_id}")
                explorer_prefix = base_url.replace('/api', '')
                print(f"Track your transaction: {explorer_prefix}/tx/{tx_id}")
            else:
                error_msg = response.text if response.text else f"HTTP {response.status_code}"
                print(f"Failed to broadcast transaction: {error_msg}")
                
        except Exception as e:
            print(f"Failed to send transaction: {str(e)}")
            import traceback
            traceback.print_exc()

class ExchangeRatesCommand(Command):
    def __init__(self, args: CommandArguments):
        self.args = args

    def execute(self) -> None:
        try:
            rates = get_exchange_rates()
            WalletDisplay.show_exchange_rates(rates)
        except Exception as e:
            print(f"Failed to fetch exchange rates: {str(e)}")
    
class UTXOCommand(Command):
    def __init__(self, args: CommandArguments, addresses: List[Tuple]):
        self.args = args
        self.addresses = addresses
        self.network = args.network
        self.address_type = args.address_type

    def execute(self) -> None:
        if not self.addresses:
            print("No addresses available. Generate or load a wallet first.")
            return

        # All addresses are SegWit now, no need to filter
        filtered_addresses = [address[3] for address in self.addresses]
        
        # Fetch UTXOs for each address
        all_utxos = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            task = progress.add_task(
                f"[cyan]Fetching UTXOs for {len(filtered_addresses)} addresses...", 
                total=len(filtered_addresses)
            )
            
            for address in filtered_addresses:
                try:
                    utxos = fetch_utxos_with_details(address, self.network)
                    if utxos and "error" not in utxos[0]:
                        all_utxos.extend(utxos)
                    progress.update(task, advance=1)
                except Exception as e:
                    print(f"Error fetching UTXOs for {address}: {str(e)}")
        
        # Display UTXOs
        WalletDisplay.show_utxos(all_utxos, self.network)

class UseWalletCommand(Command):
    def __init__(self, args: CommandArguments):
        self.args = args
        self.privkey = args.use_wallet

    def execute(self) -> None:
        try:
            # Make sure we have an address type
            if not self.args.address_type:
                self.args = self.args._replace(address_type="segwit")  # Default
                
            # Print what we're doing and explicitly show address type being used
            print(f"Loading wallet with {self.args.address_type} addresses...")
            
            # Generate wallet to get addresses
            result = generate_wallet(
                self.privkey,
                self.args.network,
                self.args.address_type
            )
            
            if None in result[:3]:
                error_message = result[3]
                print(error_message)
                return
                
            privkey, pubkey, mnemonic, addresses = result
            
            # DEBUGGING - Print information about what's being stored
            print(f"Generated addresses with type: {self.args.address_type}")
            print(f"First address: {addresses[0][3]}")
            
            # Load into wallet manager - make sure address_type is stored
            success = wallet_manager.load_wallet(
                privkey=privkey,
                network=self.args.network,
                addresses=addresses,
                pubkey=pubkey,
                encrypt=False
            )
            
            if success:
                print(f"Wallet loaded successfully and will be used for subsequent commands.")
                print(f"Network: {self.args.network}")
                print(f"Address type: {self.args.address_type}")
                print(f"Number of addresses: {len(addresses)}")
                print(f"Use --wallet-info to see details or --unload-wallet to unload it.")
                
                # Display wallet info with the correct address type
                WalletDisplay.show_wallet_info(
                    privkey, pubkey, mnemonic, addresses,
                    self.args.network, show_balance=False,
                    show_qr=False, address_type=self.args.address_type
                )
        except Exception as e:
            print(f"Failed to load wallet: {str(e)}")

class UseWalletFileCommand(Command):
    def __init__(self, args: CommandArguments):
        self.args = args
        self.wallet_file = args.use_wallet_file

    def execute(self) -> None:
        try:
            # First display wallet file info
            with open(self.wallet_file, 'r') as f:
                wallet_data = json.load(f)
            
            WalletDisplay.show_wallet_file_info(wallet_data)
            
            # Load into wallet manager
            success = wallet_manager.load_wallet_from_file(self.wallet_file)
            
            if success:
                print(f"Wallet file loaded successfully and will be used for subsequent commands.")
                print(f"Use --wallet-info to see details or --unload-wallet to unload it.")
                
        except FileNotFoundError:
            print(f"Error: Wallet file '{self.wallet_file}' not found.")
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in wallet file '{self.wallet_file}'.")
        except Exception as e:
            print(f"Failed to load wallet: {str(e)}")

class UnloadWalletCommand(Command):
    def __init__(self, args: CommandArguments):
        self.args = args

    def execute(self) -> None:
        wallet_manager.unload_wallet()

class WalletInfoCommand(Command):
    def __init__(self, args: CommandArguments):
        self.args = args

    def execute(self) -> None:
        try:
            active_wallet = wallet_manager.get_active_wallet()
            
            if not active_wallet:
                print("No wallet is currently loaded.")
                print("Use --use-wallet KEY or --use-wallet-file FILE to load a wallet.")
                return
                
            privkey = active_wallet.get('private_key')
            network = active_wallet.get('network', 'testnet')
            
            # IMPORTANT: Use the address type from the command line args if provided
            # Otherwise fallback to the stored address type
            address_type = self.args.address_type if self.args.address_type else active_wallet.get('address_type', 'segwit')
            
            # Generate wallet to get full details with the correct address type
            result = generate_wallet(privkey, network, address_type)
            
            if None in result[:3]:
                error_message = result[3]
                print(error_message)
                return
                
            privkey, pubkey, mnemonic, addresses = result
            
            # Update wallet manager with addresses if needed
            wallet_manager.update_wallet_info(addresses)
            
            print("A wallet is currently active and will be used for commands.")
            print(f"Network: {network}")
            print(f"Address type: {address_type}")
            
            # Show wallet info with the correct address type
            WalletDisplay.show_wallet_info(
                privkey, pubkey, mnemonic, addresses,
                network, show_balance=True,
                show_qr=False, address_type=address_type
            )
            
        except Exception as e:
            print(f"Error displaying wallet information: {str(e)}")
class AddressInfoCommand(Command):
    def __init__(self, args: CommandArguments):
        self.args = args
        self.network = args.network
        self.address = args.address

    def execute(self) -> None:
        # Display title
        WalletDisplay.display_title(
            "Bitcoin Wallet", 
            command_name=f"Address Info", 
            network=self.network
        )
        
        print(f"\nChecking address: {self.address}")
        
        # Fetch and display balance
        balance_info = fetch_address_balance(self.address, self.network)
        
        if balance_info.get("error"):
            print(f"Error checking address: {balance_info['error']}")
            return
            
        # Format and display the balance information
        confirmed = balance_info.get('confirmed_balance_btc', 0)
        unconfirmed = balance_info.get('unconfirmed_balance_btc', 0)
        tx_count = balance_info.get('tx_count', 0)
        unconf_count = balance_info.get('unconfirmed_tx_count', 0)

        if self.args.history:
            transactions = fetch_transaction_history(self.address, self.network, self.args.limit)
            WalletDisplay.show_transaction_history(transactions, self.network)
        
        print(f"Confirmed Balance: {confirmed:.8f} BTC")
        print(f"Pending Balance: {unconfirmed:.8f} BTC")
        print(f"Total Balance: {confirmed + unconfirmed:.8f} BTC")
        print(f"Transactions: {tx_count} ({unconf_count} pending)")
        
        # Optional: offer to show transaction history
        print(f"\nTip: Use '--address {self.address} --history' to see transaction history")
class HelpCommand(Command):
    """Command to display help information for the wallet."""
    
    def __init__(self, args: CommandArguments):
        self.args = args
        self.network = args.network
        self.specific_command = args.help_command
    
    def execute(self) -> None:
        """Display help information."""
        if HAS_RICH:
            self._display_help_rich()
        else:
            self._display_help_basic()
    
    def _display_help_rich(self) -> None:
        """Display help information with Rich formatting."""
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich.markdown import Markdown
        
        console = Console()
        
        # Display title
        WalletDisplay.display_title("Bitcoin Wallet CLI", command_name="Help", network=self.network)
        
        # If a specific command was requested, display detailed help for that command
        if self.specific_command:
            self._display_command_help_rich(self.specific_command)
            return
        
        # General description
        console.print(Panel(
            "A command-line Bitcoin wallet for managing addresses, checking balances, "
            "sending and receiving transactions, and viewing blockchain information. "
            "Works with testnet, signet, and mainnet networks.",
            title="Bitcoin Wallet CLI",
            border_style="green"
        ))
        
        # Wallet operations section
        wallet_table = Table(title="Wallet Operations")
        wallet_table.add_column("Command", style="cyan")
        wallet_table.add_column("Description", style="green")
        wallet_table.add_column("Example", style="yellow")
        
        wallet_commands = [
            ("--output FILE", "Save wallet to file", "--output my_wallet.json"),
            ("--privkey KEY", "Import from private key", "--privkey cNB35hjte5Se8CjpwsPBJgxkjzfAEyGXNJ84Jw5nfhVX8hau1SMc"),
            ("--load FILE", "Load wallet from file", "--load my_wallet.json"),
            ("--use-wallet KEY", "Use wallet for subsequent commands", "--use-wallet cNB35hjte5Se8CjpwsPBJgxkjzfAEyGXNJ84Jw5nfhVX8hau1SMc"),
            ("--use-wallet-file FILE", "Use wallet file for subsequent commands", "--use-wallet-file my_wallet.json"),
            ("--wallet-info", "Show wallet information", "--wallet-info"),
            ("--unload-wallet", "Unload active wallet", "--unload-wallet"),
            ("--check-balance", "Check wallet balance", "--check-balance"),
            ("--address ADDR", "Check balance of any address", "--address tb1qds6redgk9lk9zcspmc43a9a77p9gtrz8gney6l"),
            ("--show-qr", "Show QR codes for addresses", "--show-qr"),
            ("--network NETWORK", "Set network (mainnet, testnet, signet)", "--network testnet")
        ]
        
        for cmd, desc, example in wallet_commands:
            wallet_table.add_row(cmd, desc, example)
            
        console.print(wallet_table)
        
        # Transaction operations section
        tx_table = Table(title="Transaction Operations")
        tx_table.add_column("Command", style="cyan")
        tx_table.add_column("Description", style="green")
        tx_table.add_column("Example", style="yellow")
        
        tx_commands = [
            ("--receive", "Generate payment request", "--receive --amount 0.001 --message \"Payment\""),
            ("--new-address", "Use new address for receiving", "--receive --new-address"),
            ("--amount AMOUNT", "Set amount for send/receive", "--amount 0.001"),
            ("--message MSG", "Add message to payment request", "--message \"Coffee payment\""),
            ("--send ADDR", "Send Bitcoin to address", "--send tb1qds6redgk9lk9zcspmc43a9a77p9gtrz8gney6l --amount 0.001"),
            ("--fee-priority LEVEL", "Set fee priority (high, medium, low)", "--fee-priority high"),
            ("--privacy", "Enable privacy features", "--send ADDR --amount 0.001 --privacy"),
            ("--history", "Show transaction history", "--history"),
            ("--limit N", "Limit history results", "--history --limit 5"),
            ("--utxos", "Show unspent transaction outputs", "--utxos")
        ]
        
        for cmd, desc, example in tx_commands:
            tx_table.add_row(cmd, desc, example)
            
        console.print(tx_table)
        
        # Network information section
        network_table = Table(title="Network Information")
        network_table.add_column("Command", style="cyan")
        network_table.add_column("Description", style="green")
        network_table.add_column("Example", style="yellow")
        
        network_commands = [
            ("--check-fees", "Check current recommended fees", "--check-fees"),
            ("--blockchain-info", "Show blockchain information", "--blockchain-info"),
            ("--mempool-info", "Show mempool information", "--mempool-info"),
            ("--rates", "Show Bitcoin exchange rates", "--rates")
        ]
        
        for cmd, desc, example in network_commands:
            network_table.add_row(cmd, desc, example)
            
        console.print(network_table)
        
        # Interactive mode
        console.print(Panel(
            "Start an interactive session with the wallet using the [bold]--interactive[/bold] flag.\n"
            "In interactive mode, you can use commands like: [italic]create, load, wallet, balance, "
            "receive, send, history, fees, blockchain, help, exit[/italic]",
            title="Interactive Mode",
            border_style="blue"
        ))
        
        # Example workflows
        console.print(Markdown("""
        ## Example Workflows
        
        ### Create and save a new wallet:
        ```
        python main.py --output my_wallet.json
        ```
        
        ### Check balance of an address:
        ```
        python main.py --address tb1qds6redgk9lk9zcspmc43a9a77p9gtrz8gney6l
        ```
        
        ### Receive Bitcoin:
        ```
        python main.py --load my_wallet.json --receive --amount 0.001 --message "Payment"
        ```
        
        ### Send Bitcoin:
        ```
        python main.py --load my_wallet.json --send tb1qds6redgk9lk9zcspmc43a9a77p9gtrz8gney6l --amount 0.0001
        ```
        
        ### Check transaction history:
        ```
        python main.py --load my_wallet.json --history
        ```
        """))
        
        # Get more help
        console.print("\nFor more detailed help on specific commands, use: [bold cyan]python main.py --help command_name[/bold cyan]")

    
    def _display_help_basic(self) -> None:
        """Display help information with basic formatting."""
        print("\n" + "=" * 80)
        print(" " * 30 + "BITCOIN WALLET CLI")
        print("=" * 80)
        
        print("\nA command-line Bitcoin wallet for managing addresses, checking balances,")
        print("sending and receiving transactions, and viewing blockchain information.")
        print("Works with testnet, signet, and mainnet networks.")
        
        print("\n" + "=" * 80)
        print("WALLET OPERATIONS")
        print("=" * 80)
        print("--output FILE            Save wallet to file (e.g., --output my_wallet.json)")
        print("--privkey KEY            Import from private key")
        print("--load FILE              Load wallet from file")
        print("--use-wallet KEY         Use wallet for subsequent commands")
        print("--use-wallet-file FILE   Use wallet file for subsequent commands")
        print("--wallet-info            Show wallet information")
        print("--unload-wallet          Unload active wallet")
        print("--check-balance          Check wallet balance")
        print("--address ADDR           Check balance of any address")
        print("--show-qr                Show QR codes for addresses")
        print("--network NETWORK        Set network (mainnet, testnet, signet)")
        
        print("\n" + "=" * 80)
        print("TRANSACTION OPERATIONS")
        print("=" * 80)
        print("--receive                Generate payment request")
        print("--new-address            Use new address for receiving")
        print("--amount AMOUNT          Set amount for send/receive")
        print("--message MSG            Add message to payment request")
        print("--send ADDR              Send Bitcoin to address")
        print("--fee-priority LEVEL     Set fee priority (high, medium, low)")
        print("--privacy                Enable privacy features")
        print("--history                Show transaction history")
        print("--limit N                Limit history results")
        print("--utxos                  Show unspent transaction outputs")
        
        print("\n" + "=" * 80)
        print("NETWORK INFORMATION")
        print("=" * 80)
        print("--check-fees             Check current recommended fees")
        print("--blockchain-info        Show blockchain information")
        print("--mempool-info           Show mempool information")
        print("--rates                  Show Bitcoin exchange rates")
        
        print("\n" + "=" * 80)
        print("INTERACTIVE MODE")
        print("=" * 80)
        print("--interactive            Start an interactive session with the wallet")
        print("                         In interactive mode, use commands like: create, load,")
        print("                         balance, receive, send, history, fees, exit")
        
        print("\n" + "=" * 80)
        print("EXAMPLE WORKFLOWS")
        print("=" * 80)
        print("Create and save a new wallet:")
        print("  python main.py --output my_wallet.json")
        print("\nCheck balance of an address:")
        print("  python main.py --address tb1qds6redgk9lk9zcspmc43a9a77p9gtrz8gney6l")
        print("\nReceive Bitcoin:")
        print("  python main.py --load my_wallet.json --receive --amount 0.001 --message \"Payment\"")
        print("\nSend Bitcoin:")
        print("  python main.py --load my_wallet.json --send tb1qds6redgk9lk9zcspmc43a9a77p9gtrz8gney6l --amount 0.0001")
        print("\nCheck transaction history:")
        print("  python main.py --load my_wallet.json --history")
        
    def _display_command_help_rich(self, command: str) -> None:
        """Display detailed help for a specific command using Rich formatting."""
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        
        console = Console()
        
        # Define help content for each command
        command_help = {
            "output": {
                "title": "--output FILE",
                "description": "Save wallet information to a JSON file for later use.",
                "options": [
                    ("FILE", "Path to the output JSON file")
                ],
                "examples": [
                    "python main.py --output my_wallet.json",
                    "python main.py --network testnet --output testnet_wallet.json"
                ]
            },
            "privkey": {
                "title": "--privkey KEY",
                "description": "Import a wallet using an existing private key in WIF format.",
                "options": [
                    ("KEY", "Private key in WIF format")
                ],
                "examples": [
                    "python main.py --privkey cNB35hjte5Se8CjpwsPBJgxkjzfAEyGXNJ84Jw5nfhVX8hau1SMc",
                    "python main.py --privkey cNB35hjte5Se8CjpwsPBJgxkjzfAEyGXNJ84Jw5nfhVX8hau1SMc --output imported_wallet.json"
                ]
            },
            "load": {
                "title": "--load FILE",
                "description": "Load wallet information from a previously saved JSON file.",
                "options": [
                    ("FILE", "Path to the wallet JSON file")
                ],
                "examples": [
                    "python main.py --load my_wallet.json",
                    "python main.py --load my_wallet.json --check-balance"
                ]
            },
            "use-wallet": {
                "title": "--use-wallet KEY",
                "description": "Load a wallet using a private key and make it active for subsequent commands.",
                "options": [
                    ("KEY", "Private key in WIF format")
                ],
                "examples": [
                    "python main.py --use-wallet cNB35hjte5Se8CjpwsPBJgxkjzfAEyGXNJ84Jw5nfhVX8hau1SMc",
                    "python main.py --use-wallet cNB35hjte5Se8CjpwsPBJgxkjzfAEyGXNJ84Jw5nfhVX8hau1SMc --network testnet"
                ]
            },
            "use-wallet-file": {
                "title": "--use-wallet-file FILE",
                "description": "Load a wallet from a JSON file and make it active for subsequent commands.",
                "options": [
                    ("FILE", "Path to the wallet JSON file")
                ],
                "examples": [
                    "python main.py --use-wallet-file my_wallet.json",
                    "python main.py --use-wallet-file my_wallet.json --check-balance"
                ]
            },
            "wallet-info": {
                "title": "--wallet-info",
                "description": "Show information about the currently active wallet.",
                "options": [],
                "examples": [
                    "python main.py --wallet-info",
                    "python main.py --use-wallet-file my_wallet.json --wallet-info"
                ]
            },
            "unload-wallet": {
                "title": "--unload-wallet",
                "description": "Unload the currently active wallet for security.",
                "options": [],
                "examples": [
                    "python main.py --unload-wallet"
                ]
            },
            "check-balance": {
                "title": "--check-balance",
                "description": "Check the balance of all addresses in the wallet.",
                "options": [],
                "examples": [
                    "python main.py --load my_wallet.json --check-balance",
                    "python main.py --use-wallet cNB35hjte5Se8CjpwsPBJgxkjzfAEyGXNJ84Jw5nfhVX8hau1SMc --check-balance"
                ]
            },
            "address": {
                "title": "--address ADDR",
                "description": "Check the balance of any Bitcoin address without loading a wallet.",
                "options": [
                    ("ADDR", "Bitcoin address to check")
                ],
                "examples": [
                    "python main.py --address tb1qds6redgk9lk9zcspmc43a9a77p9gtrz8gney6l",
                    "python main.py --address tb1qds6redgk9lk9zcspmc43a9a77p9gtrz8gney6l --history"
                ]
            },
            "show-qr": {
                "title": "--show-qr",
                "description": "Show QR codes for all addresses in the wallet.",
                "options": [],
                "examples": [
                    "python main.py --load my_wallet.json --show-qr",
                    "python main.py --use-wallet cNB35hjte5Se8CjpwsPBJgxkjzfAEyGXNJ84Jw5nfhVX8hau1SMc --show-qr"
                ]
            },
            "network": {
                "title": "--network NETWORK",
                "description": "Set the Bitcoin network to use (mainnet, testnet, signet).",
                "options": [
                    ("NETWORK", "Network type (mainnet, testnet, signet)")
                ],
                "examples": [
                    "python main.py --network testnet",
                    "python main.py --network mainnet --output mainnet_wallet.json"
                ]
            },
            "receive": {
                "title": "--receive",
                "description": "Generate a payment request with optional amount and message.",
                "options": [
                    ("--amount", "Amount in BTC for the payment request"),
                    ("--message", "Optional message for the payment request"),
                    ("--new-address", "Generate a new unused address for receiving")
                ],
                "examples": [
                    "python main.py --load my_wallet.json --receive",
                    "python main.py --load my_wallet.json --receive --amount 0.001",
                    "python main.py --load my_wallet.json --receive --amount 0.001 --message \"Coffee payment\"",
                    "python main.py --load my_wallet.json --receive --new-address --amount 0.001"
                ]
            },
            "send": {
                "title": "--send ADDR",
                "description": "Send Bitcoin to the specified address.",
                "options": [
                    ("ADDR", "Recipient Bitcoin address"),
                    ("--amount", "Amount in BTC to send"),
                    ("--fee-priority", "Fee priority (high, medium, low)"),
                    ("--privacy", "Enable enhanced privacy features")
                ],
                "examples": [
                    "python main.py --load my_wallet.json --send tb1qds6redgk9lk9zcspmc43a9a77p9gtrz8gney6l --amount 0.001",
                    "python main.py --load my_wallet.json --send tb1qds6redgk9lk9zcspmc43a9a77p9gtrz8gney6l --amount 0.001 --fee-priority high",
                    "python main.py --load my_wallet.json --send tb1qds6redgk9lk9zcspmc43a9a77p9gtrz8gney6l --amount 0.001 --privacy"
                ]
            },
            "history": {
                "title": "--history",
                "description": "Show transaction history for wallet addresses.",
                "options": [
                    ("--limit", "Maximum number of transactions to show (default: 10)")
                ],
                "examples": [
                    "python main.py --load my_wallet.json --history",
                    "python main.py --load my_wallet.json --history --limit 5",
                    "python main.py --address tb1qds6redgk9lk9zcspmc43a9a77p9gtrz8gney6l --history"
                ]
            },
            "utxos": {
                "title": "--utxos",
                "description": "Show unspent transaction outputs (UTXOs) for all addresses in the wallet.",
                "options": [],
                "examples": [
                    "python main.py --load my_wallet.json --utxos",
                    "python main.py --use-wallet cNB35hjte5Se8CjpwsPBJgxkjzfAEyGXNJ84Jw5nfhVX8hau1SMc --utxos"
                ]
            },
            "check-fees": {
                "title": "--check-fees",
                "description": "Check current recommended transaction fees.",
                "options": [],
                "examples": [
                    "python main.py --check-fees",
                    "python main.py --network mainnet --check-fees"
                ]
            },
            "blockchain-info": {
                "title": "--blockchain-info",
                "description": "Show current blockchain information.",
                "options": [],
                "examples": [
                    "python main.py --blockchain-info",
                    "python main.py --network testnet --blockchain-info"
                ]
            },
            "mempool-info": {
                "title": "--mempool-info",
                "description": "Show current mempool information.",
                "options": [],
                "examples": [
                    "python main.py --mempool-info",
                    "python main.py --network testnet --mempool-info"
                ]
            },
            "rates": {
                "title": "--rates",
                "description": "Show current Bitcoin exchange rates in various currencies.",
                "options": [],
                "examples": [
                    "python main.py --rates"
                ]
            },
            "interactive": {
                "title": "--interactive",
                "description": "Start in interactive mode for a more user-friendly experience.",
                "options": [],
                "examples": [
                    "python main.py --interactive",
                    "python main.py --network testnet --interactive"
                ]
            }
        }
        
        # Remove the leading "--" if present
        cmd_key = command.lstrip("-")
        
        # Check if help exists for this command
        if cmd_key not in command_help:
            console.print(f"[bold red]No help available for command: {command}[/bold red]")
            return
        
        help_data = command_help[cmd_key]
        
        # Display panel with command description
        console.print(Panel(
            help_data["description"],
            title=help_data["title"],
            border_style="green"
        ))
        
        # Display options if any
        if help_data["options"]:
            options_table = Table(title="Options")
            options_table.add_column("Option", style="cyan")
            options_table.add_column("Description", style="green")
            
            for option, desc in help_data["options"]:
                options_table.add_row(option, desc)
            
            console.print(options_table)
        
        # Display examples
        examples_table = Table(title="Examples")
        examples_table.add_column("Command", style="yellow")
        
        for example in help_data["examples"]:
            examples_table.add_row(example)
        
        console.print(examples_table)

class NoWalletCommand(Command):
    """Command that shows an error when no wallet is loaded but required."""
    
    def __init__(self, args: CommandArguments):
        self.args = args
    
    def execute(self) -> None:
        """Show error message about no wallet being loaded."""
        print("Error: This command requires an active wallet, but no wallet is loaded.")
        print("To use this command, first load a wallet using one of these methods:")
        print("  --load FILE           Load wallet from file")
        print("  --use-wallet KEY      Use wallet from private key")
        print("  --use-wallet-file FILE  Use wallet from wallet file")
        print("  --privkey KEY         Import wallet from private key")

def create_command(args: CommandArguments) -> Command:
    """Factory function to create appropriate command based on arguments."""
    # Handle simple non-wallet commands first
    if args.help or args.help_command:
        return HelpCommand(args)
    elif args.check_fees:
        return CheckFeesCommand(args)
    elif args.blockchain_info:
        return BlockchainInfoCommand(args)
    elif args.mempool_info:
        return MempoolInfoCommand(args)
    elif args.rates:
        return ExchangeRatesCommand(args)
    
    # Handle wallet management commands
    if args.load:
        return LoadWalletCommand(args)
    elif args.use_wallet:
        return UseWalletCommand(args)
    elif args.use_wallet_file:
        return UseWalletFileCommand(args)
    elif args.unload_wallet:
        return UnloadWalletCommand(args)
    elif args.address:
        return AddressInfoCommand(args)
    
    
    active_wallet = wallet_manager.get_active_wallet()
    addresses = None
    if active_wallet:
        privkey = active_wallet.get('private_key')
        network = active_wallet.get('network', args.network)
        address_type = active_wallet.get('address_type', args.address_type)
        result = generate_wallet(privkey, network, address_type)
        if None not in result[:3]:
            _, _, _, addresses = result

    # Process wallet-dependent commands with addresses
    if args.wallet_info:
        return WalletInfoCommand(args)
    elif args.check_balance:
        return CheckBalanceCommand(args, addresses)
    elif args.history:
        return TransactionHistoryCommand(args, addresses)
    elif args.receive:
        return ReceiveCommand(args, addresses)
    elif args.send:
        return SendCommand(args, addresses)
    elif args.utxos:
        return UTXOCommand(args, addresses)