from pydantic import BaseModel, Field
from typing import Optional, List
from services.etherscan_service import EtherscanService
from services.gmgnscan_service import GMGNScanService
from services.solscan_nokey_service import SolscanService
from services.solana_explorer_service import SolanaExplorerService
from services.solbreach import SolbeachService
import os
from dotenv import load_dotenv
from typing import Any
import asyncio
import httpx
import time
from mcp.server.models import InitializationOptions
from mcp.types import (
    ClientCapabilities,
    TextContent,
    Tool,
    ListRootsResult,
    RootsCapability,
    CallToolResult
    
)
from mcp.server import NotificationOptions, Server

import json
from enum import Enum
from datetime import datetime
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route,Mount
from starlette.requests import Request
from mcp.server.sse import SseServerTransport
from starlette.responses import Response
from services.aveai_service import AveAIService
 


load_dotenv(dotenv_path=".env")
 

server = Server("ethser")

USER_AGENT = "ethser-app/1.0"

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
 

if not ETHERSCAN_API_KEY:
    raise ValueError("ETHERSCAN_API_KEY environment variable is required")

etherscan_service = EtherscanService(api_key=ETHERSCAN_API_KEY)
gmgnscan_service = GMGNScanService()
solscan_service = SolscanService()
solbeach_service = SolbeachService()
solana_explorer_service = SolanaExplorerService()

class CheckBalanceInput(BaseModel):
    address: str = Field(..., description="Ethereum address (0x format)", pattern=r"^0x[a-fA-F0-9]{40}$")

class TransactionHistoryInput(BaseModel):
    address: str = Field(..., description="Ethereum address (0x format)", pattern=r"^0x[a-fA-F0-9]{40}$")
    startblock: Optional[int] = Field(0, description="Starting block number")
    endblock: Optional[int] = Field(99999999, description="Ending block number")
    page: Optional[int] = Field(1, ge=1, description="Page number")
    offset: Optional[int] = Field(10, ge=1, le=100, description="Number of transactions per page")
    sort: Optional[str] = Field("desc", description="Sort by 'asc' or 'desc'")

class TokenTransferInput(BaseModel):
    address: str = Field(..., description="Ethereum address (0x format)", pattern=r"^0x[a-fA-F0-9]{40}$")
 #   limit: Optional[int] = Field(Query(None, ge=1, le=100), description="Number of transfers to return (max 100)")

class ContractInput(BaseModel):
    address: str = Field(..., description="Contract address (0x format)", pattern=r"^0x[a-fA-F0-9]{40}$")

class ENSNameInput(BaseModel):
    address: str = Field(..., description="Ethereum address (0x format)", pattern=r"^0x[a-fA-F0-9]{40}$")

class SolbeachAccountInput(BaseModel):
    address: str = Field(..., description="Solana address")

class SolanaExplorerAccountInput(BaseModel):
    address: str = Field(..., description="Solana address")

class GetWalletHoldingsInput(BaseModel):
    chain: str = Field(default="sol", description="Chain name (e.g. sol)")
    address: str = Field(..., description="Wallet address")
    limit: int = Field(default=10, ge=1, le=100, description="Number of holdings to return")
    orderby: str = Field(default="last_active_timestamp", description="Field to order results by")
    direction: str = Field(default="desc", description="Sort direction (asc/desc)")
    showsmall: bool = Field(default=False, description="Show small holdings")
    sellout: bool = Field(default=False, description="Show sold out tokens")
    hide_abnormal: bool = Field(default=True, description="Hide abnormal tokens")

