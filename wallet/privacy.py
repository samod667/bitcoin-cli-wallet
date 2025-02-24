import random
from typing import List, Tuple, Set

class AddressManager:
    """Manages address generation and tracking for the wallet."""
    def __init__(self):
        self.used_addresses: Set[str] = set()
        
    def mark_address_used(self, address: str):
        """Mark an address as used."""
        self.used_addresses.add(address)
        
    def get_new_address(self, derived_addresses: List[Tuple]) -> str:
        """Get a new unused address."""
        for _, _, _, address in derived_addresses:
            if address not in self.used_addresses:
                self.used_addresses.add(address)
                return address
        raise ValueError("No unused addresses available")
        
    def is_address_used(self, address: str) -> bool:
        """Check if an address has been used."""
        return address in self.used_addresses

def randomize_amount(amount: float, variance_percent: float = 0.1) -> float:
    """Add small random variance to amount to avoid round numbers."""
    if amount == 0:
        return 0
        
    # Convert to satoshis for integer math
    amount_sats = int(amount * 100_000_000)
    
    # Calculate maximum variance in satoshis (0.1% by default)
    max_variance = int(amount_sats * variance_percent / 100)
    
    # Add random variance
    if max_variance > 0:
        variance = random.randint(-max_variance, max_variance)
        amount_sats += variance
    
    # Convert back to BTC
    return amount_sats / 100_000_000

# Create a global address manager instance
address_manager = AddressManager()