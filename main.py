import json
import datetime
from wallet.cli import parse_args
from wallet.commands import create_command
from wallet.exceptions import WalletError
from wallet import generate_wallet
from wallet.interactive import InteractiveWallet
from wallet.wallet_manager import wallet_manager

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
        
        # Handle interactive mode first
        if args.interactive:
            interactive_wallet = InteractiveWallet(args.network)
            interactive_wallet.run()
            return
        
        # Handle wallet creation when specifically requested
        if args.privkey:
            # User wants to import a wallet with a private key
            try:
                result = generate_wallet(args.privkey, args.network)
                if None in result[:3]:
                    print(f"Error: {result[3]}")
                    return
                
                privkey, pubkey, mnemonic, addresses = result
                
                # Load wallet into manager
                wallet_manager.load_wallet(
                    privkey=privkey,
                    network=args.network,
                    addresses=addresses,
                    pubkey=pubkey,
                    encrypt=False
                )
                
                print(f"Wallet imported successfully from private key")
                
                # Save to file if requested
                if args.output:
                    save_to_json(args.output, privkey, pubkey, mnemonic, addresses, args.network)
            except Exception as e:
                print(f"Failed to import wallet: {str(e)}")
                return
        elif args.output and not args.load and not wallet_manager.is_wallet_loaded():
            # User wants to create a new wallet and save it to file
            try:
                result = generate_wallet(None, args.network)
                privkey, pubkey, mnemonic, addresses = result
                
                # Save to file
                save_to_json(args.output, privkey, pubkey, mnemonic, addresses, args.network)
                
                # Load wallet into manager
                wallet_manager.load_wallet(
                    privkey=privkey,
                    network=args.network,
                    addresses=addresses,
                    pubkey=pubkey,
                    encrypt=False
                )
                
                print(f"New wallet created and saved to {args.output}")
            except Exception as e:
                print(f"Failed to create wallet: {str(e)}")
                return
        
        # If no specific action, just status message
        if not any([
            args.check_balance, args.show_qr, args.receive, args.new_address, 
            args.send, args.check_fees, args.blockchain_info, args.mempool_info,
            args.load, args.history, args.rates, args.utxos, args.use_wallet,
            args.use_wallet_file, args.unload_wallet, args.wallet_info, args.address,
            args.help, args.help_command, args.output
        ]):
            if wallet_manager.is_wallet_loaded():
                args = args._replace(wallet_info=True)
            else:
                print("\nNo wallet is currently active and no command specified.")
                print("Use one of these options to get started:")
                print("  --output FILE         Create a new wallet and save to file")
                print("  --privkey KEY         Import wallet from private key")
                print("  --load FILE           Load wallet from file")
                print("  --use-wallet KEY      Use wallet from private key")
                print("  --help                Show comprehensive help")
                print("  --interactive         Start interactive mode")
                return
        
        # Execute the command - all state is managed by command classes
        # which will check wallet_manager for active wallet
        command = create_command(args)
        command.execute()
        
    except WalletError as e:
        print(f"Wallet Error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()