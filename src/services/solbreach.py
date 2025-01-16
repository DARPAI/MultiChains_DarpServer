import httpx
import json
from typing import Optional, Dict, List, Any

class SolbeachService:
    def __init__(self):
        self.base_url = "https://public-api.solanabeach.io/v1"
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


    async def get_account_info(self, address: str):
        url = f"{self.base_url}/account/{address}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def get_address_balance(self, address: str) -> Dict[str, Any]:
        data = await self.get_account_info(address)
        if not data:
            return {"address": address, "balance": 0}
        
        formatted_data = {
            "type": "system",
            "value": {
                "base": {
                    "address": {
                        "address": data["address"]
                    },
                    "balance": str(float(data["balance"]) / 100000000),
                    "executable": data["executable"],
                    "owner": {
                        "name": data["owner"]["name"],
                        "address": data["owner"]["address"]
                    },
                    "rentEpoch": data["rentEpoch"],
                    "dataSize": data["dataSize"],
                    "rentExemptReserve": data["rentExemptReserve"]
                },
                "extended": {}
            }
        }
        
        return { "address": address, "balance": formatted_data["value"]["base"]["balance"]}