class GetNewPairsInput(BaseModel):
    chain: str = Field(default="sol", description="Chain name (e.g. sol)")
    period: str = Field(default="1h", description="Time period (e.g. 1h)")
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of pairs to return"
    )
    min_marketcap: int = Field(
        default=50000,
        description="Minimum market cap in USD"
    )
    min_swaps1h: int = Field(
        default=200,
        description="Minimum number of swaps in last hour"
    )
    min_holder_count: int = Field(
        default=100,
        description="Minimum number of token holders"
    )
    filters: List[str] = Field(
        default=[
            "not_honeypot",
            "pump",
            "renounced",
            "frozen",
            "burn",
            "distribed"
        ],
        description="List of filters to apply"
    )

    #     PRICE_CHANGE_1H = "price_change_percent1h"
    # PRICE_CHANGE_5M = "price_change_percent5m"
    # PRICE_CHANGE_1M = "price_change_percent1m"
    # MARKET_CAP = "market_cap"
    # LIQUIDITY = "liquidity"
    # VOLUME = "volume"
    # HOLDER_COUNT = "holder_count"
    # SWAPS = "swaps"
    # OPEN_TIMESTAMP = "open_timestamp"
    # PRICE = "price"
    orderby: str  = Field(
        default="holder_count",
        description="Field to order results by"
    )
    direction: str = Field(
    #         ASC = "asc"
    # DESC = "desc"
        default="asc",
        description="Sort direction"
    )

    class Config:
        use_enum_values = True

 

class GetTokenKlineInput(BaseModel):
    chain: str = Field(default="sol", description="Chain name (e.g. sol)")
    token_address: str = Field(..., description="Token address")
    # FIVE_MIN = "5m"
    # ONE_HOUR = "1h"
    # FOUR_HOUR = "4h"
    # ONE_DAY = "1d"
    # ONE_WEEK = "1w"
    resolution: str = Field(
        default="1w",
        description="Kline period (5m, 1h, 4h, 1d, 1w)"
    )
   # from_time: int = Field(..., description="Start timestamp")
   # to_time: int = Field(..., description="End timestamp")

    class Config:
        use_enum_values = True

class GetSOLTransfersInput(BaseModel):
    address: str = Field(..., description="Solana address")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=10, ge=1, le=50, description="Number of items per page")
    sort_by: str = Field(default="block_time", description="Field to sort by")
    sort_order: str = Field(default="desc", description="Sort direction (asc/desc)")

class GetSOLTokenSecurityInput(BaseModel):
    chain: str = Field(default="sol", description="Chain name (e.g. sol)")
    token_address: str = Field(..., description="SOL Token address")
# class ListToolsResponse(BaseModel):
#     tools: List[Tool]

