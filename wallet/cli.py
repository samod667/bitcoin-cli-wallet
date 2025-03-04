import argparse
from typing import NamedTuple, Optional
from abc import ABC, abstractmethod

class CommandArguments(NamedTuple):
    """Structured container for parsed command line arguments."""
    network: str
    output: Optional[str] 
    check_balance: bool
    show_qr: bool
    address_type: str = "segwit"
    privkey: Optional[str] = None
    receive: bool = False
    new_address: bool = False
    amount: Optional[float] = None
    message: Optional[str] = None
    send: Optional[str] = None
    fee_priority: str = "medium"
    privacy: bool = False
    check_fees: bool = False
    blockchain_info: bool = False
    mempool_info: bool = False
    load: Optional[str] = None
    history: bool = False
    limit: int = 10
    rates: bool = False
    interactive: bool = False
    utxos: bool = False
    use_wallet: Optional[str] = None
    use_wallet_file: Optional[str] = None
    unload_wallet: bool = False
    wallet_info: bool = False
    address: Optional[str] = None
    help: bool = False
    help_command: Optional[str] = None

class Command(ABC):
    """Base class for all CLI commands."""
    
    @abstractmethod
    def execute(self) -> None:
        """Execute the command."""
        pass

def create_argument_parser() -> argparse.ArgumentParser:
    """Set up and configure command-line argument parser."""
    parser = argparse.ArgumentParser(description="Bitcoin Wallet CLI", add_help=False)
    
    # Basic wallet operations
    parser.add_argument(
        "--network",
        choices=["mainnet", "testnet", "signet"],
        default="testnet",
        help="Bitcoin network to use (default: testnet)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Save wallet information to specified JSON file"
    )
    parser.add_argument(
        "--check-balance",
        action="store_true",
        help="Check balances for all generated addresses"
    )
    parser.add_argument(
        "--show-qr",
        action="store_true",
        help="Show QR codes for addresses in terminal"
    )
    parser.add_argument(
        "--address-type",
        action="store_const",
        const="segwit",
        default="segwit",
    )
    parser.add_argument(  # Changed from positional to optional
        "--privkey",      # Changed from privKey to privkey
        type=str,
        default=None,
        help="Optional private key in WIF format"
    )
    parser.add_argument(
        "--fee-priority",
        choices=['high', 'medium', 'low'],
        default='medium',
        help="Fee priority level (default: medium)"
    )
    parser.add_argument(
        "--privacy",
        action="store_true",
        help="Enable enhanced privacy features"
    )
    parser.add_argument(
        "--check-fees",
        action="store_true",
        help="Check current recommended transaction fees"
    )
    parser.add_argument(
        "--blockchain-info",
        action="store_true",
        help="Retrieve and display current blockchain information"
    )
    parser.add_argument(
        "--mempool-info",
        action="store_true",
        help="Retrieve and display current mempool information"
    )
    
    # Transaction operations group
    tx_group = parser.add_argument_group('transaction operations')
    tx_group.add_argument(
        "--receive",
        action="store_true",
        help="Generate a payment request with amount and message"
    )
    tx_group.add_argument(
        "--new-address",
        action="store_true",
        help="Generate a new unused address for receiving"
    )
    tx_group.add_argument(
        "--amount",
        type=float,
        help="Amount in BTC for receive/send operation"
    )
    tx_group.add_argument(
        "--message",
        type=str,
        help="Optional message for the payment request"
    )
    tx_group.add_argument(
        "--send",
        type=str,
        help="Send BTC to the specified address"
    )
    parser.add_argument(
        "--load",
        type=str,
        help="Load wallet information from a JSON file"
    )
    parser.add_argument(
    "--history",
    action="store_true",
    help="Show transaction history for wallet addresses"
)
    parser.add_argument(
    "--limit",
    type=int,
    default=10,
    help="Limit number of transactions in history (default: 10)"
)
    parser.add_argument(
    "--rates",
    action="store_true",
    help="Show current Bitcoin exchange rates"
)
    parser.add_argument(
    "--interactive",
    action="store_true",
    help="Start in interactive mode"
)
    parser.add_argument(
    "--utxos",
    action="store_true",
    help="Show unspent transaction outputs (UTXOs)"
)
    parser.add_argument(
    "--use-wallet",
    type=str,
    help="Load a wallet for subsequent commands using private key"
)

    parser.add_argument(
        "--use-wallet-file",
        type=str,
        help="Load a wallet for subsequent commands from a wallet file"
)

    parser.add_argument(
        "--unload-wallet",
        action="store_true",
        help="Unload the currently active wallet"
)

    parser.add_argument(
        "--wallet-info",
        action="store_true",
        help="Display information about the currently active wallet"
)
    parser.add_argument(
        "--address",
        type=str,
        help="Check balance of any Bitcoin address (without loading a wallet)"
)
    help_group = parser.add_argument_group('help')
    help_group.add_argument(
        "--help",
        action="store_true",
        help="Show detailed help information"
    )
    help_group.add_argument(
        "--help-command",
        metavar="COMMAND",
        help="Show detailed help for a specific command"
    )
    return parser

def parse_args() -> CommandArguments:
    """Parse command-line arguments into a structured format."""
    parser = create_argument_parser()
    args = parser.parse_args()

    return CommandArguments(
        network=args.network,
        output=args.output,
        check_balance=args.check_balance,
        show_qr=args.show_qr,
        address_type=args.address_type,
        privkey=args.privkey,  # This will now match the argument name
        receive=args.receive,
        new_address=args.new_address,
        amount=args.amount,
        message=args.message,
        send=args.send,
        fee_priority=args.fee_priority,
        privacy=args.privacy,
        check_fees=args.check_fees,
        blockchain_info=args.blockchain_info,
        mempool_info=args.mempool_info,
        load=args.load,
        history=args.history,
        limit=args.limit,
        rates=args.rates,
        interactive=args.interactive,
        utxos=args.utxos,
        use_wallet=args.use_wallet,
        use_wallet_file=args.use_wallet_file,
        unload_wallet=args.unload_wallet,
        wallet_info=args.wallet_info,
        address=args.address,
        help=args.help,
        help_command=args.help_command
    )
