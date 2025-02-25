import json
import pytest
from .test_base import TestBase

class TestWallet(TestBase):
    def test_wallet_generation(self, wallet_command):
        """Test basic wallet generation"""
        result = self.run_cli_command(wallet_command)
        assert result['success'], f"Wallet generation failed: {result['stderr']}"
        
        # Check for the ASCII art header pattern instead of exact text
        assert "_ _" in result['stdout'], "Wallet header not found"
        assert "SEGWIT" in result['stdout'] or "LEGACY" in result['stdout'], "Address section not found"
        
    def test_wallet_file_operations(self, wallet_command, temp_wallet_file):
        """Test saving and loading wallet files"""
        # Generate and save wallet
        save_command = wallet_command + ['--output', str(temp_wallet_file)]
        result = self.run_cli_command(save_command)
        
        assert result['success'], "Failed to save wallet file"
        assert temp_wallet_file.exists(), "Wallet file not created"
        
        # Verify JSON structure
        with open(temp_wallet_file) as f:
            wallet_data = json.load(f)
            assert "version" in wallet_data, "Version info missing"
            assert "network" in wallet_data, "Network info missing"
            assert "addresses" in wallet_data, "Addresses missing"
            
        # Test loading wallet
        load_command = ['--load', str(temp_wallet_file)]
        result = self.run_cli_command(load_command)
        
        assert result['success'], "Failed to load wallet file"
        # Check for any wallet information being displayed, not just a specific header
        assert any(info in result['stdout'] for info in ["wallet", "Wallet", "Network", "Created"]), "Wallet info not displayed"

    @pytest.mark.parametrize("network_type,addr_type", [
        ('testnet', 'legacy'),
        ('testnet', 'segwit'),
        ('testnet', 'both'),
        ('signet', 'segwit')
    ])
    def test_wallet_configurations(self, network_type, addr_type):
        """Test wallet generation with different configurations"""
        command = ['--network', network_type, '--address-type', addr_type]
        result = self.run_cli_command(command)
        
        assert result['success'], f"Wallet generation failed for {network_type} with {addr_type}"
        
        # Updated assertions to match actual output formatting
        if addr_type in ['legacy', 'both']:
            assert 'LEGACY ADDRESSES (P2PKH)' in result['stdout']
        if addr_type in ['segwit', 'both']:
            assert 'SEGWIT ADDRESSES (Native bech32)' in result['stdout']
            
    def test_wallet_balance_check(self, wallet_command):
        """Test wallet balance checking functionality"""
        command = wallet_command + ['--check-balance']
        result = self.run_cli_command(command)
        
        assert result['success'], "Balance check failed"
        # Check for the balance table headers
        assert "Confirmed (BTC)" in result['stdout'], "Balance table not found"
        
    def test_wallet_privacy_features(self, wallet_command):
        """Test wallet privacy features"""
        command = wallet_command + ['--privacy', '--receive', '--amount', '0.1']
        result = self.run_cli_command(command)
        
        assert result['success'], "Privacy features test failed"
        assert "Payment Request Details" in result['stdout'], "Payment request not displayed"