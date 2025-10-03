"""
Специализированный модуль для CRYPTOSUD анализа.
Отвечает за комплексный анализ криптовалют с использованием множественных источников данных.
"""
import logging
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger("chatumba.crypto.cryptosud")

# Импорты из других модулей
from .detector import extract_trading_pair_from_description
from .data_fetcher import fetch_crypto_news, fetch_macro_economic_data, fetch_bingx_market_data, format_bingx_data_for_prompts, fetch_ultimate_crypto_data
from .analyzer import analyze_trading_chart

# Импорт LLM клиента через component manager
from backend.utils.component_manager import get_component_manager

component_manager = get_component_manager()
from backend.api.telegram import send_telegram_message, send_long_telegram_message


async def cryptosud_analysis(chat_id: str, 
                           image_description: str, 
                           crypto_terms: List[str],
                           detailed_chart_analysis: Optional[Dict] = None) -> str:
    """
    КРИПТОСУД - специализированный анализ криптографиков с интеграцией BingX API.
    """
    try:
        # 1. Уведомление о запуске с отображением процессов
        await send_telegram_message(chat_id, "🚨 ВНИМАНИЕ! ОБНАРУЖЕН КРИПТОГРАФ!", None)
        await send_telegram_message(chat_id, f"🔍 Найденные термины: {', '.join(crypto_terms[:5])}", None)
        
        # Показываем результаты специализированного анализа
        if detailed_chart_analysis:
            await send_telegram_message(chat_id, "📊 СПЕЦИАЛИЗИРОВАННЫЙ АНАЛИЗ ГРАФИКА ПОЛУЧЕН!", None)
            # Отправляем краткую выжимку специализированного анализа
            analysis_preview = detailed_chart_analysis[:300] + "..." if len(detailed_chart_analysis) > 300 else detailed_chart_analysis
            await send_telegram_message(chat_id, f"📈 Краткий анализ графика:\n{analysis_preview}", None)
        else:
            await send_telegram_message(chat_id, "⚠️ Специализированный анализ недоступен, работаю с базовым описанием", None)
        
        await send_telegram_message(chat_id, "⚖️ ЗАПУСКАЕТСЯ КРИПТОСУД!", None)
        
        # 2. ОПРЕДЕЛЯЕМ ТОРГОВУЮ ПАРУ И ПОЛУЧАЕМ ДАННЫЕ BINGX
        trading_pair = extract_trading_pair_from_description(image_description, crypto_terms)
        await send_telegram_message(chat_id, f"🎯 Определена торговая пара: {trading_pair}", None)
        
        # 2.1. Получаем данные BingX API
        await send_telegram_message(chat_id, f"📡 Подключаюсь к BingX API для {trading_pair}...", None)
        bingx_data = await fetch_bingx_market_data(trading_pair)
        
        if "error" not in bingx_data:
            await send_telegram_message(chat_id, "✅ BingX API подключен! Получаю рыночные данные...", None)
            # Показываем краткую информацию о полученных данных
            ticker_info = ""
            if "ticker" in bingx_data and bingx_data["ticker"]:
                ticker_data = bingx_data["ticker"].get("data", {})
                if ticker_data and isinstance(ticker_data, dict):
                    price = ticker_data.get('lastPrice', 'N/A')
                    change = ticker_data.get('priceChangePercent', 'N/A')
                    ticker_info = f"💰 Цена: ${price} ({change}%)"
            
            if ticker_info:
                await send_telegram_message(chat_id, f"📊 {ticker_info}", None)
        else:
            await send_telegram_message(chat_id, "⚠️ BingX API недоступен, работаю с альтернативными источниками", None)
        
        # 2.2. Парсинг криптоновостей и максимальных данных
        await send_telegram_message(chat_id, "📰 Собираю МАКСИМУМ данных о рынке...", None)
        crypto_news = await fetch_crypto_news(crypto_terms)
        
        # 2.3. Получаем ультимейт данные
        await send_telegram_message(chat_id, "🚀 Подключаю 6 источников данных (Binance, CoinGecko, F&G Index...)...", None)
        ultimate_data = await fetch_ultimate_crypto_data(crypto_terms)
        
        # 2.4. Форматируем данные BingX для промптов
        bingx_formatted = format_bingx_data_for_prompts(bingx_data)
        
        # Объединяем все данные
        full_market_data = f"{crypto_news}\n\n🔥 РАСШИРЕННЫЕ ДАННЫЕ:\n{ultimate_data}\n\n{bingx_formatted}"
        
        await send_telegram_message(chat_id, "✅ Все данные собраны! Начинаю анализ экспертов...", None)
        
        # 3. БЫЧИЙ АНАЛИТИК
        await send_telegram_message(chat_id, "🐂 Формирую БЫЧЬЮ позицию...", None)
        
        # Формируем полное описание графика
        full_chart_description = image_description
        if detailed_chart_analysis:
            full_chart_description += f"\n\n📊 ДЕТАЛЬНЫЙ ТЕХНИЧЕСКИЙ АНАЛИЗ:\n{detailed_chart_analysis}"
        
        bull_prompt = f"""🐂 Ты — БЫЧИЙ КРИПТОАНАЛИТИК! Оптимист и сторонник роста! 📈

🎯 Проанализируй график и рыночные данные с БЫЧЬЕЙ позиции:
💚 — Какие сигналы роста ты видишь?
🚀 — Почему цена пойдет ВВЕРХ?
💎 — Какие уровни для покупки?
📊 — Твой прогноз на ближайшее время?

🎨 Используй эмодзи, будь убедительным быком! 🐂

📷 Анализ графика:
{full_chart_description}

📰 Рыночные данные:
{full_market_data}

⚠️ ВАЖНО: Используй данные BingX API для подтверждения своих выводов!"""
        
        bull_opinion = await component_manager.get_llm_client().chat_completion(
            user_message=bull_prompt,
            system_prompt="🐂 Ты бычий криптоаналитик! Ищи сигналы роста! Используй эмодзи! 📈",
            chat_history=[],
            max_tokens=1000
        )
        
        await send_telegram_message(chat_id, "🐂 Бычий аналитик завершил анализ!", None)
        await send_long_telegram_message(chat_id, f"🐂 **БЫЧЬЯ ПОЗИЦИЯ:**\n{bull_opinion}", None)
        
        # 4. МЕДВЕЖИЙ АНАЛИТИК
        await send_telegram_message(chat_id, "🐻 Формирую МЕДВЕЖЬЮ позицию...", None)
        
        bear_prompt = f"""🐻 Ты — МЕДВЕЖИЙ КРИПТОАНАЛИТИК! Реалист и скептик! 📉

🎯 Проанализируй график и рыночные данные с МЕДВЕЖЬЕЙ позиции:
❤️ — Какие сигналы падения ты видишь?
📉 — Почему цена пойдет ВНИЗ?
💸 — Какие риски и опасности?
📊 — Твой прогноз на коррекцию?

🎨 Используй эмодзи, будь осторожным медведем! 🐻

📷 Анализ графика:
{full_chart_description}

📰 Рыночные данные:
{full_market_data}

⚠️ ВАЖНО: Используй данные BingX API для подтверждения своих выводов!"""
        
        bear_opinion = await component_manager.get_llm_client().chat_completion(
            user_message=bear_prompt,
            system_prompt="🐻 Ты медвежий криптоаналитик! Ищи риски и сигналы падения! Используй эмодзи! 📉",
            chat_history=[],
            max_tokens=1000
        )
        
        await send_telegram_message(chat_id, "🐻 Медвежий аналитик завершил анализ!", None)
        await send_long_telegram_message(chat_id, f"🐻 **МЕДВЕЖЬЯ ПОЗИЦИЯ:**\n{bear_opinion}", None)
        
        # 5. ТЕХНИЧЕСКИЙ СУДЬЯ
        await send_telegram_message(chat_id, "📊 Технический анализ от судьи...", None)
        
        tech_prompt = f"""📊 Ты — ТЕХНИЧЕСКИЙ АНАЛИТИК-СУДЬЯ! Объективный эксперт! ⚖️

🔍 Перед тобой два противоположных мнения. Дай техническую оценку:
📈 — Какие технические сигналы сильнее?
⚖️ — Что говорят индикаторы и паттерны?
🎯 — Ключевые уровни и зоны?
📊 — Объективный технический прогноз?

🎨 Используй эмодзи и будь техническим экспертом! 📊

📷 Описание графика:
{image_description}

🐂 Бычье мнение:
{bull_opinion}

🐻 Медвежье мнение:
{bear_opinion}

📰 Рыночные данные:
{full_market_data}

⚠️ ВАЖНО: Используй данные BingX API для подтверждения технических уровней!"""
        
        tech_analysis = await component_manager.get_llm_client().chat_completion(
            user_message=tech_prompt,
            system_prompt="📊 Ты технический аналитик-судья! Объективный анализ графиков! Используй эмодзи! ⚖️",
            chat_history=[],
            max_tokens=20000  # Увеличиваем до 20K токенов!
        )
        
        await send_telegram_message(chat_id, "📊 Технический судья вынес вердикт!", None)
        await send_long_telegram_message(chat_id, f"📊 **ТЕХНИЧЕСКИЙ АНАЛИЗ:**\n{tech_analysis}", None)
        
        # 6. МАКРОЭКОНОМИЧЕСКИЙ ЭКСПЕРТ
        await send_telegram_message(chat_id, "🌍 Собираю актуальные макроэкономические данные...", None)
        
        # Получаем свежие макроэкономические данные
        macro_economic_data = await fetch_macro_economic_data()
        
        await send_telegram_message(chat_id, "🌍 Макроэкономический анализ...", None)
        
        current_date = datetime.now().strftime("%d.%m.%Y")
        current_year = datetime.now().year
        
        macro_prompt = f"""🌍 Ты — МАКРОЭКОНОМИЧЕСКИЙ ЭКСПЕРТ! Видишь большую картину! 🔮

⚠️ ВАЖНО: СЕГОДНЯ {current_date} ({current_year} год). Анализируй с учетом ТЕКУЩЕГО времени!

🌐 Проанализируй ситуацию с высоты макроэкономики:
💰 — Как текущая макроэкономика влияет на крипту в {current_year} году?
🏦 — Что происходит с традиционными рынками СЕЙЧАС?
📈 — Долгосрочные тренды и циклы (учитывай халвинг 2024, ETF одобрения)?
🎯 — Стратегические рекомендации на ближайшие 6-12 месяцев?
🔮 — Где мы находимся в 4-летнем цикле Bitcoin?

🎨 Используй эмодзи и дай мудрый макросовет! 🌍

📅 АКТУАЛЬНЫЕ МАКРОДАННЫЕ ({current_date}):
{macro_economic_data}

📷 Описание графика:
{image_description}

🐂 Бычье мнение:
{bull_opinion}

🐻 Медвежье мнение:
{bear_opinion}

📊 Технический анализ:
{tech_analysis}

📰 Рыночные данные:
{full_market_data}

⚠️ ВАЖНО: Используй данные BingX API для понимания текущего состояния рынка!"""
        
        macro_analysis = await component_manager.get_llm_client().chat_completion(
            user_message=macro_prompt,
            system_prompt=f"🌍 Ты макроэкономический эксперт! СЕГОДНЯ {current_date} ({current_year} год)! Анализируй с учетом ТЕКУЩЕГО времени и циклов! Используй эмодзи! 🔮",
            chat_history=[],
            max_tokens=2000
        )
        
        await send_telegram_message(chat_id, "🌍 Макроэксперт завершил глобальный анализ!", None)
        await send_long_telegram_message(chat_id, f"🌍 **МАКРОАНАЛИЗ:**\n{macro_analysis}", None)
        
        # 7. ТОРГОВЫЙ СИГНАЛ - ФИНАЛЬНАЯ СДЕЛКА
        await send_telegram_message(chat_id, "💰 Формирую торговый сигнал...", None)
        
        trading_prompt = f"""💰 Ты — ПРОФЕССИОНАЛЬНЫЙ ТРЕЙДЕР-АНАЛИТИК! Эксперт по торговым сигналам! 📊

🎯 На основе ВСЕХ анализов выше, дай ЧЕТКУЮ ТОРГОВУЮ РЕКОМЕНДАЦИЮ:

📈 **НАПРАВЛЕНИЕ:** LONG/SHORT/ОЖИДАНИЕ
💵 **ЦЕНА ВХОДА:** Конкретная цена или диапазон
🎯 **TAKE PROFIT:** Целевые уровни (1-3 цели)
🛑 **STOP LOSS:** Уровень стоп-лосса
⏰ **ТАЙМФРЕЙМ:** Краткосрочно/среднесрочно/долгосрочно
📊 **РАЗМЕР ПОЗИЦИИ:** % от депозита
⚖️ **РИСК/ПРИБЫЛЬ:** Соотношение R/R

🔥 Будь конкретным! Никаких "возможно" и "может быть"!

📷 График: {image_description}

🐂 Бычий анализ: {bull_opinion}

🐻 Медвежий анализ: {bear_opinion}

📊 Технический анализ: {tech_analysis}

🌍 Макроанализ: {macro_analysis}

📰 Рыночные данные: {full_market_data}"""
        
        trading_signal = await component_manager.get_llm_client().chat_completion(
            user_message=trading_prompt,
            system_prompt="💰 Ты профессиональный трейдер! Давай четкие торговые сигналы! Никаких размытых формулировок! 📊",
            chat_history=[],
            max_tokens=1000
        )
        
        await send_telegram_message(chat_id, "💰 Торговый сигнал сформирован!", None)
        await send_long_telegram_message(chat_id, f"💰 **ТОРГОВЫЙ СИГНАЛ:**\n{trading_signal}", None)
        
        # Завершение
        await send_telegram_message(chat_id, "✅ КРИПТОСУД ЗАВЕРШЁН! 🎉 Торговый сигнал готов! 💰", None)
        
        logger.info(f"[КРИПТОСУД] Анализ завершён для группы {chat_id}")
        
        return "✅ КРИПТОСУД ЗАВЕРШЁН! 🎉"
        
    except Exception as e:
        logger.error(f"[КРИПТОСУД] Ошибка: {e}")
        await send_telegram_message(chat_id, f"⚠️ Ошибка КРИПТОСУДА: {e}", None)
        return f"❌ Ошибка КРИПТОСУДА: {e}"


# Глобальный экземпляр для использования
cryptosud_analyzer = None  # Не используется в новой версии
