import requests
import datetime
from typing import Dict, Union, List

def fetch_address_balance(address: str, network: str) -> Dict[str, Union[int, str, None]]:
    """
    Fetch both confirmed and unconfirmed balance of a Bitcoin address.
    """
    api_urls = {
        "mainnet": "https://blockstream.info/api",
        "testnet": "https://blockstream.info/testnet/api",
        "signet": "https://blockstream.info/signet/api"
    }
    
    base_url = api_urls.get(network)
    if not base_url:
        return {
            "balance": None,
            "error": f"Unsupported network: {network}"
        }

    try:
        response = requests.get(f"{base_url}/address/{address}")
        response.raise_for_status()
        
        data = response.json()
        
        # Calculate confirmed balance
        confirmed_balance_sat = data.get('chain_stats', {}).get('funded_txo_sum', 0) - \
                              data.get('chain_stats', {}).get('spent_txo_sum', 0)
        
        # Calculate unconfirmed balance
        unconfirmed_balance_sat = data.get('mempool_stats', {}).get('funded_txo_sum', 0) - \
                                 data.get('mempool_stats', {}).get('spent_txo_sum', 0)
        
        # Total balance (confirmed + unconfirmed)
        total_balance_sat = confirmed_balance_sat + unconfirmed_balance_sat
        
        # Convert to BTC
        total_balance_btc = total_balance_sat / 100_000_000
        
        # Get transaction counts
        confirmed_tx_count = data.get('chain_stats', {}).get('tx_count', 0)
        unconfirmed_tx_count = data.get('mempool_stats', {}).get('tx_count', 0)
        
        return {
            "balance_sat": total_balance_sat,
            "balance_btc": total_balance_btc,
            "confirmed_balance_btc": confirmed_balance_sat / 100_000_000,
            "unconfirmed_balance_btc": unconfirmed_balance_sat / 100_000_000,
            "tx_count": confirmed_tx_count + unconfirmed_tx_count,
            "confirmed_tx_count": confirmed_tx_count,
            "unconfirmed_tx_count": unconfirmed_tx_count,
            "error": None
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "balance_sat": None,
            "balance_btc": None,
            "tx_count": None,
            "error": f"API request failed: {str(e)}"
        }
def fetch_utxos(address: str, network: str) -> List[Dict]:
    """
    Fetch unspent transaction outputs (UTXOs) for an address.
    
    This function gets the list of unspent outputs that can be used as inputs
    for new transactions.
    """
    api_urls = {
        "mainnet": "https://blockstream.info/api",
        "testnet": "https://blockstream.info/testnet/api",
        "signet": "https://blockstream.info/signet/api"
    }
    base_url = api_urls.get(network)
    
    try:
        response = requests.get(f"{base_url}/address/{address}/utxo")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch UTXOs: {str(e)}")
    
def get_recommended_fee_rate(network: str) -> dict:
    """
    Fetch recommended fee rates from Mempool.space API.
    For testnet, use lower fee rates as the network is less congested.
    """
    # For testnet/signet, use lower fixed fees
    if network in ["testnet", "signet"]:
        return {
            'high': 10,    # 10 sat/vB for high priority
            'medium': 5,   # 5 sat/vB for medium priority
            'low': 1       # 1 sat/vB for low priority
        }
    
    # For mainnet, use the API
    try:
        response = requests.get("https://mempool.space/api/v1/fees/recommended")
        response.raise_for_status()
        
        fee_recommendations = response.json()
        return {
            'high': fee_recommendations.get('fastestFee', 20),
            'medium': fee_recommendations.get('halfHourFee', 10),
            'low': fee_recommendations.get('hourFee', 5)
        }
    except requests.exceptions.RequestException:
        # Fallback fees if API is unreachable
        return {
            'high': 20,
            'medium': 10,
            'low': 5
        }
    
def get_blockchain_info(network: str = "testnet") -> dict:
    """
    Fetch comprehensive blockchain information from Blockstream API.
    
    Args:
        network: Bitcoin network (mainnet, testnet, signet)
    
    Returns:
        Dictionary with blockchain information
    """
    api_urls = {
        "mainnet": "https://blockstream.info/api",
        "testnet": "https://blockstream.info/testnet/api",
        "signet": "https://blockstream.info/signet/api"
    }
    
    base_url = api_urls.get(network, api_urls["testnet"])
    
    try:
        # Fetch block height
        block_height_response = requests.get(f"{base_url}/blocks/tip/height")
        block_height = block_height_response.text
        
        # Fetch block hash
        block_hash_response = requests.get(f"{base_url}/blocks/tip/hash")
        block_hash = block_hash_response.text
        
        return {
            "block_height": int(block_height),
            "block_hash": block_hash
        }
    except Exception as e:
        return {"error": str(e)}

def get_mempool_info(network: str = "testnet") -> dict:
    """
    Fetch detailed network information.
    
    Args:
        network: Bitcoin network (mainnet, testnet, signet)
    
    Returns:
        Dictionary with network statistics
    """
    # Updated API URLs
    api_urls = {
        "mainnet": "https://blockstream.info/api",
        "testnet": "https://blockstream.info/testnet/api",
        "signet": "https://blockstream.info/signet/api"
    }
    
    base_url = api_urls.get(network, api_urls["testnet"])
    
    try:
        # Fetch recent blocks
        recent_blocks_response = requests.get(f"{base_url}/blocks")
        recent_blocks_response.raise_for_status()
        recent_blocks = recent_blocks_response.json()
        
        # Fetch blockchain tip height
        block_height_response = requests.get(f"{base_url}/blocks/tip/height")
        block_height_response.raise_for_status()
        block_height = block_height_response.text
        
        # Fetch blockchain tip hash
        block_hash_response = requests.get(f"{base_url}/blocks/tip/hash")
        block_hash_response.raise_for_status()
        block_hash = block_hash_response.text
        
        return {
            "block_tip": int(block_height),
            "recent_blocks_count": len(recent_blocks),
            "last_block_hash": block_hash,
            "fee_info": "Estimated from Blockstream API"
        }
    
    except requests.RequestException as e:
        return {
            "error": f"Network error: {str(e)}",
            "details": {
                "url": base_url,
                "network": network
            }
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "traceback": str(e)
        }
def fetch_transaction_history(address: str, network: str, limit: int = 10) -> List[Dict]:
    """
    Fetch transaction history for an address with detailed information.
    
    Args:
        address: Bitcoin address to check
        network: Network type (mainnet, testnet, signet)
        limit: Maximum number of transactions to fetch
        
    Returns:
        List of transaction details
    """
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
    
def get_exchange_rates() -> Dict[str, float]:
    """Fetch current Bitcoin exchange rates from CoinGecko API."""
    try:
        response = requests.get("https://api.coingecko.com/api/v3/simple/price",
                              params={
                                  "ids": "bitcoin",
                                  "vs_currencies": "usd,eur,gbp,jpy,cad,aud,cny"
                              })
        response.raise_for_status()
        data = response.json()
        return data.get("bitcoin", {})
    except Exception as e:
        return {"error": f"Failed to fetch exchange rates: {str(e)}"}