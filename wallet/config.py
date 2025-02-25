from dataclasses import dataclass
from typing import Dict, Optional
import json
import os

@dataclass
class NetworkConfig:
    """Configuration for a specific network."""
    api_url: str
    explorer_url: str
    network_type: str
    fee_levels: Dict[str, int]
    address_prefix: str
    
@dataclass
class WalletConfig:
    """Main wallet configuration."""
    network: str
    privacy_enabled: bool = False
    debug_mode: bool = False
    api_timeout: int = 30
    max_fee_rate: int = 100
    dust_threshold: int = 546
    network_configs: Dict[str, NetworkConfig] = None
    
    def __post_init__(self):
        self.network_configs = {
            "mainnet": NetworkConfig(
                api_url="https://blockstream.info/api",
                explorer_url="https://blockstream.info",
                network_type="mainnet",
                fee_levels={
                    'high': 20,
                    'medium': 10,
                    'low': 5
                },
                address_prefix="bc1"
            ),
            "testnet": NetworkConfig(
                api_url="https://blockstream.info/testnet/api",
                explorer_url="https://blockstream.info/testnet",
                network_type="testnet",
                fee_levels={
                    'high': 10,
                    'medium': 5,
                    'low': 1
                },
                address_prefix="tb1"
            ),
            "signet": NetworkConfig(
                api_url="https://blockstream.info/signet/api",
                explorer_url="https://blockstream.info/signet",
                network_type="signet",
                fee_levels={
                    'high': 10,
                    'medium': 5,
                    'low': 1
                },
                address_prefix="tb1"
            )
        }
    
    @property
    def current_network_config(self) -> NetworkConfig:
        """Get configuration for the current network."""
        return self.network_configs[self.network]
    
    def get_api_url(self) -> str:
        """Get API URL for current network."""
        return self.current_network_config.api_url
    
    def get_explorer_url(self) -> str:
        """Get block explorer URL for current network."""
        return self.current_network_config.explorer_url
    
    def get_fee_levels(self) -> Dict[str, int]:
        """Get fee levels for current network."""
        return self.current_network_config.fee_levels

class ConfigManager:
    """Manages wallet configuration loading and saving."""
    
    DEFAULT_CONFIG_PATH = os.path.expanduser("~/.bitcoin_wallet/config.json")
    
    @classmethod
    def load_config(cls, config_path: Optional[str] = None) -> WalletConfig:
        """Load configuration from file or create default."""
        path = config_path or cls.DEFAULT_CONFIG_PATH
        
        if os.path.exists(path):
            with open(path, 'r') as f:
                config_data = json.load(f)
                return WalletConfig(**config_data)
        
        return WalletConfig(network="testnet")
    
    @classmethod
    def save_config(cls, config: WalletConfig, config_path: Optional[str] = None) -> None:
        """Save configuration to file."""
        path = config_path or cls.DEFAULT_CONFIG_PATH
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump({
                'network': config.network,
                'privacy_enabled': config.privacy_enabled,
                'debug_mode': config.debug_mode,
                'api_timeout': config.api_timeout,
                'max_fee_rate': config.max_fee_rate,
                'dust_threshold': config.dust_threshold
            }, f, indent=4)

# Global configuration instance
config = ConfigManager.load_config()