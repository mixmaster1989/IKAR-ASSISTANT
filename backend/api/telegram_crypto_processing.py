"""
Модуль для обработки крипто-функций Telegram бота.
Перенесено из telegram_polling.py для улучшения структуры кода.
"""

import logging
import asyncio
import aiohttp
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from backend.config import TELEGRAM_CONFIG
from backend.memory.sqlite import sqlite_storage
from backend.api.telegram.crypto_handler import (
    detect_crypto_content,
    extract_trading_pair_from_description,
    fetch_crypto_news,
    analyze_trading_chart
)
from backend.api.telegram.crypto.cryptosud import cryptosud_analysis

logger = logging.getLogger("chatumba.telegram_crypto_processing")

# Словарь для хранения ожидающих подтверждения КРИПТОСУДА
pending_crypto_requests = {}

# Безопасный импорт BingX интеграции
from utils.import_helper import get_bingx_client, get_crypto_integration


async def fetch_ultimate_crypto_data(crypto_terms):
    """
    Получает комплексные данные по криптовалютам.
    Перенесено из telegram_polling.py
    """
    try:
        logger.info(f"[КРИПТО ДАННЫЕ] Получение данных для терминов: {crypto_terms[:5]}")
        
        # Получаем BingX клиент
        bingx_client = get_bingx_client()
        if not bingx_client:
            return {"error": "BingX клиент недоступен"}
        
        # Получаем крипто интеграцию
        crypto_integration = get_crypto_integration()
        if not crypto_integration:
            return {"error": "Крипто интеграция недоступна"}
        
        # Извлекаем торговую пару
        trading_pair = extract_trading_pair_from_description("", crypto_terms)
        
        # Получаем данные с BingX
        bingx_data = await fetch_bingx_market_data(trading_pair)
        
        # Получаем новости
        news_data = await fetch_crypto_news(crypto_terms)
        
        # Получаем макроэкономические данные
        macro_data = await fetch_macro_economic_data()
        
        # Формируем комплексные данные
        comprehensive_data = {
            'trading_pair': trading_pair,
            'bingx_data': bingx_data,
            'news': news_data,
            'macro_data': macro_data,
            'timestamp': datetime.now().isoformat(),
            'crypto_terms': crypto_terms
        }
        
        logger.info(f"[КРИПТО ДАННЫЕ] Получены комплексные данные для {trading_pair}")
        return comprehensive_data
        
    except Exception as e:
        logger.error(f"[КРИПТО ДАННЫЕ] Ошибка получения данных: {e}")
        return {"error": str(e)}


async def fetch_macro_economic_data():
    """
    Получает макроэкономические данные.
    Перенесено из telegram_polling.py
    """
    try:
        logger.info("[МАКРО ДАННЫЕ] Получение макроэкономических данных")
        
        # Здесь будет логика получения макроэкономических данных
        # Пока возвращаем заглушку
        macro_data = {
            'dollar_index': 105.2,
            'oil_price': 85.3,
            'gold_price': 1950.0,
            'vix_index': 18.5,
            'fed_rate': 5.25,
            'inflation': 3.2,
            'unemployment': 3.8,
            'gdp_growth': 2.1
        }
        
        logger.info("[МАКРО ДАННЫЕ] Получены макроэкономические данные")
        return macro_data
        
    except Exception as e:
        logger.error(f"[МАКРО ДАННЫЕ] Ошибка получения данных: {e}")
        return {}


async def fetch_bingx_market_data(trading_pair: str) -> dict:
    """
    Получает рыночные данные с BingX.
    Перенесено из telegram_polling.py
    """
    try:
        bingx_client = get_bingx_client()
        if not bingx_client:
            return {"error": "BingX клиент недоступен"}
        
        # Получаем различные типы данных
        ticker = bingx_client.get_ticker_24hr(trading_pair)
        order_book = bingx_client.get_order_book(trading_pair, limit=50)
        recent_trades = bingx_client.get_recent_trades(trading_pair, limit=100)
        klines_1h = bingx_client.get_klines(trading_pair, interval='1h', limit=24)
        klines_4h = bingx_client.get_klines(trading_pair, interval='4h', limit=30)
        
        # Анализируем настроения
        sentiment = bingx_client.analyze_market_sentiment(trading_pair, '1h')
        
        market_data = {
            'symbol': trading_pair,
            'timestamp': int(datetime.now().timestamp() * 1000),
            'ticker': ticker,
            'order_book': order_book,
            'recent_trades': recent_trades,
            'klines_1h': klines_1h,
            'klines_4h': klines_4h,
            'sentiment': sentiment
        }
        
        logger.info(f"[BINGX] Получены данные для {trading_pair}")
        return market_data
        
    except Exception as e:
        logger.error(f"[BINGX] Ошибка получения данных: {e}")
        return {"error": str(e)}


