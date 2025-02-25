import re
import pytest
from .test_base import TestBase

class TestTransactions(TestBase):
    def test_payment_request_generation(self):
        """Test generating a payment request"""
        result = self.run_cli_command([
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

    def test_fee_estimation(self):
        """Test fee estimation"""
        result = self.run_cli_command(['--network', 'testnet', '--check-fees'])
        
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
            
    @pytest.mark.parametrize("amount,message", [
        (0.001, "Test payment"),
        (1.0, None),
        (0.00001, "Minimum amount"),
        (10.0, "Large payment")
    ])
    def test_payment_request_variations(self, amount, message):
        """Test payment request generation with different amounts and messages"""
        command = ['--network', 'testnet', '--receive', '--amount', str(amount)]
        if message:
            command.extend(['--message', message])
            
        result = self.run_cli_command(command)
        assert result['success'], f"Payment request generation failed: {result['stderr']}"
        
        # Verify amount in output
        assert f"Amount: {amount} BTC" in result['stdout']
        
        # Verify message if provided
        if message:
            assert f"Message: {message}" in result['stdout']