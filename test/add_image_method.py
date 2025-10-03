import re

# Читаем файл
with open('backend/llm/openrouter.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Добавляем новый метод для работы с изображениями
new_method = '''
    async def chat_completion_with_image(
        self, 
        user_message: str, 
        image_base64: str,
        system_prompt: str = "",
        model: str = "qwen/qwen2.5-vl-72b-instruct:free",
        max_tokens: int = 2000
    ) -> Optional[str]:
        """
        Генерирует ответ на сообщение с изображением.
        """
        if not self.api_keys:
            logger.error("❌ OPENROUTER API КЛЮЧИ НЕ НАСТРОЕНЫ!")
            return None
        
        # Формируем сообщения для vision модели
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": user_message
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}"
                    }
                }
            ]
        })
        
        params = {"max_tokens": max_tokens}
        
        logger.info(f"🖼️ ОТПРАВЛЯЕМ ЗАПРОС С ИЗОБРАЖЕНИЕМ К {model}")
        
        # Пробуем все ключи
        for api_key in self.api_keys:
            key_suffix = api_key[-10:] if len(api_key) > 10 else api_key
            logger.info(f"🔑 ПРОБУЕМ КЛЮЧ: ...{key_suffix}")
            
            result = await self._try_model_with_key(model, messages, params, api_key)
            
            if result and result != "RATE_LIMIT_EXCEEDED":
                logger.info(f"✅ ПОЛУЧЕН ОТВЕТ С ИЗОБРАЖЕНИЕМ: {result[:100]}...")
                return result
            elif result == "RATE_LIMIT_EXCEEDED":
                logger.warning(f"⚠️ ЛИМИТ ИСЧЕРПАН для ключа ...{key_suffix}")
                continue
            
            await asyncio.sleep(1)
        
        logger.error("❌ ВСЕ КЛЮЧИ НЕДОСТУПНЫ ДЛЯ АНАЛИЗА ИЗОБРАЖЕНИЙ")
        return None'''

# Вставляем новый метод перед последним методом chat_completion
insert_position = content.rfind('    async def chat_completion(')
content = content[:insert_position] + new_method + '\n\n' + content[insert_position:]

# Записываем обратно
with open('backend/llm/openrouter.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Добавлен метод chat_completion_with_image в OpenRouter клиент!")