class GetTreasureListInput(BaseModel):
    marketcap_min: int = Field(default=100000, description="Minimum market cap")
    tvl_min: int = Field(default=100000, description="Minimum TVL")
    smart_money_buy_count_24h_min: int = Field(default=0, description="Minimum smart money buy count in 24h")
    smart_money_sell_count_24h_min: int = Field(default=0, description="Minimum smart money sell count in 24h")
    page_no: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=50, ge=1, le=100, description="Page size")
    category: str = Field(default="hot", description="Category (e.g. hot)")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """
    List available tools.
 
    """
    return [
        

        Tool(
            name="get-eth-balance",
            description="Check the ETH balance of an Eth address",
            # inputSchema={
            #     "type": "object",
            #     "properties": {
            #         "address": {
            #             "type": "string",
            #             "description": "Ethereum address (0x format)",
            #             "pattern": "^0x[a-fA-F0-9]{40}$",
                       
            #         },
            #     },
            #     "required": ["address"],
            # }
            inputSchema=CheckBalanceInput.model_json_schema()
        ),
        Tool(
            name="get-transactions",
            description="Get transaction history for an Ethereum address",
             
            inputSchema=TransactionHistoryInput.model_json_schema()
        ),
        Tool(
            name="get-token-transfers",
            description="Get ERC20 token transfers for an Ethereum address",
            # inputSchema={
            #     "type": "object",
            #     "properties": {
            #         "address": {
            #             "type": "string",
            #             "description": "Ethereum address (0x format)",
            #             "pattern": "^0x[a-fA-F0-9]{40}$"
            #         },
            #         "limit": {
            #             "type": "integer",
            #             "description": "Number of transfers to return (max 100)",
            #             "minimum": 1,
            #             "maximum": 100
            #         },
            #     },
            #     "required": ["address"],
            # }
            inputSchema=TokenTransferInput.model_json_schema()
        ),
        Tool(
            name="get-contract-abi",
            description="Get the ABI for a smart contract",
            # inputSchema={
            #     "type": "object",
            #     "properties": {
            #         "address": {
            #             "type": "string",
            #             "description": "Contract address (0x format)",
            #             "pattern": "^0x[a-fA-F0-9]{40}$"
            #         },
            #     },
            #     "required": ["address"],
            # }
            inputSchema=ContractInput.model_json_schema()
        ),
        Tool(
            name="get-gas-prices",
            description="Get current gas prices in Gwei",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get-ens-name",
            description="Get the ENS name for an Ethereum address",
            # inputSchema={
            #     "type": "object",
            #     "properties": {
            #         "address": {
            #             "type": "string",
            #             "description": "Ethereum address (0x format)",
            #             "pattern": "^0x[a-fA-F0-9]{40}$"
            #         },
            #     },
            #     "required": ["address"],
            # },
            inputSchema=ENSNameInput.model_json_schema()
        ),
        Tool(
            name="get-new-pairs",
            description="Get new trading pairs from GMGN",
            inputSchema=GetNewPairsInput.model_json_schema()
        ),
        Tool(
            name="get-token-kline",
            description="Get token kline data OHLCV from GMGN",
            inputSchema=GetTokenKlineInput.model_json_schema()
        ),
        # Tool(
        #     name="get-sol-balance",
        #     description="Check the SOL balance of a Solana address from Solanabeach",
        #     inputSchema=SolbeachAccountInput.model_json_schema()
        # ),

        Tool(
            name="get-hot-pairs",
            description="Get hot trading pairs from ave with smart money analysis",
            inputSchema=GetTreasureListInput.model_json_schema()
        ),
        Tool(
            name="get-pairs",
            description="Get token trading pairs list with smart money analysis ",
            inputSchema=GetNewPairsInput.model_json_schema()
        ),
        Tool( #无验证
            name="get-sol-balance-explorer",
            description="Check the SOL balance of a Solana address ",#from Solana Explorer",
            inputSchema=SolanaExplorerAccountInput.model_json_schema()
        ),
        Tool(
            name="get-sol-wallet-holdings",
            description="Get sol wallet holdings  token from GMGN",
            inputSchema=GetWalletHoldingsInput.model_json_schema()
        ),
        # Tool(
        #     name="get-sol-transfers",
        #     description="Get Solana account transfer history",
        #     inputSchema=GetSOLTransfersInput.model_json_schema()
        # ),
        Tool(
            name="get-sol-token-security",
            description="Get SOL token security information from GMGN",
            inputSchema=GetSOLTokenSecurityInput.model_json_schema()
        ),
 
    ]

  