def format_bingx_data_for_prompts(bingx_data: dict) -> str:
    """
    Форматирует данные BingX для промптов.
    Перенесено из telegram_polling.py
    """
    if not bingx_data or "error" in bingx_data:
        return "❌ Данные BingX недоступны"
    
    formatted = f"📊 **ДАННЫЕ BINGX:**\n\n"
    
    # Тикер
    if "ticker" in bingx_data and bingx_data["ticker"]:
        ticker_data = bingx_data["ticker"].get("data", {})
        if ticker_data and isinstance(ticker_data, dict):
            formatted += f"💰 **ТИКЕР:**\n"
            formatted += f"• Цена: ${ticker_data.get('lastPrice', 'N/A')}\n"
            formatted += f"• Изменение 24ч: {ticker_data.get('priceChangePercent', 'N/A')}%\n"
            formatted += f"• Объем 24ч: {ticker_data.get('volume', 'N/A')}\n"
            formatted += f"• Максимум 24ч: ${ticker_data.get('highPrice', 'N/A')}\n"
            formatted += f"• Минимум 24ч: ${ticker_data.get('lowPrice', 'N/A')}\n\n"
    
    # Стакан заявок
    if "order_book" in bingx_data and bingx_data["order_book"]:
        order_book_data = bingx_data["order_book"].get("data", {})
        if order_book_data and isinstance(order_book_data, dict):
            bids = order_book_data.get("bids", [])
            asks = order_book_data.get("asks", [])
            
            formatted += f"📋 **СТАКАН ЗАЯВОК:**\n"
            if bids:
                formatted += f"• Лучшая покупка: ${bids[0][0]} ({bids[0][1]})\n"
            if asks:
                formatted += f"• Лучшая продажа: ${asks[0][0]} ({asks[0][1]})\n"
            
            # Глубина рынка
            bid_depth = sum(float(bid[1]) for bid in bids[:5]) if bids else 0
            ask_depth = sum(float(ask[1]) for ask in asks[:5]) if asks else 0
            formatted += f"• Глубина покупок (топ-5): {bid_depth:.2f}\n"
            formatted += f"• Глубина продаж (топ-5): {ask_depth:.2f}\n\n"
    
    # Последние сделки
    if "recent_trades" in bingx_data and bingx_data["recent_trades"]:
        trades_data = bingx_data["recent_trades"].get("data", [])
        if trades_data and isinstance(trades_data, list) and len(trades_data) > 0:
            formatted += f"🔄 **ПОСЛЕДНИЕ СДЕЛКИ:**\n"
            # Показываем последние 5 сделок
            for i, trade in enumerate(trades_data[:5]):
                price = trade.get("price", "N/A")
                qty = trade.get("qty", "N/A")
                side = "🟢" if trade.get("isBuyerMaker") else "🔴"
                formatted += f"• {side} ${price} ({qty})\n"
            formatted += "\n"
    
    # Анализ настроений
    if "sentiment" in bingx_data and bingx_data["sentiment"]:
        sentiment_data = bingx_data["sentiment"]
        formatted += f"🎭 **АНАЛИЗ НАСТРОЕНИЙ:**\n"
        formatted += f"• Настроение: {sentiment_data.get('sentiment', 'N/A')}\n"
        formatted += f"• Сила сигнала: {sentiment_data.get('strength', 'N/A')}\n\n"
    
    # Комплексный анализ
    if "comprehensive_analysis" in bingx_data and bingx_data["comprehensive_analysis"]:
        comp_data = bingx_data["comprehensive_analysis"]
        if "analysis" in comp_data:
            analysis = comp_data["analysis"]
            formatted += f"🔍 **КОМПЛЕКСНЫЙ АНАЛИЗ:**\n"
            formatted += f"• Ликвидность: {analysis.get('liquidity_score', 'N/A')}\n"
            formatted += f"• Волатильность: {analysis.get('volatility_score', 'N/A')}%\n"
            formatted += f"• Сила тренда: {analysis.get('trend_strength', 'N/A')}\n"
            
            # Уровни поддержки/сопротивления
            support_resistance = analysis.get("support_resistance", {})
            if support_resistance:
                formatted += f"• Ближайшая поддержка: ${support_resistance.get('nearest_support', 'N/A')}\n"
                formatted += f"• Ближайшее сопротивление: ${support_resistance.get('nearest_resistance', 'N/A')}\n"
            formatted += "\n"
    
    formatted += f"⏰ Время получения: {bingx_data.get('timestamp', 'N/A')}\n"
    formatted += f"📡 Источник: {' + '.join(bingx_data.get('data_sources', ['BingX API']))}\n"
    
    return formatted


