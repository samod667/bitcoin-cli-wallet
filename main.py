import json
import argparse
from wallet import (
    generate_wallet,
    create_payment_request,
    create_and_sign_transaction,
    broadcast_transaction,
    WalletDisplay,
    get_recommended_fee_rate,
    address_manager
)

def parse_args():
    """Set up and handle command-line arguments for our Bitcoin wallet."""
    parser = argparse.ArgumentParser(description="Bitcoin Wallet CLI")
    
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
        choices=["legacy", "segwit", "both"],
        default="both",
        help="Type of address to generate (default: both)"
    )
    parser.add_argument(
        "privkey",
        nargs="?",
        default=None,
        help="Optional private key in WIF format"
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
    tx_group.add_argument(
        "--fee-priority",
        choices=['high', 'medium', 'low'],
        default='medium',
        help="Fee priority level (default: medium)"
    )
    tx_group.add_argument(
        "--privacy",
        action="store_true",
        help="Enable enhanced privacy features"
    )
    parser.add_argument(
        "--check-fees",
        action="store_true",
        help="Check current recommended transaction fees"
    )
    
    return parser.parse_args()

def display_fee_estimate(network: str, fee_priority: str):
    """Display current fee recommendations."""
    fee_rates = get_recommended_fee_rate(network)
    print("\nCurrent Fee Rates (satoshis/vB):")
    print(f"High Priority: {fee_rates['high']} sat/vB")
    print(f"Medium Priority: {fee_rates['medium']} sat/vB")
    print(f"Low Priority: {fee_rates['low']} sat/vB")
    print(f"\nUsing {fee_priority} priority: {fee_rates[fee_priority]} sat/vB")

def save_to_json(filename: str, privkey: str, pubkey: str, 
                mnemonic: str, addresses: list, network: str):
    """Save wallet information to a JSON file."""
    data = {
        "network": network,
        "private_key": privkey,
        "public_key": pubkey,
        "mnemonic": mnemonic,
        "addresses": [
            {
                "index": addr[0],
                "private_key": addr[1],
                "public_key": addr[2],
                "address": addr[3]
            }
            for addr in addresses
        ]
    }
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"\nWallet information saved to {filename}")

def main():
    """Main entry point for our Bitcoin wallet application."""
    args = parse_args()
    
    try:
        if args.check_fees:
            display_fee_estimate(args.network, args.fee_priority or 'medium')
            return

        # Get wallet information
        try:
            # Use 'both' address type when checking balance
            address_type = 'both' if args.check_balance else args.address_type
            result = generate_wallet(args.privkey, args.network, address_type)
            
            if None in result[:3]:
                error_message = result[3]
                print(error_message)
                return
            
            privkey, pubkey, mnemonic, addresses = result
            
        except Exception as e:
            print(f"Failed to generate wallet: {str(e)}")
            return

        if args.receive:
            # Handle receive operation
            if not args.amount and not args.message:
                print("Tip: You can add --amount and --message to create a complete payment request")
            
            # Get receive address (new or reuse)
            if args.new_address and len(addresses) > 1:
                receive_address = address_manager.get_new_address(addresses)
                print("\nUsing new unused address for better privacy")
            else:
                receive_address = addresses[0][3]
            
            try:
                # Create and display payment request
                payment_uri = create_payment_request(
                    receive_address,
                    args.amount,
                    args.message,
                    args.network
                )
                
                WalletDisplay.show_payment_request(
                    receive_address,
                    payment_uri,
                    args.amount,
                    args.message
                )
            except Exception as e:
                print(f"Failed to create payment request: {str(e)}")
            
        elif args.send:
            if not args.amount:
                print("Please specify amount to send using --amount")
                return
            if not args.privkey:
                print("Please provide a private key to send from")
                return
            
            try:
                # Display current fee rates before sending
                display_fee_estimate(args.network, args.fee_priority)
                
                from_address = addresses[0][3]
                
                if args.privacy:
                    print("\nPrivacy features enabled:")
                    print("- Using new address for change")
                    print("- Adding amount randomization")
                    print("- Randomizing fee slightly")
                
                print(f"\nPreparing to send {args.amount} BTC")
                print(f"From: {from_address}")
                print(f"To: {args.send}")
                
                # Create and sign transaction
                tx = create_and_sign_transaction(
                    from_address,
                    args.privkey,
                    args.send,
                    args.amount,
                    args.network,
                    args.fee_priority,
                    addresses if args.privacy else None
                )
                
                # Broadcast the transaction
                tx_id = broadcast_transaction(tx, args.network)
                
                print("\nTransaction sent successfully!")
                print(f"Transaction ID: {tx_id}")
                print(f"Track your transaction: https://blockstream.info/{args.network}/tx/{tx_id}")
                
            except Exception as e:
                print(f"Failed to send transaction: {str(e)}")
            
        else:
            # Regular wallet generation/display
            try:
                WalletDisplay.show_wallet_info(
                    privkey, pubkey, mnemonic, addresses,
                    args.network, args.check_balance, args.show_qr
                )
                
                if args.output:
                    save_to_json(args.output, privkey, pubkey, mnemonic, addresses, args.network)
                    
            except Exception as e:
                print(f"Failed to display wallet information: {str(e)}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()