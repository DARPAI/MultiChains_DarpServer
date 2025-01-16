# 🚀 MultiChainsDarpServer

MultiChainsDarpServer  is a comprehensive blockchain data aggregation service that integrates multiple data sources and APIs to provide token analytics and market insights.

> MultiChainsDarpServer will be used to build a decentralized agent that can interact with web3 services (We are working on it 😊)

## ✨ Features

### Multi-chain Analytics
- 🔷 Ethereum (via Etherscan)
- ☀️ Solana (via SolScan, Solbeach, Solana Explorer)

### Market Intelligence
- 📊 Ave.ai token tracking
- 📈 GMGN.ai market data
- ⚡ Real-time price monitoring
- 🛡️ Token security analysis
- 👛 Wallet holdings tracking

## 🛠️ Environment Setup

### API Configuration
Create a `.env` file with required API keys:
```env
ETHERSCAN_API_KEY=   # From etherscan.io
GMGN_COOKIE=         # From gmgn.ai (F12 dev tools)
AVE_AUTH=            # From ave.ai (F12 dev tools)
```

## 🚀 Quick Start

We use UV as our Python package installer and runner. UV is much faster than pip and provides better dependency resolution.

### Prerequisites
- Python 3.8+
- UV package manager

### Install UV

**Unix-like systems (Linux/macOS):**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Using pip:**
```bash
pip install uv
```

### Start Server

Run the server using UV:
```bash
cd darp
uv run ./src/server.py
```

## 📊 Logging

All API requests and responses are automatically logged for monitoring and debugging purposes.

## 🔨 Development

### Built With
- Etherscan API
- Solscan API
- Ave.ai API
- GMGN.ai API

---