async def validate_price_from_apis(trading_pair, chart_price):
    """
    Валидация цены с графика через реальные API.
    Перенесено из telegram_polling.py
    """
    import aiohttp
    
    logger.info(f"[ВАЛИДАЦИЯ-ЦЕНЫ] Проверяю цену {chart_price} для пары {trading_pair}")
    
    validated_prices = []
    
    # Определяем символ для разных API
    pair_mapping = {
        'PEPE/USDT': {'binance': 'PEPEUSDT', 'coingecko': 'pepe'},
        'BTC/USDT': {'binance': 'BTCUSDT', 'coingecko': 'bitcoin'},
        'ETH/USDT': {'binance': 'ETHUSDT', 'coingecko': 'ethereum'},
        'BNB/USDT': {'binance': 'BNBUSDT', 'coingecko': 'binancecoin'}
    }
    
    pair_info = pair_mapping.get(trading_pair.upper())
    if not pair_info:
        logger.warning(f"[ВАЛИДАЦИЯ-ЦЕНЫ] Неизвестная пара: {trading_pair}")
        return chart_price, []
    
    async with aiohttp.ClientSession() as session:
        
        # 1. Binance API
        try:
            binance_symbol = pair_info['binance']
            url = f'https://api.binance.com/api/v3/ticker/price?symbol={binance_symbol}'
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    binance_price = float(data.get('price', 0))
                    validated_prices.append(('Binance', binance_price))
                    logger.info(f"[ВАЛИДАЦИЯ-ЦЕНЫ] Binance: {binance_price}")
        except Exception as e:
            logger.error(f"[ВАЛИДАЦИЯ-ЦЕНЫ] Ошибка Binance: {e}")
        
        # 2. CoinGecko API
        try:
            coingecko_id = pair_info['coingecko']
            url = f'https://api.coingecko.com/api/v3/simple/price?ids={coingecko_id}&vs_currencies=usd'
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    coingecko_price = data.get(coingecko_id, {}).get('usd', 0)
                    if coingecko_price:
                        validated_prices.append(('CoinGecko', coingecko_price))
                        logger.info(f"[ВАЛИДАЦИЯ-ЦЕНЫ] CoinGecko: {coingecko_price}")
        except Exception as e:
            logger.error(f"[ВАЛИДАЦИЯ-ЦЕНЫ] Ошибка CoinGecko: {e}")
    
    # Анализируем валидацию
    if validated_prices:
        avg_price = sum(price for _, price in validated_prices) / len(validated_prices)
        
        # Проверяем отклонение цены с графика
        if chart_price and chart_price > 0:
            deviation = abs(chart_price - avg_price) / avg_price * 100
            logger.info(f"[ВАЛИДАЦИЯ-ЦЕНЫ] График: {chart_price}, Среднее API: {avg_price:.8f}, Отклонение: {deviation:.1f}%")
            
            if deviation > 10:  # Если отклонение больше 10%
                logger.warning(f"[ВАЛИДАЦИЯ-ЦЕНЫ] Большое отклонение! Используем цену из API")
                return avg_price, validated_prices
        
        return chart_price or avg_price, validated_prices
    
    return chart_price, []


