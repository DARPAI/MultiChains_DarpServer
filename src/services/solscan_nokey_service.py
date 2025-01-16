import httpx
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import os
from pathlib import Path
#this service is not used anymore

log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    filename=log_dir / "solscan.log",
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger('SolscanService')

class SolscanService:
    def __init__(self):
        self.base_url = "https://pro-api.solscan.io"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "application/json",
        
        }

    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict:
        """Make a request to Solscan API"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{endpoint}",
                params=params,
                headers=self.headers
            )
            response.encoding = 'utf-8'
            data = response.json()
            
            if not data.get("success"):
                error_msg = (data.get("message") or "Failed to fetch data from Solscan").encode('utf-8').decode('utf-8')
                raise Exception(error_msg)
            
            return data["data"]

    async def get_account_transfers(
        self,
        address: str,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "block_time",
        sort_order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """Get account transfer history
        
        Args:
            page: Page number
            page_size: Number of items per page
            sort_by: Field to sort by
            sort_order: Sort direction (asc/desc)
        """
        try:
            params = {
                "address": address,
                "page": page,
                "page_size": page_size,
                "sort_by": sort_by,
                "sort_order": sort_order
            }
            
            data = await self._make_request(
                "/v2.0/account/transfer",
                params
            )

            logger.info(
                f"""
                Account transfers request:
                Address: {address}
                Page: {page}
                Page size: {page_size}
                Sort by: {sort_by}
                Sort order: {sort_order}
                """
            )

            formatted_transfers = []
            for transfer in data:
                formatted_transfer = {
                    "block_id": transfer["block_id"],
                    "transaction_id": transfer["trans_id"],
                    "timestamp": transfer["block_time"],
                    "datetime": transfer["time"],
                    "type": transfer["activity_type"],
                    "from": transfer["from_address"],
                    "to": transfer["to_address"],
                    "token": transfer["token_address"],
                    "decimals": transfer["token_decimals"],
                    "amount": transfer["amount"],
                    "direction": transfer["flow"]
                }
                formatted_transfers.append(formatted_transfer)
                
                logger.info(
                    f"""
                    Transfer Details:
                    Transaction ID: {formatted_transfer['transaction_id']}
                    From: {formatted_transfer['from']}
                    To: {formatted_transfer['to']}
                    Amount: {formatted_transfer['amount']}
                    Type: {formatted_transfer['type']}
                    Direction: {formatted_transfer['direction']}
                    Timestamp: {formatted_transfer['datetime']}
                    """
                )
            
            return formatted_transfers
            
        except Exception as error:
            logger.error(f"Failed to get account transfers: {str(error)}")
            raise Exception(f"Failed to get account transfers: {str(error)}") 