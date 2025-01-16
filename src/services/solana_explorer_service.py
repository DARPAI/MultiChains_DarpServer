import httpx
import json
from typing import Optional, Dict, List, Any
import uuid   
class SolanaExplorerService:
    def __init__(self):
        self.base_url = "https://explorer-api.mainnet-beta.solana.com/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
            "Accept": "*/*",
            "Accept-Language": "en-GB,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://explorer.solana.com/",
            "Content-Type": "application/json",
            "Solana-Client": "js/1.0.0-maintenance",
            "Origin": "https://explorer.solana.com",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Priority": "u=4",
            "Te": "trailers"
        }

    async def get_multiple_accounts(self, addresses: List[str]) -> Dict[str, Any]:
        payload = {
            "method": "getMultipleAccounts",
            "jsonrpc": "2.0",
            "params": [addresses, {"encoding": "jsonParsed", "commitment": "confirmed"}],
            "id": str(uuid.uuid4())  
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(self.base_url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def get_address_balance(self, address: str) -> Dict[str, Any]:
        data = await self.get_multiple_accounts([address])
        if not data or not data.get("result") or not data["result"].get("value") or not data["result"]["value"][0]:
            return None
        
        account_data = data["result"]["value"][0]
        balance = account_data.get("lamports", 0)
        
        return {
            "address": address,
            "balance": str(float(balance) / 1000000000)
        } 