async def process_telegram_photo_with_crypto_detection(message, chat_id, user_id, temp_dir, download_telegram_file, send_telegram_message):
    """
    Обработка фото с детекцией криптоконтента.
    Перенесено из telegram_polling.py
    """
    from backend.api.telegram_vision import process_telegram_photo
    from backend.api.telegram_core import send_telegram_message_with_buttons
    
    try:
        logger.info(f"[КРИПТОДЕТЕКТОР] Начинаю обработку фото в группе {chat_id}")
        
        # Обычная обработка фото
        image_description = await process_telegram_photo(message, chat_id, user_id, temp_dir, download_telegram_file, send_telegram_message)
        
        logger.info(f"[КРИПТОДЕТЕКТОР] Получено описание: {image_description[:100] if image_description else 'None'}...")
        
        if image_description:
            logger.info(f"[КРИПТОДЕТЕКТОР] Полное описание: {image_description}")
            # Проверяем на криптоконтент
            is_crypto, crypto_terms = detect_crypto_content(image_description)
            
            logger.info(f"[КРИПТОДЕТЕКТОР] Результат детекции: is_crypto={is_crypto}, terms={crypto_terms}")
            
            if is_crypto:
                logger.info(f"[КРИПТОДЕТЕКТОР] ✅ ОБНАРУЖЕН КРИПТОКОНТЕНТ! Отправляю кнопки подтверждения...")
                logger.info(f"[КРИПТОДЕТЕКТОР] Найденные термины: {crypto_terms}")
                
                # Сохраняем данные для последующего анализа
                request_id = f"{chat_id}_{int(datetime.now().timestamp())}"
                pending_crypto_requests[request_id] = {
                    'chat_id': chat_id,
                    'image_description': image_description,
                    'crypto_terms': crypto_terms,
                    'message': message,
                    'timestamp': datetime.now()
                }
                
                # Отправляем сообщение с кнопками
                buttons = [
                    [{"text": "✅ ДА - Запустить КРИПТОСУД", "callback_data": f"crypto_yes_{request_id}"}],
                    [{"text": "❌ НЕТ - Пропустить", "callback_data": f"crypto_no_{request_id}"}]
                ]
                
                terms_text = ', '.join(crypto_terms[:5])
                confirmation_text = (
                    f"🔍 **ОБНАРУЖЕН КРИПТОГРАФ!**\n\n"
                    f"📊 Найденные термины: {terms_text}\n\n"
                    f"⚠️ КРИПТОСУД потребляет много ресурсов.\n"
                    f"Запустить полный анализ?"
                )
                
                await send_telegram_message_with_buttons(chat_id, confirmation_text, buttons)
                logger.info(f"[КРИПТОДЕТЕКТОР] Отправлены кнопки подтверждения для {request_id}")
            else:
                logger.info(f"[КРИПТОДЕТЕКТОР] ❌ Криптоконтент не обнаружен в группе {chat_id}")
        else:
            logger.warning(f"[КРИПТОДЕТЕКТОР] Не получено описание изображения")
        
        return image_description
        
    except Exception as e:
        logger.error(f"[КРИПТОДЕТЕКТОР] Ошибка: {e}")
        return None


async def handle_crypto_callback(callback_query, callback_data, chat_id, message_id):
    """
    Обрабатывает callback для крипто-функций.
    Перенесено из telegram_polling.py
    """
    from backend.api.telegram_core import answer_callback_query, send_telegram_message
    
    try:
        if callback_data.startswith('crypto_'):
            action = callback_data.split('_')[1]
            
            if action == 'yes':
                # Извлекаем request_id
                request_id = callback_data.split('_', 2)[2]
                
                if request_id in pending_crypto_requests:
                    request_data = pending_crypto_requests[request_id]
                    
                    # Отвечаем на callback
                    await answer_callback_query(callback_query["id"], "🔍 Запускаю КРИПТОСУД анализ...")
                    
                    # Запускаем анализ
                    analysis_result = await cryptosud_analysis(
                        request_data['chat_id'],
                        request_data['image_description'],
                        request_data['crypto_terms']
                    )
                    
                    # Отправляем результат
                    await send_telegram_message(request_data['chat_id'], analysis_result)
                    
                    # Удаляем из pending
                    del pending_crypto_requests[request_id]
                    
                    logger.info(f"[КРИПТО CALLBACK] Анализ завершен для {request_id}")
                else:
                    await answer_callback_query(callback_query["id"], "❌ Запрос устарел")
                    
            elif action == 'no':
                # Извлекаем request_id
                request_id = callback_data.split('_', 2)[2]
                
                # Отвечаем на callback
                await answer_callback_query(callback_query["id"], "❌ Анализ отменен")
                
                # Удаляем из pending
                if request_id in pending_crypto_requests:
                    del pending_crypto_requests[request_id]
                
                logger.info(f"[КРИПТО CALLBACK] Анализ отменен для {request_id}")
                
            else:
                await answer_callback_query(callback_query["id"], "❌ Неизвестное действие")
                
    except Exception as e:
        logger.error(f"Ошибка обработки крипто callback: {e}")
        await answer_callback_query(callback_query["id"], "❌ Ошибка обработки")


def cleanup_old_crypto_requests():
    """Очищает старые крипто-запросы (старше 1 часа)."""
    try:
        current_time = datetime.now()
        expired_requests = []
        
        for request_id, request_data in pending_crypto_requests.items():
            if current_time - request_data['timestamp'] > timedelta(hours=1):
                expired_requests.append(request_id)
        
        for request_id in expired_requests:
            del pending_crypto_requests[request_id]
        
        if expired_requests:
            logger.info(f"[КРИПТО ОЧИСТКА] Удалено {len(expired_requests)} устаревших запросов")
            
    except Exception as e:
        logger.error(f"[КРИПТО ОЧИСТКА] Ошибка очистки: {e}") 