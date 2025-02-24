import requests
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