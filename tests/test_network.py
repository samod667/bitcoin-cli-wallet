import re
from .test_base import TestBase

class TestNetwork(TestBase):
    def test_blockchain_info(self):
        """Test retrieving blockchain information"""
        result = self.run_cli_command(['--network', 'testnet', '--blockchain-info'])
        
        assert result['success'], f"Blockchain info retrieval failed: {result['stderr']}"
        
        # Check for specific blockchain info elements
        assert "BLOCKCHAIN INFORMATION" in result['stdout'], "Blockchain info header missing"
        
        # Check for block height
        block_height_match = re.search(r'Block Height\s*:\s*(\d+)', result['stdout'])
        assert block_height_match, "Block height not found"
        block_height = int(block_height_match.group(1))
        assert block_height > 0, "Invalid block height"

    def test_mempool_info(self):
        """Test retrieving mempool information"""
        result = self.run_cli_command(['--network', 'testnet', '--mempool-info'])
        
        assert result['success'], f"Mempool info retrieval failed: {result['stderr']}"
        
        # Check for specific network info elements
        assert "NETWORK INFORMATION" in result['stdout'], "Network info header missing"
        
        # Check for block height
        block_height_match = re.search(r'Current Block Height\s*:\s*(\d+)', result['stdout'])
        assert block_height_match, "Block height not found"
        block_height = int(block_height_match.group(1))
        assert block_height > 0, "Invalid block height"
        
    def test_different_networks(self):
        """Test network info retrieval on different networks"""
        networks = ['testnet', 'signet']  # Excluding mainnet for safety
        for network in networks:
            result = self.run_cli_command(['--network', network, '--blockchain-info'])
            assert result['success'], f"Network info failed for {network}: {result['stderr']}"
            
    def test_api_error_handling(self):
        """Test handling of API errors"""
        # Force an error by using an invalid network
        result = self.run_cli_command(['--network', 'invalid', '--blockchain-info'])
        assert not result['success'], "Expected failure for invalid network"
        assert "error" in result['stderr'].lower(), "Error message not found in output"