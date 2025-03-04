import bitcoin
import requests
import random
from bitcoin.core import CMutableTransaction, CMutableTxIn, CMutableTxOut, COutPoint, CTxWitness, CTxInWitness
from bitcoin.core.script import CScript, SignatureHash, SIGHASH_ALL, OP_0, OP_HASH160, OP_EQUAL, SIGVERSION_WITNESS_V0
from bitcoin.core.script import OP_DUP, OP_HASH160, OP_EQUALVERIFY, OP_CHECKSIG
from bitcoin.wallet import CBitcoinSecret, P2PKHBitcoinAddress, CBech32BitcoinAddress
from bitcoin.core import Hash160
from typing import Dict, List, Optional, Tuple
from .network import fetch_utxos, get_recommended_fee_rate
from .privacy import address_manager, randomize_amount

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

def is_segwit_address(address: str) -> bool:
    """Check if an address is a SegWit address."""
    return True  # All addresses are SegWit now

def calculate_tx_size(num_inputs: int, num_outputs: int, is_segwit: bool = True) -> int:
    """
    Calculate the estimated virtual size of a transaction.
    
    For SegWit transactions:
    - Base size: version(4) + input count(1) + inputs(36*n) + output count(1) + outputs(32*m) + locktime(4)
    - Witness size: (signature(72) + pubkey(33))*n
    - Virtual size = (base size * 4 + witness size) / 4
    """
    if is_segwit:
        base_size = (
            4 +  # Version
            1 +  # Input count
            (36 * num_inputs) +  # Input size (without script)
            1 +  # Output count
            (32 * num_outputs) +  # Output size
            4    # Locktime
        )
        witness_size = (72 + 33) * num_inputs  # signature + pubkey per input
        return (base_size * 4 + witness_size) // 4
    else:
        return (
            4 +  # Version
            1 +  # Input count
            (148 * num_inputs) +  # Legacy input size
            1 +  # Output count
            (34 * num_outputs) +  # Output size
            4    # Locktime
        )

def create_and_sign_transaction(from_address: str, from_privkey: str,
                              to_address: str, amount: float, 
                              network: str, fee_priority: str = 'medium',
                              derived_addresses: List[Tuple] = None) -> bitcoin.core.CTransaction:
    """
    Create and sign a Bitcoin transaction with improved privacy and SegWit support.
    """
    # Randomize the amount slightly to avoid round numbers
    actual_amount = randomize_amount(amount)
    amount_sat = int(actual_amount * 100_000_000)
    
    # Mark the sending address as used
    address_manager.mark_address_used(from_address)
    
    # Determine if we're using SegWit - now all addresses are SegWit
    is_segwit_from = True  # Added this line - was missing before
    
    # Get recommended fee rates with small random adjustment
    fee_rates = get_recommended_fee_rate(network)
    base_fee_rate = fee_rates.get(fee_priority, fee_rates['medium'])
    fee_rate = base_fee_rate + random.randint(-1, 1)  # Add slight randomness
    
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
        
        # Calculate estimated fee
        estimated_size = calculate_tx_size(
            num_inputs=len(selected_utxos),
            num_outputs=2,  # Assuming recipient output + change output
            is_segwit=is_segwit_from
        )
        estimated_fee = estimated_size * fee_rate
        
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
    #print("Public key length:", len(public_key))

    
    for utxo in selected_utxos:
        outpoint = COutPoint(bitcoin.core.lx(utxo['txid']), utxo['vout'])
        tx_in = CMutableTxIn(outpoint)
        tx_inputs.append(tx_in)
    
    # Calculate change amount
    change_amount = total_input - amount_sat - estimated_fee
    
    # Create transaction outputs
    tx_outputs = []
    
    # Create recipient output - directly parse Bech32 address
    if to_address.startswith(('tb1', 'bc1')):
        # This is already a Bech32 address, use it directly
        try:
            recipient_addr = bitcoin.wallet.CBitcoinAddress(to_address)
            recipient_script = recipient_addr.to_scriptPubKey()
        except Exception:
            # If direct parsing fails, try to decode it as a Bech32 address
            hrp = "bc" if network == "mainnet" else "tb"
            decoded = bitcoin.bech32.decode(hrp, to_address)
            if decoded[0] is None:
                raise ValueError(f"Invalid Bech32 address: {to_address}")
            witness_version, witness_program = decoded
            recipient_script = CScript([OP_0, witness_program])
    else:
        # For legacy addresses (though we don't generate these anymore)
        recipient_addr = P2PKHBitcoinAddress(to_address)
        recipient_script = recipient_addr.to_scriptPubKey()
    
    tx_outputs.append(CMutableTxOut(amount_sat, recipient_script))
    
    # Add change output if significant
    if change_amount >= 546:  # Dust threshold
        # Get a fresh change address if privacy is enabled
        if derived_addresses:
            change_address = address_manager.get_new_address(derived_addresses)
            print(f"Using new change address: {change_address}")
        else:
            change_address = from_address
            
        # Randomize change amount slightly
        change_amount = int(randomize_amount(change_amount / 100_000_000) * 100_000_000)
        
        # Create change output - must handle SegWit addresses properly
        if change_address.startswith(('tb1', 'bc1')):
            # This is already a Bech32 address, use it directly
            try:
                change_addr = bitcoin.wallet.CBitcoinAddress(change_address)
                change_script = change_addr.to_scriptPubKey()
            except Exception:
                # If direct parsing fails, try to decode it as a Bech32 address
                hrp = "bc" if network == "mainnet" else "tb"
                decoded = bitcoin.bech32.decode(hrp, change_address)
                if decoded[0] is None:
                    raise ValueError(f"Invalid Bech32 address: {change_address}")
                witness_version, witness_program = decoded
                change_script = CScript([OP_0, witness_program])
        else:
            # For legacy addresses (though we don't generate these anymore)
            change_addr = P2PKHBitcoinAddress(change_address)
            change_script = change_addr.to_scriptPubKey()
            
        tx_outputs.append(CMutableTxOut(change_amount, change_script))
    
    # Create transaction
    tx = CMutableTransaction(tx_inputs, tx_outputs)
    
    # Sign each input
    witness = CTxWitness()
    
    signatures = []
    for i, utxo in enumerate(selected_utxos):
        witness_script = CScript([OP_DUP, OP_HASH160, Hash160(public_key), OP_EQUALVERIFY, OP_CHECKSIG])
        sighash = SignatureHash(witness_script, tx, i, SIGHASH_ALL, 
                                amount=utxo['value'], sigversion=SIGVERSION_WITNESS_V0)
        sig = private_key.sign(sighash) + bytes([SIGHASH_ALL])
        signatures.append(sig)
        
        witness.vtxinwit.append(CTxInWitness(CScript([sig, public_key])))
        tx.vin[i].scriptSig = CScript()
        
        # Set the witness data
        tx.wit = witness
    
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