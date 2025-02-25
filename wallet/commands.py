from typing import Optional, List, Tuple
import json
import datetime

# Add Rich library imports with fallback
try:
    from rich.progress import Progress, SpinnerColumn, TextColumn
    HAS_RICH = True
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
    fetch_utxos_with_details  # Add this import
)

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
            
            if not privkey:
                print("Error: No private key found in the wallet file.")
                return
            
            # Regenerate wallet using the private key
            result = generate_wallet(privkey, network, self.args.address_type)
            
            # Display wallet information
            privkey, pubkey, mnemonic, addresses = result
            WalletDisplay.show_wallet_info(
                privkey, pubkey, mnemonic, addresses,
                network, show_balance=True, 
                show_qr=self.args.show_qr,
                address_type=self.args.address_type  # Pass address_type to display
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
        filtered_addresses = []
        for _, _, _, address in self.addresses:
            is_segwit = address.startswith(('tb1', 'bc1'))
            if (self.address_type == "both" or 
                (self.address_type == "segwit" and is_segwit) or
                (self.address_type == "legacy" and not is_segwit)):
                filtered_addresses.append(address)
        
        if not filtered_addresses:
            print(f"No {self.address_type} addresses found in wallet.")
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
    def __init__(self, args: CommandArguments):
        self.args = args

    def execute(self) -> None:
        result = generate_wallet(
            self.args.privkey,
            self.args.network,
            self.args.address_type
        )
        
        if None in result[:3]:
            error_message = result[3]
            print(error_message)
            return
            
        privkey, pubkey, mnemonic, addresses = result
        WalletDisplay.show_wallet_info(
            privkey, pubkey, mnemonic, addresses,
            self.args.network, self.args.check_balance,
            self.args.show_qr, self.args.address_type  # Pass address_type to display
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
    def __init__(self, args: CommandArguments, addresses: List[Tuple]):
        self.args = args
        self.addresses = addresses

    def execute(self) -> None:
        if not self.args.amount:
            print("Please specify amount to send using --amount")
            return
        if not self.args.privkey:
            print("Please provide a private key to send from")
            return
        
        try:
            # Display current fee rates before sending
            CheckFeesCommand(self.args).execute()
            
            from_address = self.addresses[0][3]
            
            if self.args.privacy:
                print("\nPrivacy features enabled:")
                print("- Using new address for change")
                print("- Adding amount randomization")
                print("- Randomizing fee slightly")
            
            print(f"\nPreparing to send {self.args.amount} BTC")
            print(f"From: {from_address}")
            print(f"To: {self.args.send}")
            
            # Create and sign transaction
            tx = create_and_sign_transaction(
                from_address,
                self.args.privkey,
                self.args.send,
                self.args.amount,
                self.args.network,
                self.args.fee_priority,
                self.addresses if self.args.privacy else None
            )
            
            # Broadcast the transaction
            tx_id = broadcast_transaction(tx, self.args.network)
            
            print("\nTransaction sent successfully!")
            print(f"Transaction ID: {tx_id}")
            print(f"Track your transaction: https://blockstream.info/{self.args.network}/tx/{tx_id}")
            
        except Exception as e:
            print(f"Failed to send transaction: {str(e)}")

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

        # Filter addresses based on address_type
        filtered_addresses = []
        for _, _, _, address in self.addresses:
            is_segwit = address.startswith(('tb1', 'bc1'))
            if (self.address_type == "both" or 
                (self.address_type == "segwit" and is_segwit) or
                (self.address_type == "legacy" and not is_segwit)):
                filtered_addresses.append(address)
        
        if not filtered_addresses:
            print(f"No {self.address_type} addresses found in wallet.")
            return
        
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

def create_command(args: CommandArguments, addresses: Optional[List[Tuple]] = None) -> Command:
    """Factory function to create appropriate command based on arguments."""
    if args.load:
        return LoadWalletCommand(args)
    elif args.check_fees:
        return CheckFeesCommand(args)
    elif args.blockchain_info:
        return BlockchainInfoCommand(args)
    elif args.mempool_info:
        return MempoolInfoCommand(args)
    elif args.history and addresses:
        return TransactionHistoryCommand(args, addresses)
    elif args.receive and addresses:
        return ReceiveCommand(args, addresses)
    elif args.send and addresses:
        return SendCommand(args, addresses)
    elif args.rates:
        return ExchangeRatesCommand(args)
    elif args.utxos and addresses:
        return UTXOCommand(args, addresses)
    else:
        return GenerateWalletCommand(args)