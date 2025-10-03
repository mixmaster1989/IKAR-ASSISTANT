#!/usr/bin/env python3
"""
Тестовый скрипт для проверки детектора криптоконтента
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from api.telegram_polling import detect_crypto_content, CRYPTO_TERMS

def test_crypto_detector():
    """Тестирует детектор криптоконтента."""
    
    print("ТЕСТ ДЕТЕКТОРА КРИПТОКОНТЕНТА")
    print("=" * 50)
    
    # Тестовые тексты
    test_texts = [
        "На изображении показан график криптовалютной пары PEPE/USDT на бирже OKX",
        "График отображает динамику цены за последние 15 минут",
        "Видны свечные бары, показывающие изменения цены",
        "На графике также нанесены скользящие средние (EMA)",
        "Bitcoin растет к луне!",
        "Обычная картинка с котиком",
        "Ethereum падает вниз",
        "Покупаю на Binance",
        "Трейдинг на TradingView"
    ]
    
    print(f"📚 Всего криптотерминов в словаре: {len(CRYPTO_TERMS)}")
    print(f"🔤 Примеры терминов: {list(CRYPTO_TERMS)[:10]}")
    print()
    
    for i, text in enumerate(test_texts, 1):
        print(f"🧪 ТЕСТ {i}: {text}")
        is_crypto, found_terms = detect_crypto_content(text)
        print(f"   Результат: {'✅ КРИПТО' if is_crypto else '❌ НЕ КРИПТО'}")
        if found_terms:
            print(f"   Найдено: {found_terms}")
        print()
    
    # Специальный тест с описанием из логов
    real_description = """На изображении показан график криптовалютной пары PEPE/USDT на бирже OKX. График отображает динамику цены за последние 15 минут. Видны свечные бары, показывающие изменения цены в течение этого периода. На графике также нанесены скользящие средние (EMA) с периодами 20, 50, 100 и 200. В правой части экрана отображаются текущие значения цены, максимальное и минимальное значения за выбранный период. В верхней части экрана показаны кнопки для покупки и продажи по текущим ценам. В нижней части экрана расположены вкладки для навигации по приложению: "Котировки", "График", "Обзор", "Сообщество" и "Меню". Время на устройстве — 14:34, дата — суббота, 21 июня. Уровень заряда батареи — 41%."""
    
    print("🎯 РЕАЛЬНЫЙ ТЕСТ (из логов):")
    print(f"Текст: {real_description[:100]}...")
    is_crypto, found_terms = detect_crypto_content(real_description)
    print(f"Результат: {'✅ КРИПТО' if is_crypto else '❌ НЕ КРИПТО'}")
    print(f"Найдено терминов: {len(found_terms)}")
    print(f"Термины: {found_terms}")

if __name__ == "__main__":
    test_crypto_detector()