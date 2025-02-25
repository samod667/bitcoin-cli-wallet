import json
import datetime
from wallet.cli import parse_args
from wallet.commands import create_command
from wallet.exceptions import WalletError
from wallet import generate_wallet
from wallet.interactive import InteractiveWallet

def save_to_json(filename: str, privkey: str, pubkey: str,
                mnemonic: str, addresses: list, network: str):
    """Save wallet information to a JSON file with enhanced metadata."""
    data = {
        "version": "1.0",
        "created_at": datetime.datetime.now().isoformat(),
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
        ],
        "metadata": {
            "total_addresses": len(addresses),
            "address_types": list(set(
                "segwit" if addr[3].startswith(('tb1', 'bc1')) else "legacy" 
                for addr in addresses
            ))
        }
    }
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    
    print(f"\nWallet information saved to {filename}")
    print("WARNING: Keep this file secure and do not share your private key!")

def main():
    """Main entry point for our Bitcoin wallet application."""
    try:
        # Parse command line arguments
        args = parse_args()
        
        # Check if interactive mode is requested
        if args.interactive:
            interactive_wallet = InteractiveWallet(args.network)
            interactive_wallet.run()
            return
            
        # Rest of your existing main function...
        addresses = None
        result = None
        
        # We need wallet generation for these operations
        needs_wallet = (
            args.receive or 
            args.send or 
            args.output or
            not (args.check_fees or args.blockchain_info or args.mempool_info or args.load)
        )
        
        if needs_wallet:
            try:
                # Use 'both' address type when checking balance
                address_type = 'both' if args.check_balance else args.address_type
                result = generate_wallet(args.privkey, args.network, address_type)
                
                if None in result[:3]:
                    error_message = result[3]
                    print(error_message)
                    return
                
                privkey, pubkey, mnemonic, addresses = result
                
                # Save to file if output specified
                if args.output and result:
                    save_to_json(args.output, privkey, pubkey, mnemonic, addresses, args.network)
                
            except Exception as e:
                print(f"Failed to generate wallet: {str(e)}")
                return
        
        # Create and execute the appropriate command
        command = create_command(args, addresses)
        command.execute()
        
    except WalletError as e:
        print(f"Wallet Error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()