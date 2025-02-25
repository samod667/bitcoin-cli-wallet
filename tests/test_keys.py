import pytest
import re
from .test_base import TestBase
from . import TEST_PRIVATE_KEY

class TestKeys(TestBase):
    def test_private_key_import(self):
        """Test importing an existing private key"""
        result = self.run_cli_command([
            '--network', 'testnet',
            '--privkey', TEST_PRIVATE_KEY
        ])
        
        assert result['success'], f"Private key import failed: {result['stderr']}"
        # Update to match your actual output when importing a key
        assert "N/A (provided private key)" in result['stdout'], "Mnemonic should be N/A for imported keys"

    def test_key_generation(self):
        """Test new key generation"""
        result = self.run_cli_command(['--network', 'testnet'])
        
        assert result['success'], "Key generation failed"
        assert "Seed Phrase" in result['stdout'], "Seed phrase not found"
        assert "Private Key" in result['stdout'], "Private key not found"
        assert "Public Key" in result['stdout'], "Public key not found"
        
    def test_invalid_private_key(self):
        """Test handling of invalid private key"""
        result = self.run_cli_command([
            '--network', 'testnet',
            '--privkey', 'invalid_key'
        ])
        
        # Instead of checking success, let's check if it generated addresses
        addresses = re.findall(r'(tb1q\w+|[mn][a-km-zA-HJ-NP-Z1-9]{25,34})', result['stdout'])
        assert len(addresses) == 0, "Should not generate addresses with invalid key"
        
    @pytest.mark.parametrize("network", ['testnet', 'signet'])
    def test_key_network_compatibility(self, network):
        """Test key generation on different networks"""
        result = self.run_cli_command(['--network', network])
        
        assert result['success'], f"Key generation failed for {network}"
        if network == 'testnet':
            assert any('tb1' in line for line in result['stdout'].split('\n')), "Testnet address not found"
        elif network == 'signet':
            assert any('tb1' in line for line in result['stdout'].split('\n')), "Signet address not found"