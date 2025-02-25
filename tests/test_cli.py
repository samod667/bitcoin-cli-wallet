import pytest
from .test_base import TestBase

class TestCLI(TestBase):
    def test_help_command(self):
        """Test help output"""
        result = self.run_cli_command(['--help'])
        
        assert result['success'], "Help command failed"
        assert "usage:" in result['stdout'], "Help usage section missing"
        assert "Bitcoin Wallet CLI" in result['stdout'], "Help description missing"
        
    def test_invalid_command(self):
        """Test handling of invalid commands"""
        result = self.run_cli_command(['--invalid-option'])
        
        assert not result['success'], "Should fail with invalid option"
        assert "error:" in result['stderr'], "Error message missing"
        
    def test_multiple_operations(self):
        """Test combining multiple operations"""
        result = self.run_cli_command([
            '--network', 'testnet',
            '--check-balance',
            '--show-qr'
        ])
        
        assert result['success'], "Multiple operations failed"
        # Check for both balance and QR code information
        assert "Confirmed (BTC)" in result['stdout'], "Balance check missing"
        assert "Address QR Codes:" in result['stdout'], "QR code missing"
        
    def test_network_parameter(self):
        """Test network parameter validation"""
        # Valid networks
        for network in ['testnet', 'mainnet', 'signet']:
            result = self.run_cli_command(['--network', network])
            assert result['success'], f"Valid network {network} failed"
        
        # Invalid network
        result = self.run_cli_command(['--network', 'invalid'])
        assert not result['success'], "Invalid network should fail"
        
    def test_amount_parameter(self):
        """Test amount parameter validation"""
        result = self.run_cli_command([
            '--network', 'testnet',
            '--receive',
            '--amount', 'invalid'
        ])
        assert not result['success'], "Invalid amount should fail"
        
    def test_address_type_parameter(self):
        """Test address type parameter validation"""
        for addr_type in ['legacy', 'segwit', 'both']:
            result = self.run_cli_command(['--address-type', addr_type])
            assert result['success'], f"Valid address type {addr_type} failed"
            
        result = self.run_cli_command(['--address-type', 'invalid'])
        assert not result['success'], "Invalid address type should fail"
        
    def test_fee_priority_parameter(self):
        """Test fee priority parameter validation"""
        for priority in ['high', 'medium', 'low']:
            result = self.run_cli_command(['--fee-priority', priority])
            assert result['success'], f"Valid fee priority {priority} failed"
            
        result = self.run_cli_command(['--fee-priority', 'invalid'])
        assert not result['success'], "Invalid fee priority should fail"