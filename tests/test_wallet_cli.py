import os
import json
import re
import pytest
import subprocess
import tempfile
from typing import List, Dict, Any

def run_cli_command(command: List[str]) -> Dict[str, Any]:
    """
    Run CLI command and capture output
    
    Args:
        command: List of command arguments
    
    Returns:
        Dictionary with command results
    """
    try:
        # Ensure 'python' is used to run the script
        full_command = ['python', 'main.py'] + command
        
        # Run the command
        result = subprocess.run(
            full_command, 
            capture_output=True, 
            text=True, 
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        return {
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'success': result.returncode == 0
        }
    except Exception as e:
        return {
            'returncode': 1,
            'stdout': '',
            'stderr': str(e),
            'success': False
        }

def test_segwit_address_generation():
    """Detailed test for SegWit address generation"""
    result = run_cli_command(['--network', 'testnet', '--address-type', 'segwit'])
    
    assert result['success'], f"SegWit address generation failed: {result['stderr']}"
    
    # More flexible SegWit address regex
    segwit_addresses = re.findall(r'(tb1q\w+)', result['stdout'])
    assert len(segwit_addresses) > 0, "No SegWit addresses generated"
    
    # Verify address format
    for address in segwit_addresses:
        assert address.startswith('tb1q'), f"Invalid SegWit address format: {address}"
        assert 42 <= len(address) <= 62, f"Unexpected SegWit address length: {address}"

def test_legacy_address_generation():
    """Detailed test for Legacy address generation"""
    result = run_cli_command(['--network', 'testnet', '--address-type', 'legacy'])
    
    assert result['success'], f"Legacy address generation failed: {result['stderr']}"
    
    # Print entire stdout for debugging
    print("\n--- Full Output ---")
    print(result['stdout'])
    print("--- End of Output ---\n")
    
    # More comprehensive regex to capture legacy addresses
    legacy_addresses = re.findall(r'(m[a-zA-Z0-9]{33,40})', result['stdout'])
    
    print("Found Legacy Addresses:", legacy_addresses)
    
    assert len(legacy_addresses) > 0, "No Legacy addresses generated"
    
    # Verify address format
    for address in legacy_addresses:
        print(f"Checking address: {address}")
        print(f"Address length: {len(address)}")
        print(f"Address prefix: {address[:3]}")
        
        # Verify address starts with valid prefix
        assert address.startswith(('m', 'n', '2', '3', 'mk', 'mn')), f"Invalid Legacy address format: {address}"
        
        # Check first character
        assert address[0] in 'm', f"Invalid first character: {address[0]}"
        
        # Allow a wider range of address lengths
        assert 33 <= len(address) <= 40, f"Unexpected Legacy address length: {address}"
        
        # Additional check for base58 characters (simplified)
        assert all(c in '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz' for c in address[1:]), \
            f"Invalid characters in address: {address}"

def test_payment_request_generation():
    """Test generating a payment request"""
    result = run_cli_command([
        '--network', 'testnet', 
        '--receive', 
        '--amount', '0.001', 
        '--message', 'Test Payment'
    ])
    
    assert result['success'], f"Payment request generation failed: {result['stderr']}"
    
    # Check for key payment request details
    assert "Payment Request Details" in result['stdout'], "Payment request header missing"
    assert "Amount: 0.001 BTC" in result['stdout'], "Payment amount not correctly displayed"
    assert "Message: Test Payment" in result['stdout'], "Payment message not correctly displayed"
    
    # Check for payment URI
    payment_uris = re.findall(r'(bitcoin(?:-testnet)?:[\w-]+\?.*)', result['stdout'])
    assert len(payment_uris) > 0, "No payment URI generated"

def test_fee_estimation():
    """Test fee estimation"""
    result = run_cli_command(['--network', 'testnet', '--check-fees'])
    
    assert result['success'], f"Fee estimation failed: {result['stderr']}"
    
    # Check for fee rate details
    assert "Current Fee Rates" in result['stdout'], "Fee rates header missing"
    
    # Extract fee rates
    fee_rates = re.findall(r'(\w+ Priority): (\d+) sat/vB', result['stdout'])
    assert len(fee_rates) == 3, "Expected 3 fee priority levels"
    
    # Verify fee rates are numeric and reasonable
    for priority, rate in fee_rates:
        rate = int(rate)
        assert 0 < rate < 1000, f"Unreasonable {priority} fee rate: {rate}"

def test_blockchain_info():
    """Detailed test for blockchain information"""
    result = run_cli_command(['--network', 'testnet', '--blockchain-info'])
    
    assert result['success'], f"Blockchain info retrieval failed: {result['stderr']}"
    
    # Check for specific blockchain info elements
    assert "BLOCKCHAIN INFORMATION" in result['stdout'], "Blockchain info header missing"
    
    # Check for block height
    block_height_match = re.search(r'Block Height\s*:\s*(\d+)', result['stdout'])
    assert block_height_match, "Block height not found"
    block_height = int(block_height_match.group(1))
    assert block_height > 0, "Invalid block height"

def test_mempool_info():
    """Detailed test for mempool information"""
    result = run_cli_command(['--network', 'testnet', '--mempool-info'])
    
    assert result['success'], f"Mempool info retrieval failed: {result['stderr']}"
    
    # Check for specific network info elements
    assert "NETWORK INFORMATION" in result['stdout'], "Network info header missing"
    
    # Check for block height
    block_height_match = re.search(r'Current Block Height\s*:\s*(\d+)', result['stdout'])
    assert block_height_match, "Block height not found"
    block_height = int(block_height_match.group(1))
    assert block_height > 0, "Invalid block height"