@server.call_tool()
async def call_tool( name: str, arguments: dict | None) -> Any:
    """
   
    Tools can fetch web3 data and notify clients of changes.
    """
    if name == "get-eth-balance":
        try:
        
        
            input_data = CheckBalanceInput(**arguments)
            
            # Use context manager to handle both request and response logging
            with open("logxx.txt", "a") as log_file:
                # Log request
                log_file.write(
                    f"[REQUEST] Tool: check-balance, Address: {input_data.address}\n"
                )
                
                # Get balance
                balance = await etherscan_service.get_address_balance(input_data.address)
                
                # Format response
                response = f"Address: {balance['address']}\nBalance: {balance['balanceInEth']}\n"
                
                # Log response
                log_file.write(
                    f"[RESPONSE] Address: {balance['address']}, Balance: {balance['balanceInEth']}"
                )
                log_file.write(
                    f"[RESPONSE] type: {type(response)} \n"
                )
       
            return [TextContent(type="text", text= response)]
          
        except Exception as e:
            raise ValueError(f"Unknown tool: {e}")

    elif name == "get-transactions":
        try:
            input_data = TransactionHistoryInput(**arguments)
            transactions = await etherscan_service.get_transaction_history(
                address=input_data.address,
                startblock=input_data.startblock,
                endblock=input_data.endblock,
                page=input_data.page,
                offset=input_data.offset,
                sort=input_data.sort
            )
            formatted_transactions = [
                f"Block {tx['blockNumber']}:\n"
                f"Time: {tx['timestamp']}\n"
                f"Hash: {tx['hash']}\n"
                f"From: {tx['from']}\n"
                f"To: {tx['to']}\n"
                f"Value: {tx['value']} ETH\n"
                f"---\n"
                for tx in transactions
            ]
            response = (
                f"Recent transactions for {input_data.address}:\n\n" + 
                "\n".join(formatted_transactions)
                if transactions
                else f"No transactions found for {input_data.address}"
            )
            return [TextContent(type="text", text=response)]
        except Exception as e:
            raise ValueError(f"Error getting transactions: {str(e)}")

    elif name == "get-token-transfers":
        try:
            input_data = TokenTransferInput(**arguments)
            transfers = await etherscan_service.get_token_transfers(input_data.address, input_data.limit)
            formatted_transfers = [
                f"Block {tx['blockNumber']} ({tx['timestamp']}):\n"
                f"Token: {tx['tokenName']} ({tx['tokenSymbol']})\n"
                f"From: {tx['from']}\n"
                f"To: {tx['to']}\n"
                f"Value: {tx['value']}\n"
                f"Contract: {tx['token']}\n"
                f"---"
                for tx in transfers
            ]
            response = (
                f"Recent token transfers for {input_data.address}:\n\n{''.join(formatted_transfers)}"
                if transfers
                else f"No token transfers found for {input_data.address}"
            )
            return [TextContent(type="text", text=response)]
        except Exception as e:
            raise ValueError(f"Unknown tool: {e}")

    elif name == "get-contract-abi":
        try:
            input_data = ContractInput(**arguments)
            abi_data = await etherscan_service.get_contract_abi(input_data.address)
            formatted_abi = json.dumps(abi_data["abi"], indent=2)
            return [TextContent(type="text", text=f"Contract ABI for {abi_data['address']}:\n\n{formatted_abi}")]
        except Exception as e:
            raise ValueError(f"Error getting contract ABI: {str(e)}")

    elif name == "get-gas-prices":
        try:
            prices = await etherscan_service.get_gas_oracle()
            response = (
                "Current Gas Prices:\n"
                f"Safe Low: {prices['safeGwei']} Gwei\n"
                f"Standard: {prices['proposeGwei']} Gwei\n"
                f"Fast: {prices['fastGwei']} Gwei"
            )
            return [TextContent(type="text", text=response)]
        except Exception as e:
            raise ValueError(f"Unknown tool: {e}")

    elif name == "get-ens-name":
        try:
            input_data = ENSNameInput(**arguments)
            ens_name = await etherscan_service.get_ens_name(input_data.address)
            response = f"ENS name for {input_data.address}: {ens_name}" if ens_name else f"No ENS name found for {input_data.address}"
            return [TextContent(type="text", text=response)]
        except Exception as e:
            raise ValueError(f"Unknown tool: {e}")

    elif name == "get-new-pairs":
        try:
            input_data = GetNewPairsInput(**arguments)
            pairs = await gmgnscan_service.get_new_pairs(
                chain=input_data.chain,
                period=input_data.period,
                limit=input_data.limit,
                min_marketcap=input_data.min_marketcap,
                min_swaps1h=input_data.min_swaps1h,
                min_holder_count=input_data.min_holder_count,
                filters=input_data.filters,
                orderby=input_data.orderby,
                direction=input_data.direction
            )
            formatted_pairs = [
                (f"CA address: {pair['address']}\n"
                f"Token: {pair['base_token_info']['name']} ({pair['base_token_info']['symbol']})\n"
                f"Price: ${pair['base_token_info']['price']}\n"
                f"Market Cap: ${pair['base_token_info']['market_cap']}\n"
                f"Price Changes:\n"
                f"1h: {pair['base_token_info']['price_change_percent1h']}%\n"
                f"5m: {pair['base_token_info']['price_change_percent5m']}%\n"
                f"1m: {pair['base_token_info']['price_change_percent1m']}%\n"
                f"Liquidity: ${pair['base_token_info']['liquidity']}\n"
                f"Volume: ${pair['base_token_info']['volume']}\n"
                f"Trading Activity:\n"
                f"Total Swaps: {pair['base_token_info']['swaps']}\n"
                f"Buys: {pair['base_token_info']['buys']}\n"
                f"Sells: {pair['base_token_info']['sells']}\n"
                f"Holders: {pair['base_token_info']['holder_count']}\n"
                f"Top 10 Holders: {float(pair['base_token_info']['top_10_holder_rate'])*100:.2f}%\n"
                f"Token Info:\n"
                f"Total Supply: {pair['base_token_info']['total_supply']}\n"
                f"Burn Ratio: {pair['base_token_info']['burn_ratio']}\n"
                f"Burn Status: {pair['base_token_info']['burn_status']}\n"
                f"Creator Info:\n"
                f"Creator: {pair['creator']}\n"
                f"Creator Balance: {float(pair['base_token_info']['creator_balance_rate'])*100:.4f}%\n"
                f"Creator Status: {pair['base_token_info']['creator_token_status']}\n"
                f"Security:\n"
                f"Honeypot: {pair['base_token_info']['is_honeypot']}\n"
                f"Renounced: {pair['base_token_info']['renounced']}\n"
                f"Renounced Mint: {pair['base_token_info']['renounced_mint']}\n"
                f"Renounced Freeze: {pair['base_token_info']['renounced_freeze_account']}\n"
                f"Pool Info:\n"
                f"  Type: {pair['pool_type_str']}\n"
                f"  Quote Symbol: {pair['quote_symbol']}\n"
                f"  Quote Reserve: {pair['quote_reserve']}\n"
                f"  Initial Liquidity: {pair['initial_liquidity']}\n"
                f"Social Links: {', '.join(f'{k}: {v}' for k,v in pair['base_token_info']['social_links'].items() if v)}\n"
                f"Launch Time: {datetime.fromtimestamp(pair['open_timestamp']).strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"---\n").encode('utf-8').decode('utf-8')
                for pair in pairs
            ]
            response = ("New Trading Pairs:\n\n" + "\n".join(formatted_pairs)).encode('utf-8').decode('utf-8')
            return [TextContent(type="text", text=response)]
        except Exception as e:
            error_msg = str(e).encode('utf-8').decode('utf-8')
            raise ValueError(f"Error getting new pairs: {error_msg}")

    elif name == "get-token-kline":
        try:
            input_data = GetTokenKlineInput(**arguments)
            klines = await gmgnscan_service.get_token_kline(
                chain=input_data.chain,
                token_address=input_data.token_address,
                resolution=input_data.resolution,
                from_time=int(time.time()) - (60 * 60 * 24 * 30),  
                to_time=int(time.time())  # Current time
            )
            
            formatted_klines = [
                (f"Time: {datetime.fromtimestamp(int(kline['time'])/1000).strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Open:   ${float(kline['open']):.8f}\n"
                f"High:   ${float(kline['high']):.8f}\n"
                f"Low:    ${float(kline['low']):.8f}\n"
                f"Close:  ${float(kline['close']):.8f}\n"
                f"Volume: {float(kline['volume']):.2f}\n"
                f"---\n").encode('utf-8').decode('utf-8')
                for kline in klines
            ]
            
            response = (f"Kline Data ({input_data.resolution}):\n\n" + 
                       "\n".join(formatted_klines)).encode('utf-8').decode('utf-8')
            return [TextContent(type="text", text=response)]
        except Exception as e:
            error_msg = str(e).encode('utf-8').decode('utf-8')
            raise ValueError(f"Error getting token kline: {error_msg}")

    elif name == "get-sol-transfers":
        try:
            input_data = GetSOLTransfersInput(**arguments)
            transfers = await solscan_service.get_account_transfers(
                address=input_data.address,
                page=input_data.page,
                page_size=input_data.page_size,
                sort_by=input_data.sort_by,
                sort_order=input_data.sort_order
            )
            
            formatted_transfers = [
                (f"Transaction: {transfer['transaction_id']}\n"
                f"Time: {transfer['datetime']}\n"
                f"Type: {transfer['type']}\n"
                f"From: {transfer['from']}\n"
                f"To: {transfer['to']}\n"
                f"Token: {transfer['token']}\n"
                f"Amount: {transfer['amount'] / (10 ** transfer['decimals'])}\n"
                f"Direction: {transfer['direction']}\n"
                f"---\n").encode('utf-8').decode('utf-8')
                for transfer in transfers
            ]
            
            response = ("Solana Account Transfers:\n\n" + 
                       "\n".join(formatted_transfers)).encode('utf-8').decode('utf-8')
            return [TextContent(type="text", text=response)]
        except Exception as e:
            error_msg = str(e).encode('utf-8').decode('utf-8')
            raise ValueError(f"Error getting transfers: {error_msg}")

    elif name == "get-sol-balance":
        try:
            input_data = SolbeachAccountInput(**arguments)
            balance_info = await solbeach_service.get_address_balance(input_data.address)
            if balance_info:
                response = f"Address: {balance_info['address']}\nBalance: {balance_info['balance']}\n"
                return [TextContent(type="text", text=response)]
            else:
                return [TextContent(type="text", text=f"No account info found for {input_data.address}")]
        except Exception as e:
            raise ValueError(f"Error getting solbeach account info: {str(e)}")

    elif name == "get-sol-balance-explorer":
        try:
            input_data = SolanaExplorerAccountInput(**arguments)
            balance_info = await solana_explorer_service.get_address_balance(input_data.address)
            if balance_info:
                response = f"Address: {balance_info['address']}\nBalance: {balance_info['balance']}\n"
                return [TextContent(type="text", text=response)]
            else:
                return [TextContent(type="text", text=f"No account info found for {input_data.address}")]
        except Exception as e:
            raise ValueError(f"Error getting solana explorer account info: {str(e)}")

    elif name == "get-sol-wallet-holdings":
        try:
            input_data = GetWalletHoldingsInput(**arguments)
            holdings = await gmgnscan_service.get_wallet_holdings(
                chain=input_data.chain,
                address=input_data.address,
                limit=input_data.limit,
                orderby=input_data.orderby,
                direction=input_data.direction,
                showsmall=input_data.showsmall,
                sellout=input_data.sellout,
                hide_abnormal=input_data.hide_abnormal
            )
            formatted_holdings = [
                f"Token: {holding['token']['name']} ({holding['token']['symbol']})\n"
                f"Balance: {holding['balance']}\n"
                f"USD Value: ${holding['usd_value']}\n"
                f"Price: ${holding['price']}\n"
                f"Total Profit: ${holding['total_profit']}\n"
                f"Last Active: {datetime.fromtimestamp(holding['last_active_timestamp']).strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"---\n"
                for holding in holdings
            ]
            return [TextContent(type="text", text="Wallet Holdings:\n\n" + "".join(formatted_holdings))]
        except Exception as e:
            raise ValueError(f"Error getting wallet holdings: {str(e)}")
    
    elif name == "get-sol-token-security":
        try:
            input_data = GetSOLTokenSecurityInput(**arguments)
            security_info = await gmgnscan_service.get_token_security(
                chain=input_data.chain,
                token_address=input_data.token_address
            )
            response = (
                f"Token Security for {security_info['address']}:\n"
                f"Show Alert: {security_info.get('is_show_alert')}\n"
                f"Top 10 Holder Rate: {security_info.get('top_10_holder_rate')}\n"
                f"Renounced Mint: {security_info.get('renounced_mint')}\n"
                f"Renounced Freeze Account: {security_info.get('renounced_freeze_account')}\n"
                f"Burn Ratio: {security_info.get('burn_ratio')}\n"
                f"Burn Status: {security_info.get('burn_status')}\n"
                f"Dev Token Burn Amount: {security_info.get('dev_token_burn_amount')}\n"
                f"Dev Token Burn Ratio: {security_info.get('dev_token_burn_ratio')}\n"
     
            )
            return [TextContent(type="text", text=response)]
        except Exception as e:
            raise ValueError(f"Error getting token security: {str(e)}")

    elif name == "get-hot-pairs" or name == "get-pairs":
        try:
            input_data = GetTreasureListInput(**arguments)
            with AveAIService() as service:
                pairs = service.get_treasure_list(
                    marketcap_min=input_data.marketcap_min,
                    tvl_min=input_data.tvl_min,
                    smart_money_buy_count_24h_min=input_data.smart_money_buy_count_24h_min,
                    smart_money_sell_count_24h_min=input_data.smart_money_sell_count_24h_min,
                    page_no=input_data.page_no,
                    page_size=input_data.page_size,
                    category=input_data.category
                )
                
                formatted_pairs = [
                #    f"Pair: {pair['id']}\n"
                    f"Chain: {pair['chain']}\n"
                 #   f"Token: {pair['base_token_info']['symbol']} ({pair['base_token_info']['name']})\n"
                    f"Address: {pair['address']}\n"
                    f"Price: ${pair['base_token_info']['price']}\n"
                    f"Market Cap: ${pair['base_token_info']['market_cap']}\n"
                    f"Liquidity: ${pair['base_token_info']['liquidity']}\n"
                    f"Volume: ${pair['base_token_info']['volume']}\n"
                    f"Holders: {pair['base_token_info']['holder_count']}\n"
                    f"Trading Activity:\n"
                    f"  Swaps: {pair['base_token_info']['swaps']}\n"
                    f"  Buys: {pair['base_token_info']['buys']}\n"
                    f"  Sells: {pair['base_token_info']['sells']}\n"
                    f"Smart Money Activity:\n"
                    f"  Smart Money Count: {pair['base_token_info']['smart_degen_count']}\n"
                    f"Top 10 Holders: {pair['base_token_info']['top_10_holder_rate']}%\n"
                    f"Creator Balance: {pair['base_token_info']['creator_balance_rate']}%\n"
                    f"---\n"
                    for pair in pairs
                ]
                
                response = "\n\n" + "".join(formatted_pairs)
                return [TextContent(type="text", text=response)]
                
        except Exception as e:
            error_msg = str(e).encode('utf-8').decode('utf-8')
            raise ValueError(f"Error getting treasure list: {error_msg}")

    else:
        raise ValueError(f"Unknown tool: {name}")
 


sse = SseServerTransport("/messages/")


async def handle_sse(request):
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await server.run(
            streams[0], streams[1], server.create_initialization_options()
        )



routes = [
    Route("/sse", endpoint=handle_sse),
    Mount("/messages/", app=sse.handle_post_message),

]

 
starlette_app = Starlette(routes=routes,debug=True)
if __name__ == "__main__":

    uvicorn.run(starlette_app, host="0.0.0.0", port=28500)
