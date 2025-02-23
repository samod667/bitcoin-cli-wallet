# wallet/transactions.py

import bitcoin
import requests
from bitcoin.core import CMutableTransaction, CMutableTxIn, CMutableTxOut, COutPoint
from bitcoin.core.script import CScript, SignatureHash, SIGHASH_ALL
from bitcoin.wallet import CBitcoinSecret, P2PKHBitcoinAddress
from typing import Dict, List, Optional
from .network import fetch_utxos, get_recommended_fee_rate

def calculate_tx_size(num_inputs: int, num_outputs: int) -> int:
    """
    Calculate the estimated virtual size of a transaction.
    
    A typical P2PKH transaction has:
    - 4 bytes version
    - 1 byte input count
    - 148 bytes per input (approximate)
    - 1 byte output count
    - 34 bytes per output
    - 4 bytes locktime
    
    Args:
        num_inputs: Number of transaction inputs
        num_outputs: Number of transaction outputs
        
    Returns:
        Estimated transaction size in virtual bytes
    """
    return (
        4 +  # Version
        1 +  # Input count
        (148 * num_inputs) +  # Input size
        1 +  # Output count
        (34 * num_outputs) +  # Output size
        4    # Locktime
    )

def create_payment_request(address: str, amount: Optional[float] = None, 
                         message: Optional[str] = None, network: str = "testnet") -> str:
    """
    Create a Bitcoin payment request URI following BIP21 standard.
    
    This function generates a properly formatted Bitcoin URI that can be used
    for payment requests. The URI includes the address and optional parameters
    for amount and message.
    
    Args:
        address: Bitcoin address to receive payment
        amount: Optional amount in BTC
        message: Optional message/label for the payment
        network: Network type (mainnet, testnet, signet)
    
    Returns:
        A properly formatted Bitcoin URI string
    """
    scheme = "bitcoin:" if network == "mainnet" else "bitcoin-testnet:"
    uri = f"{scheme}{address}"
    
    params = []
    if amount is not None:
        params.append(f"amount={amount}")
    if message is not None:
        params.append(f"message={message}")
    
    if params:
        uri += "?" + "&".join(params)
    
    return uri

def create_and_sign_transaction(from_address: str, from_privkey: str,
                              to_address: str, amount: float, 
                              network: str, fee_priority: str = 'medium') -> bitcoin.core.CTransaction:
    """
    Create and sign a Bitcoin transaction with dynamic fee calculation.
    
    This function creates a transaction with a fee calculated based on:
    1. The estimated transaction size in virtual bytes
    2. Current network fee recommendations
    3. User's priority preference (high, medium, low)
    
    Args:
        from_address: Sender's Bitcoin address
        from_privkey: Sender's private key in WIF format
        to_address: Recipient's Bitcoin address
        amount: Amount to send in BTC
        network: Network type (mainnet, testnet, signet)
        fee_priority: Desired fee priority level (high, medium, low)
        
    Returns:
        A signed CTransaction object ready for broadcast
    """
    # Convert amount to satoshis
    amount_sat = int(amount * 100_000_000)
    
    # Get recommended fee rates
    fee_rates = get_recommended_fee_rate(network)
    fee_rate = fee_rates.get(fee_priority, fee_rates['medium'])
    
    # Fetch available UTXOs
    utxos = fetch_utxos(from_address, network)
    if not utxos:
        raise ValueError("No UTXOs found for this address")
    
    # Sort UTXOs by value for optimal selection
    utxos.sort(key=lambda x: x['value'], reverse=True)
    
    # Select UTXOs and calculate fee
    selected_utxos = []
    total_input = 0
    
    for utxo in utxos:
        selected_utxos.append(utxo)
        total_input += utxo['value']
        
        # Calculate estimated fee for current transaction size
        estimated_size = calculate_tx_size(
            num_inputs=len(selected_utxos),
            num_outputs=2  # Assuming recipient output + change output
        )
        estimated_fee = estimated_size * fee_rate
        
        # Check if we have enough funds
        if total_input >= amount_sat + estimated_fee:
            break
    
    if total_input < amount_sat + estimated_fee:
        raise ValueError(
            f"Insufficient balance. Need {(amount_sat + estimated_fee)/100_000_000} BTC "
            f"(including {estimated_fee/100_000_000} BTC fee)"
        )
    
    # Create transaction inputs
    tx_inputs = []
    private_key = CBitcoinSecret(from_privkey)
    public_key = private_key.pub
    
    for utxo in selected_utxos:
        outpoint = COutPoint(bitcoin.core.lx(utxo['txid']), utxo['vout'])
        tx_in = CMutableTxIn(outpoint)
        tx_inputs.append(tx_in)
    
    # Calculate change amount
    change_amount = total_input - amount_sat - estimated_fee
    
    # Create transaction outputs
    tx_outputs = []
    
    # Output for recipient
    recipient_script = bitcoin.core.standard.CScript.to_p2pkh(
        P2PKHBitcoinAddress(to_address).to_scriptPubKey()
    )
    tx_outputs.append(CMutableTxOut(amount_sat, recipient_script))
    
    # Add change output if significant
    if change_amount >= 546:  # Dust threshold
        change_script = bitcoin.core.standard.CScript.to_p2pkh(
            public_key.to_p2pkh_scriptPubKey()
        )
        tx_outputs.append(CMutableTxOut(change_amount, change_script))
    
    # Create and sign the transaction
    tx = CMutableTransaction(tx_inputs, tx_outputs)
    
    # Sign each input
    for i, utxo in enumerate(selected_utxos):
        script_pubkey = CScript([public_key, bitcoin.core.opcodes.OP_CHECKSIG])
        sighash = SignatureHash(script_pubkey, tx, i, SIGHASH_ALL)
        sig = private_key.sign(sighash) + bytes([SIGHASH_ALL])
        tx.vin[i].scriptSig = CScript([sig, public_key])
    
    return tx

def broadcast_transaction(tx: bitcoin.core.CTransaction, network: str) -> str:
    """
    Broadcast a signed transaction to the Bitcoin network.
    
    This function takes a signed transaction and broadcasts it to the network
    using the Blockstream API. It handles the conversion of the transaction
    to the proper format and manages the API interaction.
    
    Args:
        tx: The signed transaction to broadcast
        network: Network type (mainnet, testnet, signet)
    
    Returns:
        Transaction ID of the broadcast transaction
    """
    api_urls = {
        "mainnet": "https://blockstream.info/api",
        "testnet": "https://blockstream.info/testnet/api",
        "signet": "https://blockstream.info/signet/api"
    }
    
    base_url = api_urls.get(network)
    if not base_url:
        raise ValueError(f"Unsupported network: {network}")
    
    try:
        # Convert transaction to hex
        tx_hex = tx.serialize().hex()
        
        # Broadcast transaction
        response = requests.post(f"{base_url}/tx", data=tx_hex)
        
        if response.status_code == 200:
            return response.text.strip()
        else:
            error_msg = response.text if response.text else f"HTTP {response.status_code}"
            raise Exception(f"Failed to broadcast transaction: {error_msg}")
            
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error while broadcasting transaction: {str(e)}")