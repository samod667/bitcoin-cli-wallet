# main.py

import argparse
from wallet import (
    generate_wallet,
    create_payment_request,
    create_and_sign_transaction,
    broadcast_transaction,
    WalletDisplay,
    get_recommended_fee_rate
)

def parse_args():
    """
    Set up and handle command-line arguments for our Bitcoin wallet.
    This function defines all the possible commands and options our wallet supports.
    """
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
    parser.add_argument(
    "--check-fees",
    action="store_true",
    help="Check current recommended transaction fees"
)
    
    return parser.parse_args()

def display_fee_estimate(network: str, fee_priority: str):
    """
    Display current fee recommendations to help users understand transaction costs.
    """
    fee_rates = get_recommended_fee_rate(network)
    print("\nCurrent Fee Rates (satoshis/vB):")
    print(f"High Priority: {fee_rates['high']} sat/vB")
    print(f"Medium Priority: {fee_rates['medium']} sat/vB")
    print(f"Low Priority: {fee_rates['low']} sat/vB")
    print(f"\nUsing {fee_priority} priority: {fee_rates[fee_priority]} sat/vB")

def main():
    """
    Main entry point for our Bitcoin wallet application.
    Handles command parsing and executes the appropriate wallet functions.
    """
    args = parse_args()
    
    try:
        if args.check_fees:
            display_fee_estimate(args.network, args.fee_priority or 'medium')
            return
        if args.receive:
            # Handle receive operation
            if not args.amount and not args.message:
                print("Tip: You can add --amount and --message to create a complete payment request")
            
            # Generate wallet info
            privkey, pubkey, mnemonic, addresses = generate_wallet(args.privkey, args.network)
            receive_address = addresses[0][3]
            
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
            
        elif args.send:
            if not args.amount:
                raise ValueError("Please specify amount to send using --amount")
            if not args.privkey:
                raise ValueError("Please provide a private key to send from")
            
            # Display current fee rates before sending
            display_fee_estimate(args.network, args.fee_priority)
            
            # Generate wallet info
            privkey, pubkey, mnemonic, addresses = generate_wallet(args.privkey, args.network)
            from_address = addresses[0][3]
            
            print(f"\nPreparing to send {args.amount} BTC")
            print(f"From: {from_address}")
            print(f"To: {args.send}")
            
            # Create and sign transaction with specified fee priority
            tx = create_and_sign_transaction(
                from_address,
                args.privkey,
                args.send,
                args.amount,
                args.network,
                args.fee_priority
            )
            
            # Broadcast the transaction
            tx_id = broadcast_transaction(tx, args.network)
            
            print("\nTransaction sent successfully!")
            print(f"Transaction ID: {tx_id}")
            print(f"Track your transaction: https://blockstream.info/{args.network}/tx/{tx_id}")
            
        else:
            # Regular wallet generation/display
            privkey, pubkey, mnemonic, addresses = generate_wallet(args.privkey, args.network)
            
            WalletDisplay.show_wallet_info(
                privkey, pubkey, mnemonic, addresses,
                args.network, args.check_balance, args.show_qr
            )
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()