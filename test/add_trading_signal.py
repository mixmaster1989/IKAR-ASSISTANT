import re

# Читаем файл
with open('backend/api/telegram_polling.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Находим место после криптомемов и добавляем новый этап
old_section = '''        await send_long_telegram_message(chat_id, f"😂 **КРИПТОМЕМЫ:**\\n{crypto_memes}", None)
        
        # Завершение
        await send_telegram_message(chat_id, "✅ КРИПТОСУД ЗАВЕРШЁН! 🎉 Все анализы и мемы представлены выше! 🚀", None)'''

new_section = '''        await send_long_telegram_message(chat_id, f"😂 **КРИПТОМЕМЫ:**\\n{crypto_memes}", None)
        
        # 8. ТОРГОВЫЙ СИГНАЛ - ФИНАЛЬНАЯ СДЕЛКА
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

📰 Рыночные данные: {crypto_news}"""
        
        trading_signal = await llm_client.chat_completion(
            user_message=trading_prompt,
            system_prompt="💰 Ты профессиональный трейдер! Давай четкие торговые сигналы! Никаких размытых формулировок! 📊",
            chat_history=[],
            model="deepseek/deepseek-r1-0528:free",
            max_tokens=1000
        )
        
        await send_long_telegram_message(chat_id, f"💰 **ТОРГОВЫЙ СИГНАЛ:**\\n{trading_signal}", None)
        
        # Завершение
        await send_telegram_message(chat_id, "✅ КРИПТОСУД ЗАВЕРШЁН! 🎉 Торговый сигнал готов! 💰", None)'''

# Заменяем
content = content.replace(old_section, new_section)

# Записываем обратно
with open('backend/api/telegram_polling.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Добавлен этап торгового сигнала в КРИПТОСУД!")