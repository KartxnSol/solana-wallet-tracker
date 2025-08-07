import os
import requests

API_KEY = os.getenv("HELIUS_API_KEY")
BASE_URL = f"https://api.helius.xyz/v0"

HEADERS = {"accept": "application/json"}

def get_transaction_history(address: str, limit: int = 5):
    """
    Get the transaction history of a wallet from Helius
    """
    url = f"{BASE_URL}/addresses/{address}/transactions?api-key={API_KEY}&limit={limit}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def is_fresh_wallet(address: str) -> bool:
    """
    Determine if a wallet has zero or only one transaction
    (used for 'fresh wallet' detection)
    """
    try:
        history = get_transaction_history(address, limit=2)
        return len(history) <= 1
    except Exception as e:
        print(f"Error checking fresh wallet status for {address}: {e}")
        return False
