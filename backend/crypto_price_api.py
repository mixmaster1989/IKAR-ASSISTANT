#!/usr/bin/env python3
"""
💰 API для получения актуальных цен криптовалют
Интеграция с биржами для получения реальных данных
"""

import aiohttp
import asyncio
import logging
from typing import Dict, Optional, List
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class CryptoPriceAPI:
    """API для получения актуальных цен криптовалют"""
    
    def __init__(self):
        self.session = None
        self.cache = {}
        self.cache_duration = 60  # 1 минута
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Получение HTTP сессии"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10),
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
        return self.session
    
    async def get_binance_price(self, symbol: str = "BTCUSDT") -> Optional[Dict]:
        """Получение цены с Binance"""
        try:
            session = await self._get_session()
            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "symbol": data["symbol"],
                        "price": float(data["lastPrice"]),
                        "change_24h": float(data["priceChangePercent"]),
                        "volume": float(data["volume"]),
                        "high_24h": float(data["highPrice"]),
                        "low_24h": float(data["lowPrice"]),
                        "source": "Binance",
                        "timestamp": datetime.now().isoformat()
                    }
        except Exception as e:
            logger.error(f"Ошибка получения цены с Binance: {e}")
        return None
    
    async def get_coingecko_price(self, coin_id: str = "bitcoin") -> Optional[Dict]:
        """Получение цены с CoinGecko"""
        try:
            session = await self._get_session()
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if coin_id in data:
                        coin_data = data[coin_id]
                        return {
                            "symbol": coin_id.upper(),
                            "price": coin_data["usd"],
                            "change_24h": coin_data.get("usd_24h_change", 0),
                            "volume": coin_data.get("usd_24h_vol", 0),
                            "source": "CoinGecko",
                            "timestamp": datetime.now().isoformat()
                        }
        except Exception as e:
            logger.error(f"Ошибка получения цены с CoinGecko: {e}")
        return None
    
    async def get_crypto_news(self) -> List[Dict]:
        """Получение новостей о криптовалютах"""
        try:
            session = await self._get_session()
            url = "https://api.coingecko.com/api/v3/news"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", [])[:5]  # Последние 5 новостей
        except Exception as e:
            logger.error(f"Ошибка получения новостей: {e}")
        return []
    
    async def get_crypto_intelligence(self, query: str) -> Dict:
        """Получение комплексной информации о криптовалютах"""
        result = {
            "prices": {},
            "news": [],
            "summary": "",
            "timestamp": datetime.now().isoformat()
        }
        
        # Получаем цены основных криптовалют
        btc_price = await self.get_binance_price("BTCUSDT")
        eth_price = await self.get_binance_price("ETHUSDT")
        
        if btc_price:
            result["prices"]["BTC"] = btc_price
        if eth_price:
            result["prices"]["ETH"] = eth_price
            
        # Получаем новости
        news = await self.get_crypto_news()
        result["news"] = news
        
        # Формируем краткое резюме
        if result["prices"]:
            summary_parts = []
            for symbol, price_data in result["prices"].items():
                change = price_data["change_24h"]
                change_symbol = "📈" if change > 0 else "📉"
                summary_parts.append(
                    f"{symbol}: ${price_data['price']:,.2f} ({change_symbol} {change:+.2f}%)"
                )
            
            result["summary"] = " | ".join(summary_parts)
        
        return result
    
    async def close(self):
        """Закрытие сессии"""
        if self.session and not self.session.closed:
            await self.session.close()

# Глобальный экземпляр
_crypto_api = None

async def get_crypto_api() -> CryptoPriceAPI:
    """Получение глобального экземпляра API"""
    global _crypto_api
    if _crypto_api is None:
        _crypto_api = CryptoPriceAPI()
    return _crypto_api

async def get_crypto_price(symbol: str = "BTC") -> Optional[Dict]:
    """Получение цены криптовалюты"""
    api = await get_crypto_api()
    if symbol.upper() == "BTC":
        return await api.get_binance_price("BTCUSDT")
    elif symbol.upper() == "ETH":
        return await api.get_binance_price("ETHUSDT")
    else:
        return await api.get_binance_price(f"{symbol.upper()}USDT")

async def get_crypto_intelligence(query: str) -> Dict:
    """Получение комплексной информации о криптовалютах"""
    api = await get_crypto_api()
    return await api.get_crypto_intelligence(query) 