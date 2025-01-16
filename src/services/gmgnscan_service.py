from curl_cffi import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from typing import Literal, TypedDict
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
import asyncio
from functools import partial

load_dotenv()
def setup_logger(name: str) -> logging.Logger:
    """Set up and configure logger"""
    logger = logging.getLogger(name)
   
    if logger.hasHandlers():
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    try:
        log_dir = Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create file handler - use current module name as log filename
        log_file = log_dir / "gmgnscan.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Configure console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        logger.info(f"GMGNScan Logger initialized. Log file: {log_file}")
        
    except Exception as e:
        # Ensure at least console output is available
        fallback_handler = logging.StreamHandler()
        fallback_handler.setLevel(logging.ERROR)
        logger.addHandler(fallback_handler)
        logger.error(f"Failed to initialize logger: {str(e)}")
    
    return logger


logger = setup_logger('GMGNScanService')

class KlineResolution(str, Enum):
    FIVE_MIN = "5m"
    ONE_HOUR = "1h" 
    FOUR_HOUR = "4h"
    ONE_DAY = "1d"
    ONE_WEEK = "1w"
   # ONE_MONTH = "1m"

class GMGNScanService:
    def __init__(self):
        self.base_url = "https://gmgn.ai"
        
        username = os.getenv('PROXY_USERNAME')
        password = os.getenv('PROXY_PASSWORD')
        proxy_host = os.getenv('PROXY_HOST' )
        proxy_port = os.getenv('PROXY_PORT')
        
        if not all([username, password]):
            self.logger.warning("Proxy credentials not found in environment variables")
            self.proxies = None
        else:
            # Build proxy URL
            proxy_url = f'http://{username}:{password}@{proxy_host}:{proxy_port}'
            
            # Set proxy
            self.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
        
        self.headers = {
     
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-GB,zh;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://gmgn.ai/?chain=sol",
            "Cookie": os.getenv("GMGN_COOKIE", ""),
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "no-cors",
            "Sec-Fetch-Site": "same-origin",
            "Priority": "u=4",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "Te": "trailers"
        }
        self.body = {}

        self.logger = setup_logger(f'GMGNScanService.{id(self)}')
        self.logger.info(f"GMGN_COOKIE: {os.getenv('GMGN_COOKIE', '')}")
        self.logger.info(f"USER_AGENT: {os.getenv('USER_AGENT', '')}")
        self.logger.info(f"Using proxy: {self.proxies}")

    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup resources"""
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)

    async def cleanup(self):
        """Cleanup resources"""
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)

    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict:
        """Make a request to GMGN API"""
        try:
            url = f"{self.base_url}{endpoint}"
            
  
            request_log = f"=== HTTP Request ===\nGET {url} HTTP/1.1\n"
            request_log += '\n'.join(f"{k}: {v}" for k, v in self.headers.items())
            request_log += f"\n\nQuery Parameters: {params}\n"
            self.logger.info(request_log)
            

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                partial(
                    requests.get,
                    url,
                    params=params,
                    headers=self.headers,
                    proxies=self.proxies,
                    impersonate="chrome124",
                    # verify=False  # If SSL verification needs to be disabled
                )
            )
            
            response.encoding = 'utf-8'
        
            response_log = f"=== HTTP Response ===\nHTTP/1.1 {response.status_code} {response.reason}\n"
            response_log += '\n'.join(f"{k}: {v}" for k, v in response.headers.items())
            response_log += f"\n\nResponse Body: {response.text}\n"
            self.logger.info(response_log)
            
            data = response.json()
            if data.get("code") != 0:
                error_msg = (data.get("msg") or "Failed to fetch data from GMGN").encode('utf-8').decode('utf-8')
                raise Exception(error_msg)
            
            return data["data"]
            
        except Exception as error:
            self.logger.error(f"Request failed: {str(error)}")
            raise

    async def get_new_pairs(
        self,
        chain: str = "sol",
        period: str = "1h",
        limit: int = 10,
        min_marketcap: int = 50000,
        min_swaps1h: int = 200,
        min_holder_count: int = 100,
        filters: List[str] = [
            "not_honeypot",
            "pump",
            "renounced",
            "frozen",
            "burn",
            "distribed"
        ],
        launchpad: str = "pump",
        orderby: str = "open_timestamp",
        direction: str = "desc"
    ) -> List[Dict[str, Any]]:
        """Get new trading pairs information
        
        Args:
            chain: Chain name (e.g. sol)
            period: Time period (e.g. 1h)
            limit: Number of pairs to return
            min_marketcap: Minimum market cap in USD
            min_swaps1h: Minimum number of swaps in last hour
            min_holder_count: Minimum number of token holders
            filters: List of filters to apply
            launchpad: Launchpad name
            orderby: Field to order results by
            direction: Sort direction (asc/desc)
        """
        try:
            params = {
                "limit": limit,
                "orderby": orderby,
                "direction": direction,
                "launchpad": launchpad,
                "period": period,
                "filters[]": filters,
                "min_marketcap": min_marketcap,
                "min_swaps1h": min_swaps1h,
                "min_holder_count": min_holder_count
            }
            
            data = await self._make_request(
                f"/defi/quotation/v1/pairs/{chain}/new_pairs/{period}",
                params
            )
         
            formatted_pairs = []
            for pair in data["pairs"]:
                token_info = pair["base_token_info"]
                formatted_pair = {
                    "id": pair["id"],
                   # "address": pair["address"],
                    "address": pair["base_address"],
                  #  "quote_address": pair["quote_address"],
                    "quote_reserve": pair["quote_reserve"],
                    "initial_liquidity": pair["initial_liquidity"],
                    "initial_quote_reserve": pair["initial_quote_reserve"],
                    "creator": pair["creator"],
                    "pool_type_str": pair["pool_type_str"],
                    "pool_type": pair["pool_type"],
                    "quote_symbol": pair["quote_symbol"],
                    "base_token_info": {
                        "symbol": token_info["symbol"],
                        "name": token_info["name"],
                        "logo": token_info.get("logo"),
                        "total_supply": token_info["total_supply"],
                        "price": token_info["price"],
                        "holder_count": token_info["holder_count"],
                        "launchpad_status": token_info.get("launchpad_status"),
                        "price_change_percent1m": token_info.get("price_change_percent1m"),
                        "price_change_percent5m": token_info.get("price_change_percent5m"),
                        "price_change_percent1h": token_info.get("price_change_percent1h"),
                        "burn_ratio": token_info.get("burn_ratio"),
                        "burn_status": token_info.get("burn_status"),
                        "is_show_alert": token_info.get("is_show_alert", False),
                        "hot_level": token_info.get("hot_level", 0),
                        "liquidity": token_info["liquidity"],
                        "top_10_holder_rate": token_info.get("top_10_holder_rate"),
                        "renounced_mint": token_info.get("renounced_mint"),
                        "renounced_freeze_account": token_info.get("renounced_freeze_account"),
                        "market_cap": token_info.get("market_cap"),
                        "creator_balance_rate": token_info.get("creator_balance_rate"),
                        "creator_token_status": token_info.get("creator_token_status"),
                        "rat_trader_amount_rate": token_info.get("rat_trader_amount_rate"),
                        "bluechip_owner_percentage": token_info.get("bluechip_owner_percentage"),
                        "smart_degen_count": token_info.get("smart_degen_count"),
                        "renowned_count": token_info.get("renowned_count"),
                        "volume": token_info.get("volume"),
                        "swaps": token_info.get("swaps"),
                        "buys": token_info.get("buys"),
                        "sells": token_info.get("sells"),
                        "buy_tax": token_info.get("buy_tax"),
                        "sell_tax": token_info.get("sell_tax"),
                        "is_honeypot": token_info.get("is_honeypot"),
                        "renounced": token_info.get("renounced"),
                        "dev_token_burn_amount": token_info.get("dev_token_burn_amount"),
                        "dev_token_burn_ratio": token_info.get("dev_token_burn_ratio"),
                        "dexscr_ad": token_info.get("dexscr_ad"),
                        "dexscr_update_link": token_info.get("dexscr_update_link"),
                        "cto_flag": token_info.get("cto_flag"),
                        "twitter_change_flag": token_info.get("twitter_change_flag"),
                        "address": token_info.get("address"),
                        "social_links": token_info.get("social_links", {})
                    },
                    "open_timestamp": pair["open_timestamp"],
                    "launchpad": pair.get("launchpad")
                }
                formatted_pairs.append(formatted_pair)
            
            # Update logging to use logger and write to file
            self.logger.info("New pairs data retrieved:")
            for pair in formatted_pairs:
                self.logger.info(
                    f"""
                    Pair Details:
                    Address: {pair['address']}
                    Token: {pair['base_token_info']['name']} ({pair['base_token_info']['symbol']})
                    Price: ${pair['base_token_info']['price']}
                    Market Cap: ${pair['base_token_info']['market_cap']}
                    Liquidity: ${pair['base_token_info']['liquidity']}
                    Volume: ${pair['base_token_info']['volume']}
                    Holders: {pair['base_token_info']['holder_count']}
                    Open Timestamp: {pair['open_timestamp']}
                    Buy Tax: {pair['base_token_info']['buy_tax']}%
                    Sell Tax: {pair['base_token_info']['sell_tax']}%
                    Is Honeypot: {pair['base_token_info']['is_honeypot']}
                    Renounced: {pair['base_token_info']['renounced']}
                    Burn Ratio: {pair['base_token_info']['burn_ratio']}%
                    Burn Status: {pair['base_token_info']['burn_status']}
                    Top 10 Holder Rate: {pair['base_token_info']['top_10_holder_rate']}%
                    Creator Balance Rate: {pair['base_token_info']['creator_balance_rate']}%
                    Creator Token Status: {pair['base_token_info']['creator_token_status']}
                    Smart Degen Count: {pair['base_token_info']['smart_degen_count']}
                    Renowned Count: {pair['base_token_info']['renowned_count']}
                    Social Links: {pair['base_token_info']['social_links']}
                    """
                )
            return formatted_pairs
            
        except Exception as error:
            self.logger.error(f"Failed to get new pairs: {str(error)}")
            raise Exception(f"Failed to get new pairs: {str(error)}") 

    async def get_token_kline(
        self,
        chain: str,
        token_address: str,
        resolution: KlineResolution,
        from_time: int,
        to_time: int
    ) -> List[Dict[str, Any]]:
        """Get token kline data
        
        Args:
            chain: Chain name (e.g. sol)
            token_address: Token address
            resolution: Kline resolution (5m, 1h, 4h, 1d, 1w )
            from_time: Start timestamp
            to_time: End timestamp
        """
        try:
            params = {
                "resolution": resolution,
                "from": from_time,
                "to": to_time
            }
            
            data = await self._make_request(
                f"/api/v1/token_kline/{chain}/{token_address}",
                params
            )

            self.logger.info(
                f"""
                Token kline data retrieved:
                Token: {token_address}
                Chain: {chain}
                Resolution: {resolution}
                Time range: {from_time} to {to_time}
                Data points: {len(data['list'])}
                """
            )
            return data["list"]
            
        except Exception as error:
            self.logger.error(f"Failed to get token kline: {str(error)}")
            raise Exception(f"Failed to get token kline: {str(error)}") 

    class TokenInfo(TypedDict):
        address: str
        token_address: str
        symbol: str
        name: str
        decimals: int
        logo: str
        price_change_6h: str
        is_show_alert: bool
        is_honeypot: Optional[bool]

    class HoldingInfo(TypedDict):
        token: 'GMGNScanService.TokenInfo'
        balance: str
        usd_value: str
        realized_profit_30d: str
        realized_profit: str
        realized_pnl: str
        realized_pnl_30d: str
        unrealized_profit: str
        unrealized_pnl: str
        total_profit: str
        total_profit_pnl: str
        avg_cost: str
        avg_sold: str
        buy_30d: int
        sell_30d: int
        sells: int
        price: str
        cost: str
        position_percent: str
        last_active_timestamp: int
        history_sold_income: str
        history_bought_cost: str

    async def get_wallet_holdings(
        self,
        chain: str,
        address: str,
        limit: int = 10,
        orderby: str = "last_active_timestamp",
        direction: str = "desc",
        showsmall: bool = False,
        sellout: bool = False,
        hide_abnormal: bool = False
    ) -> List[HoldingInfo]:
        """Get wallet token holdings"""
        try:
            params = {
                "limit": limit,
                "orderby": orderby,
                "direction": direction,
                "showsmall": str(showsmall).lower(),
                "sellout": str(sellout).lower(),
                "hide_abnormal": str(hide_abnormal).lower()
            }
            data = await self._make_request(f"/api/v1/wallet_holdings/{chain}/{address}", params)
            return data["holdings"]
        except Exception as error:
            self.logger.error(f"Failed to get wallet holdings: {str(error)}")
            raise Exception(f"Failed to get wallet holdings: {str(error)}") 

    class TokenSecurityInfo(TypedDict):
        address: str
        is_show_alert: bool
        top_10_holder_rate: str
        renounced_mint: bool
        renounced_freeze_account: bool
        burn_ratio: str
        burn_status: str
        dev_token_burn_amount: str
        dev_token_burn_ratio: str
 
        
    async def get_token_security(self, chain: str, token_address: str) -> TokenSecurityInfo:
        """Get token security information"""
        try:
            data = await self._make_request(f"/api/v1/token_security_{chain}/{chain}/{token_address}", {})
            self.logger.info(f"Token security data retrieved for {token_address}: {data}")
            
            # Ensure all keys are present, using .get() with default None
            security_info = {
                "address": data.get("address"),
                "is_show_alert": data.get("is_show_alert"),
                "top_10_holder_rate": data.get("top_10_holder_rate"),
                "renounced_mint": data.get("renounced_mint"),
                "renounced_freeze_account": data.get("renounced_freeze_account"),
                "burn_ratio": data.get("burn_ratio"),
                "burn_status": data.get("burn_status"),
                "dev_token_burn_amount": data.get("dev_token_burn_amount"),
                "dev_token_burn_ratio": data.get("dev_token_burn_ratio"),
           
            }
            
            return security_info
        except Exception as error:
            self.logger.error(f"Failed to get token security info for {token_address}: {str(error)}")
            raise Exception(f"Failed to get token security info for {token_address}: {str(error)}") 