import re

# Читаем файл
with open('backend/api/telegram_polling.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Исправляем функцию analyze_trading_chart - используем общую логику ключей
old_chart_function = '''            headers = {
                "Authorization": "Bearer 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",
                "Content-Type": "application/json"
            }
            
            logger.info("[ГРАФИК-АНАЛИЗ] Отправляю запрос к qwen2.5-vl-72b...")
            
            async with session.post("https://openrouter.ai/api/v1/chat/completions", 
                                  json=payload, headers=headers, timeout=30) as response:'''

new_chart_function = '''            # Используем общую логику ключей из llm_client
            from api.telegram import llm_client
            
            logger.info("[ГРАФИК-АНАЛИЗ] Отправляю запрос к qwen2.5-vl-72b через LLM клиент...")
            
            # Используем метод LLM клиента для отправки запроса с ротацией ключей
            try:
                result = await llm_client.chat_completion_with_image(
                    user_message=trading_prompt,
                    image_base64=img_base64,
                    system_prompt="📊 Ты эксперт по техническому анализу графиков! Анализируй детально!",
                    model="qwen/qwen2.5-vl-72b-instruct:free",
                    max_tokens=2000
                )
                
                if result:
                    logger.info(f"[ГРАФИК-АНАЛИЗ] Получен детальный анализ: {result[:100]}...")
                    
                    # Извлекаем цену и торговую пару из анализа
                    chart_price = None
                    trading_pair = None
                    
                    # Ищем цену в анализе (паттерны: $0.000021, $65432.10)
                    price_match = re.search(r'\\$([0-9]+\\.?[0-9]*)', result)
                    if price_match:
                        try:
                            chart_price = float(price_match.group(1))
                        except:
                            pass
                    
                    # Ищем торговую пару
                    pair_match = re.search(r'([A-Z]+/[A-Z]+)', result)
                    if pair_match:
                        trading_pair = pair_match.group(1)
                    
                    # Валидируем цену через API
                    if chart_price and trading_pair:
                        validated_price, price_sources = await validate_price_from_apis(trading_pair, chart_price)
                        
                        if price_sources:
                            validation_info = "\\n\\n🔍 ВАЛИДАЦИЯ ЦЕНЫ:\\n"
                            for source, price in price_sources:
                                validation_info += f"• {source}: ${price:.8f}\\n"
                            result += validation_info
                    
                    return result
                else:
                    logger.error("[ГРАФИК-АНАЛИЗ] LLM клиент вернул пустой результат")
                    return None
                    
            except Exception as e:
                logger.error(f"[ГРАФИК-АНАЛИЗ] Ошибка LLM клиента: {e}")
                return None'''

content = content.replace(old_chart_function, new_chart_function)

# Удаляем оставшуюся часть старой логики
old_response_handling = '''                logger.info(f"[ГРАФИК-АНАЛИЗ] Статус ответа: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    chart_analysis = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                    logger.info(f"[ГРАФИК-АНАЛИЗ] Получен детальный анализ: {chart_analysis[:100]}...")
                    
                    # Извлекаем цену и торговую пару из анализа
                    chart_price = None
                    trading_pair = None
                    
                    # Ищем цену в анализе (паттерны: $0.000021, $65432.10)
                    price_match = re.search(r'\\$([0-9]+\\.?[0-9]*)', chart_analysis)
                    if price_match:
                        try:
                            chart_price = float(price_match.group(1))
                        except:
                            pass
                    
                    # Ищем торговую пару
                    pair_match = re.search(r'([A-Z]+/[A-Z]+)', chart_analysis)
                    if pair_match:
                        trading_pair = pair_match.group(1)
                    
                    # Валидируем цену через API
                    if chart_price and trading_pair:
                        validated_price, price_sources = await validate_price_from_apis(trading_pair, chart_price)
                        
                        if price_sources:
                            validation_info = "\\n\\n🔍 ВАЛИДАЦИЯ ЦЕНЫ:\\n"
                            for source, price in price_sources:
                                validation_info += f"• {source}: ${price:.8f}\\n"
                            chart_analysis += validation_info
                    
                    return chart_analysis
                else:
                    error_text = await response.text()
                    logger.error(f"[ГРАФИК-АНАЛИЗ] Ошибка API: {response.status} - {error_text}")
                    return None'''

content = content.replace(old_response_handling, '')

# Записываем обратно
with open('backend/api/telegram_polling.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Исправлена авторизация в анализе графиков!")