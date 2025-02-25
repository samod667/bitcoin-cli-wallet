from .test_base import TestBase

class TestQR(TestBase):
    def test_qr_code_generation(self):
        """Test QR code generation for addresses"""
        result = self.run_cli_command(['--network', 'testnet', '--show-qr'])
        
        assert result['success'], f"QR code generation failed: {result['stderr']}"
        assert "QR Code" in result['stdout'], "QR code header not found"
        
        # Check for QR code ASCII art characters
        qr_characters = {'█', '▀', '▄', ' '}
        found_qr_chars = any(c in result['stdout'] for c in qr_characters)
        assert found_qr_chars, "QR code characters not found in output"

    def test_payment_request_qr(self):
        """Test QR code generation for payment requests"""
        result = self.run_cli_command([
            '--network', 'testnet',
            '--receive',
            '--amount', '0.001',
            '--message', 'Test Payment',
            '--show-qr'
        ])
        
        assert result['success'], "Payment request QR generation failed"
        assert "Payment Request Details" in result['stdout'], "Payment details missing"
        assert "QR Code" in result['stdout'], "QR code section missing"