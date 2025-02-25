import re
import pytest
from .test_base import TestBase

class TestAddresses(TestBase):
    def test_segwit_address_generation(self):
        """Detailed test for SegWit address generation"""
        result = self.run_cli_command(['--network', 'testnet', '--address-type', 'segwit'])
        
        assert result['success'], f"SegWit address generation failed: {result['stderr']}"
        
        # More flexible SegWit address regex
        segwit_addresses = re.findall(r'(tb1q\w+)', result['stdout'])
        assert len(segwit_addresses) > 0, "No SegWit addresses generated"
        
        # Verify address format
        for address in segwit_addresses:
            assert address.startswith('tb1q'), f"Invalid SegWit address format: {address}"
            assert 42 <= len(address) <= 62, f"Unexpected SegWit address length: {address}"

    def test_legacy_address_generation(self):
        """Detailed test for Legacy address generation"""
        result = self.run_cli_command(['--network', 'testnet', '--address-type', 'legacy'])
        
        assert result['success'], f"Legacy address generation failed: {result['stderr']}"
        
        # Print entire stdout for debugging