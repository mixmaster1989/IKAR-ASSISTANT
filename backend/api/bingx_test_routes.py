"""
API маршруты для тестирования BingX.
Доступны через веб-интерфейс для проверки работы API.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from utils.import_helper import get_bingx_client, get_crypto_integration

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/bingx", tags=["BingX API Testing"])


@router.get("/status")
async def get_bingx_status() -> Dict[str, Any]:
    """Проверяет статус подключения к BingX API."""
    try:
        bingx_client = get_bingx_client()
        if not bingx_client:
            return {
                "status": "error",
                "message": "BingX клиент недоступен",
                "details": "Проверьте настройку API ключей"
            }
        
        # Проверяем подключение
        server_time = bingx_client.get_server_time()
        
        return {
            "status": "success",
            "message": "BingX API подключен",
            "server_time": server_time,
            "api_key_configured": bool(bingx_client.api_key),
            "secret_key_configured": bool(bingx_client.secret_key)
        }
    except Exception as e:
        logger.error(f"Ошибка проверки статуса BingX: {e}")
        return {
            "status": "error",
            "message": f"Ошибка подключения: {str(e)}"
        }


@router.get("/ticker/{symbol}")
async def get_ticker_data(symbol: str = "BTC-USDT") -> Dict[str, Any]:
    """Получает данные тикера для указанной пары."""
    try:
        bingx_client = get_bingx_client()
        if not bingx_client:
            raise HTTPException(status_code=500, detail="BingX клиент недоступен")
        
        ticker = bingx_client.get_ticker_24hr(symbol)
        
        if not ticker or not isinstance(ticker, dict):
            raise HTTPException(status_code=404, detail=f"Данные для {symbol} не найдены")
        
        return {
            "symbol": symbol,
            "data": ticker,
            "formatted": {
                "price": ticker.get('lastPrice', 'N/A'),
                "change_24h": ticker.get('priceChangePercent', 'N/A'),
                "volume": ticker.get('volume', 'N/A'),
                "high_24h": ticker.get('highPrice', 'N/A'),
                "low_24h": ticker.get('lowPrice', 'N/A')
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения тикера {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения данных: {str(e)}")


@router.get("/sentiment/{symbol}")
async def get_market_sentiment(symbol: str = "BTC-USDT", timeframe: str = "1h") -> Dict[str, Any]:
    """Получает анализ настроений рынка для указанной пары."""
    try:
        bingx_client = get_bingx_client()
        if not bingx_client:
            raise HTTPException(status_code=500, detail="BingX клиент недоступен")
        
        sentiment = bingx_client.analyze_market_sentiment(symbol, timeframe)
        
        if not sentiment or 'error' in sentiment:
            raise HTTPException(status_code=404, detail=f"Не удалось проанализировать {symbol}")
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "sentiment": sentiment
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка анализа настроений {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {str(e)}")


@router.get("/crypto-sud")
async def get_crypto_sud_data() -> Dict[str, Any]:
    """Получает данные для криптосуда."""
    try:
        crypto_integration = get_crypto_integration()
        if not crypto_integration:
            raise HTTPException(status_code=500, detail="Crypto integration недоступен")
        
        sud_data = crypto_integration.get_crypto_sud_data()
        
        return {
            "status": "success",
            "data": sud_data,
            "summary": {
                "symbols_count": len(sud_data.get('symbols', {})),
                "trending_pairs_count": len(sud_data.get('trending_pairs', [])),
                "risk_level": sud_data.get('risk_assessment', {}).get('overall_risk', 'unknown')
            }
        }
    except Exception as e:
        logger.error(f"Ошибка получения данных криптосуда: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения данных: {str(e)}")


@router.get("/recommendation/{symbol}")
async def get_position_recommendation(symbol: str = "BTC-USDT", balance: float = 1000) -> Dict[str, Any]:
    """Получает рекомендации по позициям для указанной пары."""
    try:
        crypto_integration = get_crypto_integration()
        if not crypto_integration:
            raise HTTPException(status_code=500, detail="Crypto integration недоступен")
        
        recommendation = crypto_integration.get_position_recommendations(symbol, balance)
        
        if not recommendation or 'error' in recommendation:
            raise HTTPException(status_code=404, detail=f"Не удалось получить рекомендации для {symbol}")
        
        return {
            "symbol": symbol,
            "user_balance": balance,
            "recommendation": recommendation
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения рекомендаций {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения рекомендаций: {str(e)}")


@router.get("/market-overview")
async def get_market_overview() -> Dict[str, Any]:
    """Получает обзор рынка по нескольким основным парам."""
    try:
        bingx_client = get_bingx_client()
        if not bingx_client:
            raise HTTPException(status_code=500, detail="BingX клиент недоступен")
        
        symbols = ["BTC-USDT", "ETH-USDT", "BNB-USDT", "ADA-USDT", "SOL-USDT"]
        overview = {}
        
        for symbol in symbols:
            try:
                ticker = bingx_client.get_ticker_24hr(symbol)
                if ticker and isinstance(ticker, dict):
                    overview[symbol] = {
                        "price": ticker.get('lastPrice', 'N/A'),
                        "change_24h": ticker.get('priceChangePercent', 'N/A'),
                        "volume": ticker.get('volume', 'N/A')
                    }
            except Exception as e:
                logger.warning(f"Не удалось получить данные для {symbol}: {e}")
                overview[symbol] = {"error": str(e)}
        
        return {
            "status": "success",
            "overview": overview,
            "timestamp": "current"
        }
    except Exception as e:
        logger.error(f"Ошибка получения обзора рынка: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения обзора: {str(e)}") 