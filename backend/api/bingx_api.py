"""
Модуль для работы с API биржи BingX.
Предоставляет интерфейс для получения рыночных данных, управления позициями и анализа криптовалют.
"""

import hashlib
import hmac
import time
import requests
import json
from typing import Dict, List, Optional, Union, Any
from urllib.parse import urlencode
import logging

# Безопасный импорт конфигурации
try:
    from ..config import BINGX_CONFIG
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import BINGX_CONFIG

from utils.logger import get_logger

logger = get_logger(__name__)


class BingXAPI:
    """
    Класс для работы с API BingX.
    Поддерживает получение рыночных данных, управление позициями и анализ.
    """
    
    def __init__(self, api_key: str = None, secret_key: str = None, testnet: bool = None):
        """
        Инициализация API клиента BingX.
        
        Args:
            api_key: API ключ BingX
            secret_key: Секретный ключ BingX
            testnet: Использовать тестовую сеть
        """
        self.api_key = api_key or BINGX_CONFIG["api_key"]
        self.secret_key = secret_key or BINGX_CONFIG["secret_key"]
        self.base_url = BINGX_CONFIG["base_url"]
        self.timeout = BINGX_CONFIG["timeout"]
        self.retry_attempts = BINGX_CONFIG["retry_attempts"]
        self.retry_delay = BINGX_CONFIG["retry_delay"]
        self.testnet = testnet if testnet is not None else BINGX_CONFIG["testnet"]
        
        if self.testnet:
            self.base_url = "https://open-api-testnet.bingx.com"
        
        if not self.api_key or not self.secret_key:
            logger.warning("BingX API ключи не настроены. Некоторые функции будут недоступны.")
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """
        Генерирует подпись для API запроса.
        
        Args:
            params: Параметры запроса
            
        Returns:
            Подпись в формате hex
        """
        query_string = urlencode(params)
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, 
                     signed: bool = False) -> Dict:
        """
        Выполняет HTTP запрос к API BingX.
        
        Args:
            method: HTTP метод (GET, POST)
            endpoint: API endpoint
            params: Параметры запроса
            signed: Требуется ли подпись
            
        Returns:
            Ответ от API
        """
        if params is None:
            params = {}
        
        url = f"{self.base_url}{endpoint}"
        
        # Добавляем timestamp для подписанных запросов
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['apiKey'] = self.api_key
            params['signature'] = self._generate_signature(params)
        
        headers = {
            'Content-Type': 'application/json',
            'X-BX-APIKEY': self.api_key
        }
        
        for attempt in range(self.retry_attempts):
            try:
                if method.upper() == 'GET':
                    response = requests.get(url, params=params, headers=headers, 
                                          timeout=self.timeout)
                else:
                    response = requests.post(url, json=params, headers=headers, 
                                           timeout=self.timeout)
                
                response.raise_for_status()
                data = response.json()
                
                if data.get('code') == 0:
                    return data.get('data', data)
                else:
                    logger.error(f"BingX API error: {data}")
                    return data
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise
        
        return {}
    
    def get_server_time(self) -> Dict:
        """Получает время сервера BingX."""
        return self._make_request('GET', '/openApi/spot/v1/common/serverTime')
    
    def get_exchange_info(self) -> Dict:
        """Получает информацию о доступных торговых парах."""
        return self._make_request('GET', '/openApi/spot/v1/common/exchangeInfo')
    
    def get_ticker_24hr(self, symbol: str = None) -> Dict:
        """
        Получает 24-часовую статистику по тикеру.
        
        Args:
            symbol: Торговая пара (например, BTC-USDT)
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._make_request('GET', '/openApi/spot/v1/ticker/24hr', params)
    
    def get_klines(self, symbol: str, interval: str = '1h', 
                   limit: int = 100, start_time: int = None, end_time: int = None) -> Dict:
        """
        Получает исторические данные свечей (K-lines).
        
        Args:
            symbol: Торговая пара
            interval: Интервал (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M)
            limit: Количество свечей (максимум 1000)
            start_time: Время начала (timestamp в миллисекундах)
            end_time: Время окончания (timestamp в миллисекундах)
        """
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
            
        return self._make_request('GET', '/openApi/spot/v1/market/klines', params)
    
    def get_order_book(self, symbol: str, limit: int = 100) -> Dict:
        """
        Получает стакан заявок.
        
        Args:
            symbol: Торговая пара
            limit: Глубина стакана (5, 10, 20, 50, 100, 500, 1000)
        """
        params = {
            'symbol': symbol,
            'limit': limit
        }
        return self._make_request('GET', '/openApi/spot/v1/market/depth', params)
    
    def get_recent_trades(self, symbol: str, limit: int = 100) -> Dict:
        """
        Получает последние сделки.
        
        Args:
            symbol: Торговая пара
            limit: Количество сделок (максимум 1000)
        """
        params = {
            'symbol': symbol,
            'limit': limit
        }
        return self._make_request('GET', '/openApi/spot/v1/market/trades', params)
    
    def get_account_info(self) -> Dict:
        """Получает информацию об аккаунте."""
        return self._make_request('GET', '/openApi/v2/user/getBalance', {}, signed=True)
    
    def get_positions(self, symbol: str = None) -> Dict:
        """
        Получает открытые позиции.
        
        Args:
            symbol: Торговая пара (опционально)
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._make_request('GET', '/openApi/v2/trade/getPositions', params, signed=True)
    
    def get_open_orders(self, symbol: str = None) -> Dict:
        """
        Получает открытые заявки.
        
        Args:
            symbol: Торговая пара (опционально)
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._make_request('GET', '/openApi/v2/trade/getOpenOrders', params, signed=True)
    
    def place_order(self, symbol: str, side: str, order_type: str, 
                   quantity: float, price: float = None, 
                   time_in_force: str = 'GTC') -> Dict:
        """
        Размещает заявку.
        
        Args:
            symbol: Торговая пара
            side: Сторона (BUY, SELL)
            order_type: Тип заявки (LIMIT, MARKET, STOP, STOP_MARKET)
            quantity: Количество
            price: Цена (для лимитных заявок)
            time_in_force: Время действия (GTC, IOC, FOK)
        """
        params = {
            'symbol': symbol,
            'side': side,
            'orderType': order_type,
            'quantity': quantity,
            'timeInForce': time_in_force
        }
        
        if price:
            params['price'] = price
            
        return self._make_request('POST', '/openApi/v2/trade/placeOrder', params, signed=True)
    
    def cancel_order(self, symbol: str, order_id: str) -> Dict:
        """
        Отменяет заявку.
        
        Args:
            symbol: Торговая пара
            order_id: ID заявки
        """
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        return self._make_request('POST', '/openApi/v2/trade/cancelOrder', params, signed=True)
    
    def get_order_history(self, symbol: str = None, limit: int = 100) -> Dict:
        """
        Получает историю заявок.
        
        Args:
            symbol: Торговая пара (опционально)
            limit: Количество записей
        """
        params = {'limit': limit}
        if symbol:
            params['symbol'] = symbol
        return self._make_request('GET', '/openApi/v2/trade/getOrderHistory', params, signed=True)
    
    def get_trade_history(self, symbol: str = None, limit: int = 100) -> Dict:
        """
        Получает историю сделок.
        
        Args:
            symbol: Торговая пара (опционально)
            limit: Количество записей
        """
        params = {'limit': limit}
        if symbol:
            params['symbol'] = symbol
        return self._make_request('GET', '/openApi/v2/trade/getTradeHistory', params, signed=True)
    
    def get_market_data_summary(self, symbols: List[str] = None) -> Dict:
        """
        Получает сводку рыночных данных для нескольких символов.
        
        Args:
            symbols: Список торговых пар
        """
        if not symbols:
            # Получаем популярные пары по умолчанию
            symbols = ['BTC-USDT', 'ETH-USDT', 'BNB-USDT', 'ADA-USDT', 'SOL-USDT']
        
        summary = {}
        for symbol in symbols:
            try:
                ticker = self.get_ticker_24hr(symbol)
                if ticker and isinstance(ticker, dict):
                    summary[symbol] = {
                        'price': float(ticker.get('lastPrice', 0)),
                        'change_24h': float(ticker.get('priceChangePercent', 0)),
                        'volume_24h': float(ticker.get('volume', 0)),
                        'high_24h': float(ticker.get('highPrice', 0)),
                        'low_24h': float(ticker.get('lowPrice', 0))
                    }
            except Exception as e:
                logger.error(f"Error getting data for {symbol}: {e}")
                summary[symbol] = None
        
        return summary
    
    def analyze_market_sentiment(self, symbol: str, timeframe: str = '1h') -> Dict:
        """
        Анализирует настроения рынка для заданной пары.
        
        Args:
            symbol: Торговая пара
            timeframe: Временной интервал
            
        Returns:
            Словарь с анализом настроений
        """
        try:
            # Получаем данные свечей
            klines = self.get_klines(symbol, interval=timeframe, limit=100)
            
            if not klines or not isinstance(klines, list):
                return {'error': 'Не удалось получить данные свечей'}
            
            # Простой анализ настроений на основе цены и объема
            prices = [float(k[4]) for k in klines]  # Цены закрытия
            volumes = [float(k[5]) for k in klines]  # Объемы
            
            current_price = prices[-1]
            price_change = ((current_price - prices[0]) / prices[0]) * 100
            
            # Анализ тренда
            if len(prices) >= 20:
                short_ma = sum(prices[-10:]) / 10
                long_ma = sum(prices[-20:]) / 20
                trend = 'bullish' if short_ma > long_ma else 'bearish'
            else:
                trend = 'neutral'
            
            # Анализ объема
            avg_volume = sum(volumes) / len(volumes)
            current_volume = volumes[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'price_change_24h': price_change,
                'trend': trend,
                'volume_ratio': volume_ratio,
                'sentiment': 'bullish' if price_change > 0 and volume_ratio > 1.2 else 
                           'bearish' if price_change < 0 and volume_ratio > 1.2 else 'neutral'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing market sentiment for {symbol}: {e}")
            return {'error': str(e)}


# Создаем глобальный экземпляр API клиента
bingx_client = BingXAPI() 