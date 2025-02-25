import os
import subprocess
from typing import List, Dict, Any
import pytest

class TestBase:
    @staticmethod
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

    @pytest.fixture
    def wallet_command(self):
        """Fixture for basic wallet command."""
        return ['--network', 'testnet']

    @pytest.fixture
    def temp_wallet_file(self, tmp_path):
        """Fixture for temporary wallet file."""
        return tmp_path / "test_wallet.json"