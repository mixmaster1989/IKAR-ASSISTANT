import re

# Читаем файл
with open('backend/api/telegram_polling.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Заменяем блок с криптодетекцией
old_block = '''        if image_description:
            # Проверяем на криптоконтент
            is_crypto, crypto_terms = detect_crypto_content(image_description)
            
            logger.info(f"[КРИПТОДЕТЕКТОР] Результат детекции: is_crypto={is_crypto}, terms={crypto_terms}")
            
            if is_crypto:
                logger.info(f"[КРИПТОДЕТЕКТОР] Обнаружен криптоконтент в группе {chat_id}: {crypto_terms}")
                # Запускаем КРИПТОСУД!
                await cryptosud_analysis(chat_id, image_description, crypto_terms)
            else:
                logger.info(f"[КРИПТОДЕТЕКТОР] Криптоконтент не обнаружен в группе {chat_id}")'''

new_block = '''        if image_description:
            logger.info(f"[КРИПТОДЕТЕКТОР] Полное описание: {image_description}")
            # Проверяем на криптоконтент
            is_crypto, crypto_terms = detect_crypto_content(image_description)
            
            logger.info(f"[КРИПТОДЕТЕКТОР] Результат детекции: is_crypto={is_crypto}, terms={crypto_terms}")
            
            if is_crypto:
                logger.info(f"[КРИПТОДЕТЕКТОР] ✅ ОБНАРУЖЕН КРИПТОКОНТЕНТ! Запускаю КРИПТОСУД для группы {chat_id}")
                logger.info(f"[КРИПТОДЕТЕКТОР] Найденные термины: {crypto_terms}")
                # Запускаем КРИПТОСУД!
                try:
                    await cryptosud_analysis(chat_id, image_description, crypto_terms)
                    logger.info(f"[КРИПТОДЕТЕКТОР] ✅ КРИПТОСУД успешно завершен для группы {chat_id}")
                except Exception as e:
                    logger.error(f"[КРИПТОДЕТЕКТОР] ❌ Ошибка в КРИПТОСУДЕ: {e}")
            else:
                logger.info(f"[КРИПТОДЕТЕКТОР] ❌ Криптоконтент не обнаружен в группе {chat_id}")'''

# Заменяем
content = content.replace(old_block, new_block)

# Записываем обратно
with open('backend/api/telegram_polling.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Исправлено! Добавлены отладочные логи в криптодетектор.")