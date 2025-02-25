# This file ensures the tests directory is treated as a Python package.
# It can be empty, but we'll add some useful test constants.

TESTNET_ADDRESS = "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx"
MAINNET_ADDRESS = "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
TEST_PRIVATE_KEY = "cVt4o7BGAig1UXywgGSmARhxMdzP5qvQsxKkSsc1XEkw3tDTQFpy"

# Network configurations for testing
TEST_NETWORKS = ['testnet', 'signet']  # Excluding mainnet for safety

# Test data
TEST_AMOUNTS = [0.001, 0.01, 0.1, 1.0]
TEST_MESSAGES = ["Test payment", "Invoice #123", "Donation", None]
TEST_FEE_PRIORITIES = ['high', 'medium', 'low']