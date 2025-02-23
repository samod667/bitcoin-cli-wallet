# wallet/network.py

import requests
from typing import Dict, Union, List

def fetch_address_balance(address: str, network: str) -> Dict[str, Union[int, str, None]]:
    """
    Fetch the balance of a Bitcoin address using Blockstream's Esplora API.
    
    This function queries the Blockstream API to get the current balance and
    transaction count for a Bitcoin address. It handles both mainnet and testnet
    addresses.
    
    Args:
        address: The Bitcoin address to check
        network: Network type (mainnet, testnet, signet)
    
    Returns:
        Dictionary containing balance information and status
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
        
        balance_sat = data.get('chain_stats', {}).get('funded_txo_sum', 0) - \
                     data.get('chain_stats', {}).get('spent_txo_sum', 0)
        balance_btc = balance_sat / 100_000_000
        
        tx_count = data.get('chain_stats', {}).get('tx_count', 0)
        
        return {
            "balance_sat": balance_sat,
            "balance_btc": balance_btc,
            "tx_count": tx_count,
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
    
    This function queries the Mempool.space API to get current fee recommendations
    for different priority levels. The API provides fee estimates for various
    confirmation target times:
    - High priority: Targeting next block (10 minutes)
    - Medium priority: Targeting 3 blocks (30 minutes)
    - Low priority: Targeting 6 blocks (1 hour)
    
    Args:
        network: Bitcoin network to use (mainnet, testnet, signet)
        
    Returns:
        Dictionary containing fee rates in sat/vB for different priority levels
    """
    api_urls = {
        "mainnet": "https://mempool.space/api/v1/fees/recommended",
        "testnet": "https://mempool.space/testnet/api/v1/fees/recommended",
        "signet": "https://mempool.space/signet/api/v1/fees/recommended"
    }
    
    try:
        response = requests.get(api_urls.get(network))
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