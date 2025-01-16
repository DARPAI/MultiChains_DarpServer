from curl_cffi import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
import urllib.parse
import uuid   

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
        
        log_file = log_dir / "aveai.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        logger.info(f"AveAI Logger initialized. Log file: {log_file}")
        
    except Exception as e:
        fallback_handler = logging.StreamHandler()
        fallback_handler.setLevel(logging.ERROR)
        logger.addHandler(fallback_handler)
        logger.error(f"Failed to initialize logger: {str(e)}")
    
    return logger

logger = setup_logger('AveAIService')

class AveAIService:
    def __init__(self):
        self.base_url = "https://febweb002.com"
        
        # Ensure log directory exists
        log_dir = Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Load proxy configuration from environment variables
        username = os.getenv('PROXY_USERNAME')
        password = os.getenv('PROXY_PASSWORD')
        proxy_host = os.getenv('PROXY_HOST')
        proxy_port = os.getenv('PROXY_PORT')
        
        if not all([username, password]):
            self.logger.warning("Proxy credentials not found in environment variables")
            self.proxies = None
        else:
            proxy_url = f'http://{username}:{password}@{proxy_host}:{proxy_port}'
            self.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
        
        # Generate unique udid
        udid = str(uuid.uuid4())
        timestamp = int(datetime.now().timestamp() * 1000)
        
        self.headers = {
            "Ave-Udid": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0--{timestamp}--{udid}",
            "Sec-Ch-Ua-Platform": "Windows",
            "Lang": "en",
            "Sec-Ch-Ua": '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "X-Auth": os.getenv("AVE_AUTH", ""),
            "Sec-Ch-Ua-Mobile": "?0",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
            "Accept": "application/json, text/plain, */*",
            "Dnt": "1",
            "Origin": "https://ave.ai",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://ave.ai/",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Priority": "u=1, i"
        }

        self.logger = setup_logger(f'AveAIService.{id(self)}')
        self.logger.info(f"Using proxy: {self.proxies}")

    def __enter__(self):
        """Synchronous context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Synchronous context manager exit"""
        # Cleanup resources
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)

    def cleanup(self):
        """Cleanup resources"""
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)

    def get_treasure_list(
        self,
        marketcap_min: int = 100000,
        tvl_min: int = 100000,
        smart_money_buy_count_24h_min: int = 0,
        smart_money_sell_count_24h_min: int = 0,
        page_no: int = 1,
        page_size: int = 50,
        category: str = "hot"
    ) -> List[Dict[str, Any]]:
        """Get treasure list from Ave.ai"""
        try:
            params = {
                "marketcap_min": marketcap_min,
                "tvl_min": tvl_min,
                "pageNO": page_no,
                "pageSize": page_size,
                "category": category
            }
            
            # Only add parameters when value is not 0
            if smart_money_buy_count_24h_min > 0:
                params["smart_money_buy_count_24h_min"] = smart_money_buy_count_24h_min
            if smart_money_sell_count_24h_min > 0:
                params["smart_money_sell_count_24h_min"] = smart_money_sell_count_24h_min
            
            url = f"{self.base_url}/v1api/v4/tokens/treasure/list"
            
            # Print request information
            request_log = (
                f"=== HTTP Request ===\n"
                f"GET {url}?{urllib.parse.urlencode(params)} HTTP/2\n"
                f"Host: {self.base_url.replace('https://', '')}\n"
            )
            request_log += '\n'.join(f"{k}: {v}" for k, v in self.headers.items())
            request_log += "\n\n"  
            self.logger.info(request_log)
            
            # Use synchronous request directly
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                proxies=self.proxies,
                impersonate="chrome124"
            )
            
            response.encoding = 'utf-8'
            
            # Print response information
            response_log = (
                f"\n=== HTTP Response ===\n"
                f"HTTP/2 {response.status_code} {response.reason}\n"
            )
            response_log += '\n'.join(f"{k}: {v}" for k, v in response.headers.items())
            response_log += f"\n\n{response.text}\n"  # Empty line followed by response body
            self.logger.info(response_log)
            
            data = response.json()
            if data.get("status") != 1:
                error_msg = data.get("msg", "Failed to fetch data from Ave.ai")
                raise Exception(error_msg)
            
            formatted_pairs = []
            for pair in data["data"]["data"]:
                formatted_pair = {
                    "id": pair["pair"],
                    "address": pair["target_token"],
                    "chain": pair["chain"],
                    "amm": pair["amm"],
                    "quote_reserve": float(pair["reserve1"]),
                    "initial_liquidity": float(pair["init_tvl"]),
                    "tvl": float(pair["tvl"]),
                    "creator": "",  # Ave.ai API 没有
                    "pool_type_str": pair["amm"],
                    "pool_type": pair["amm"],
                    "quote_symbol": pair["token1_symbol"],
                    "base_token_info": {
                        "symbol": pair["token0_symbol"],
                        "name": pair["token0_symbol"],
                        "logo": pair["token0_logo_url"],
                        "total_supply": 0,  # API 未提供
                        "price": float(pair["current_price_usd"]),
                        "holder_count": int(pair["holders"]),
                        "market_cap": float(pair["market_cap"]),
                        "liquidity": float(pair["tvl"]),
                        "volume": float(pair["volume_u_24h"]),
                        "swaps": int(pair["tx_24h_count"]),
                        "buys": int(pair["buys_tx_24h_count"]),
                        "sells": int(pair["sells_tx_24h_count"]),
                        "is_honeypot": False,  # API 未提供
                        "renounced": False,  # API 未提供
                        "burn_ratio": 0,  # API 未提供
                        "burn_status": "",  # API 未提供
                        "top_10_holder_rate": float(pair["holders_top10_ratio"]),
                        "creator_balance_rate": float(pair["dev_balance_ratio_cur"]),
                        "smart_degen_count": int(pair["smart_money_buy_count_24h"]),
                        "renowned_count": 0,  # API 未提供
                        "social_links": {}  # API 未提供
                    }
                }
                formatted_pairs.append(formatted_pair)
            
            return formatted_pairs
            
        except Exception as error:
            self.logger.error(f"Request failed: {str(error)}")
            raise 