import httpx
from web3 import Web3
from typing import Optional, Dict, List, Any
import json

class EtherscanService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.etherscan.io/api"
        self.web3 = Web3()

    async def _make_request(self, params: Dict[str, Any]) -> Dict:
        """Make a request to Etherscan API"""
        params["apikey"] = self.api_key
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params)
            data = response.json()
           #$ print(data)
            
            if data["status"] != "1" or not data.get("result"):
                raise Exception(data.get("message") or "Failed to fetch data from Etherscan")
            
            return data["result"]

    async def get_address_balance(self, address: str) -> Dict[str, Any]:
        """Get ETH balance for an address"""
        try:
            # Validate address format
            if not self.web3.is_address(address):
                raise ValueError("Invalid Ethereum address format")

            # Get balance in Wei
            params = {
               # "chainid": "1",  # Ethereum mainnet
                "module": "account",
                "action": "balance",
                "address": address,
                "tag": "latest",
            }
            
            balance_wei = await self._make_request(params)
         #   print(balance_wei)
            balance_eth = self.web3.from_wei(int(balance_wei), 'ether')
    
            return {
                "address": address,
             #   "balanceWei": balance_wei,
                "balanceInEth":str(balance_eth)
            }
            
        except Exception as error:
            raise Exception(f"Failed to get address balance: {str(error)}")

    async def get_transaction_history(
        self, 
        address: str,
        startblock: int = 0,
        endblock: int = 99999999,
        page: int = 1,
        offset: int = 10,
        sort: str = "desc"
    ) -> List[Dict[str, Any]]:
        """Get transaction history for an address"""
        try:
            if not self.web3.is_address(address):
                raise ValueError("Invalid Ethereum address format")

            params = {
                "chainid": "1",  # Ethereum mainnet
                "module": "account",
                "action": "txlist",
                "address": address,
                "startblock": str(startblock),
                "endblock": str(endblock),
                "page": str(page),
                "offset": str(offset),
                "sort": sort
            }
            
            transactions = await self._make_request(params)
            
            # 格式化返回的交易数据
            formatted_transactions = []
            for tx in transactions:
                formatted_tx = {
                    'blockNumber': tx.get('blockNumber'),
                    'timestamp': tx.get('timeStamp'),
                    'hash': tx.get('hash'),
                    'from': tx.get('from'),
                    'to': tx.get('to'),
                    'value': self.web3.from_wei(int(tx.get('value', '0')), 'ether')
                }
                formatted_transactions.append(formatted_tx)
            
            return formatted_transactions
            
        except Exception as error:
            raise Exception(f"Failed to get transaction history: {str(error)}")

    async def get_token_transfers(
        self, 
        address: str, 
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get ERC20 token transfers for an address"""
        try:
            if not self.web3.is_address(address):
                raise ValueError("Invalid Ethereum address format")

            params = {
                "module": "account",
                "action": "tokentx",
                "address": address,
                "sort": "desc",
                "page": 1,
                "offset": limit or 10
            }
            
            transfers = await self._make_request(params)
            return transfers
            
        except Exception as error:
            raise Exception(f"Failed to get token transfers: {str(error)}")

    async def get_contract_abi(self, address: str) -> Dict[str, Any]:
        """Get contract ABI"""
        try:
            if not self.web3.is_address(address):
                raise ValueError("Invalid Ethereum address format")

            params = {
                "chainid": "1",  # Ethereum mainnet
                "module": "contract",
                "action": "getabi",
                "address": address
            }
            
            abi_str = await self._make_request(params)
            abi_json = json.loads(abi_str)
            return {
                "address": address,
                "abi": abi_json
            }
            
        except Exception as error:
            raise Exception(f"Failed to get contract ABI: {str(error)}")

    async def get_gas_oracle(self) -> Dict[str, str]:
        """Get current gas prices"""
        try:
            params = {
                "module": "gastracker",
                "action": "gasoracle"
            }
            
            gas_data = await self._make_request(params)
            return {
                "safeGwei": gas_data["SafeGasPrice"],
                "proposeGwei": gas_data["ProposeGasPrice"],
                "fastGwei": gas_data["FastGasPrice"]
            }
            
        except Exception as error:
            raise Exception(f"Failed to get gas prices: {str(error)}")

    async def get_ens_name(self, address: str) -> Optional[str]:
        """Get ENS name for an address"""
        try:
            if not self.web3.is_address(address):
                raise ValueError("Invalid Ethereum address format")

      
            return None
            
        except Exception as error:
            raise Exception(f"Failed to get ENS name: {str(error)}") 