from .test_base import TestBase

class TestPrivacy(TestBase):
    def test_new_address_generation(self):
        """Test generation of new addresses for privacy"""
        result = self.run_cli_command([
            '--network', 'testnet',
            '--receive',
            '--new-address',
            '--privacy'
        ])
        
        assert result['success'], "New address generation failed"
        assert "Using new unused address" in result['stdout'], "New address message not found"
        
    def test_amount_randomization(self):
        """Test amount randomization for privacy"""
        # Test send command which implements amount randomization
        result = self.run_cli_command([
            '--network', 'testnet',
            '--send', 'tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx',
            '--amount', '0.1',
            '--privacy',
            '--privkey', 'cVt4o7BGAig1UXywgGSmARhxMdzP5qvQsxKkSsc1XEkw3tDTQFpy'
        ])
        
        assert result['success'], "Amount randomization test failed"
        assert "Adding amount randomization" in result['stdout'], "Amount randomization not enabled"
        
    def test_change_address_management(self):
        """Test change address management for privacy"""
        result = self.run_cli_command([
            '--network', 'testnet',
            '--send', 'tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx',
            '--amount', '0.1',
            '--privacy',
            '--privkey', 'cVt4o7BGAig1UXywgGSmARhxMdzP5qvQsxKkSsc1XEkw3tDTQFpy'
        ])
        
        assert result['success'], "Change address management test failed"
        assert "Using new address for change" in result['stdout'], "Change address feature not found"
        
    def test_privacy_features_enabled(self):
        """Test that privacy features are properly enabled"""
        result = self.run_cli_command([
            '--network', 'testnet',
            '--send', 'tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx',
            '--amount', '0.1',
            '--privacy',
            '--privkey', 'cVt4o7BGAig1UXywgGSmARhxMdzP5qvQsxKkSsc1XEkw3tDTQFpy'
        ])
        
        assert result['success'], "Privacy features test failed"
        # Check for all privacy features
        assert all(msg in result['stdout'] for msg in [
            "Privacy features enabled",
            "Using new address for change",
            "Adding amount randomization",
            "Randomizing fee slightly"
        ]), "Privacy confirmation missing"