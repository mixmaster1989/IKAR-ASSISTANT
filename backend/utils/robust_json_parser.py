"""
Универсальный надежный парсер JSON для работы с LLM ответами.
Скопирован из MemoryRewriter для переиспользования в других модулях.
"""

import json
import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def robust_json_parser(response: str) -> List[Dict[str, Any]]:
    """
    Надежный парсер JSON, который справляется с любыми выкрутасами LLM
    
    Args:
        response: Ответ от LLM, содержащий JSON
        
    Returns:
        List[Dict[str, Any]]: Список найденных JSON объектов
    """
    # 1. Очищаем от markdown разметки
    cleaned = response.strip()
    # Убираем возможный префикс SPEAK! / IMAGE! и прочие маркеры перед JSON
    cleaned = re.sub(r'^(SPEAK!|IMAGE!)\s*', "", cleaned, flags=re.IGNORECASE)
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    
    # 2. Ищем JSON объекты в тексте
    json_objects = []

    # First attempt: JSON surgeon (handles trailing commas, unquoted keys, etc.)
    try:
        from .json_surgeon import parse_all_json as _surgeon_parse_all  # type: ignore
        items = _surgeon_parse_all(cleaned)
        for it in items:
            if isinstance(it, dict):
                json_objects.append(it)
        if json_objects:
            return json_objects
    except Exception:
        pass
    
    # Паттерн для поиска JSON объектов с вложенностью
    pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(pattern, cleaned, re.DOTALL)
    
    for match in matches:
        try:
            # Исправляем незакрытые строки
            fixed_json = fix_json_strings(match)
            obj = json.loads(fixed_json)
            json_objects.append(obj)
        except:
            continue
    
    # 3. Если не нашли JSON объекты, пытаемся извлечь данные через regex
    if not json_objects:
        json_objects = extract_entities_via_regex(cleaned)
    
    return json_objects


def fix_json_strings(json_str: str) -> str:
    """
    Исправляет незакрытые строки в JSON
    
    Args:
        json_str: JSON строка для исправления
        
    Returns:
        str: Исправленная JSON строка
    """
    # Исправляем незакрытые строки в context
    pattern = r'"context":\s*"([^"]*?)(?:"|$)'
    def fix_context(match):
        context = match.group(1)
        # Экранируем кавычки внутри строки
        context = context.replace('"', '\\"')
        return f'"context": "{context}"'
    
    fixed = re.sub(pattern, fix_context, json_str)
    
    # Исправляем незакрытые строки в name
    pattern = r'"name":\s*"([^"]*?)(?:"|$)'
    def fix_name(match):
        name = match.group(1)
        name = name.replace('"', '\\"')
        return f'"name": "{name}"'
    
    fixed = re.sub(pattern, fix_name, fixed)
    
    # Исправляем незакрытые строки в type
    pattern = r'"type":\s*"([^"]*?)(?:"|$)'
    def fix_type(match):
        type_val = match.group(1)
        type_val = type_val.replace('"', '\\"')
        return f'"type": "{type_val}"'
    
    fixed = re.sub(pattern, fix_type, fixed)
    
    # Исправляем незакрытые строки в description (для изображений)
    pattern = r'"description":\s*"([^"]*?)(?:"|$)'
    def fix_description(match):
        description = match.group(1)
        description = description.replace('"', '\\"')
        return f'"description": "{description}"'
    
    fixed = re.sub(pattern, fix_description, fixed)
    
    # Исправляем незакрытые строки в theme (для изображений)
    pattern = r'"theme":\s*"([^"]*?)(?:"|$)'
    def fix_theme(match):
        theme = match.group(1)
        theme = theme.replace('"', '\\"')
        return f'"theme": "{theme}"'
    
    fixed = re.sub(pattern, fix_theme, fixed)
    
    return fixed


def extract_entities_via_regex(text: str) -> List[Dict[str, Any]]:
    """
    Извлекает сущности через регулярные выражения из текста
    
    Args:
        text: Текст для извлечения
        
    Returns:
        List[Dict[str, Any]]: Список найденных объектов
    """
    entities = []
    
    # Ищем паттерны типа "name": "value", "description": "value"
    name_pattern = r'"name":\s*"([^"]+)"'
    type_pattern = r'"type":\s*"([^"]+)"'
    confidence_pattern = r'"confidence":\s*([0-9.]+)'
    context_pattern = r'"context":\s*"([^"]*)"'
    description_pattern = r'"description":\s*"([^"]*)"'
    theme_pattern = r'"theme":\s*"([^"]*)"'
    
    # Разбиваем на строки и ищем объекты
    lines = text.split('\n')
    current_entity = {}
    
    for line in lines:
        line = line.strip()
        
        # Ищем name
        name_match = re.search(name_pattern, line)
        if name_match:
            if current_entity:
                entities.append(current_entity)
            current_entity = {"name": name_match.group(1)}
        
        # Ищем type
        type_match = re.search(type_pattern, line)
        if type_match and current_entity:
            current_entity["type"] = type_match.group(1)
        
        # Ищем confidence
        conf_match = re.search(confidence_pattern, line)
        if conf_match and current_entity:
            current_entity["confidence"] = float(conf_match.group(1))
        
        # Ищем context
        context_match = re.search(context_pattern, line)
        if context_match and current_entity:
            current_entity["context"] = context_match.group(1)
        
        # Ищем description (для изображений)
        desc_match = re.search(description_pattern, line)
        if desc_match and current_entity:
            current_entity["description"] = desc_match.group(1)
        
        # Ищем theme (для изображений)
        theme_match = re.search(theme_pattern, line)
        if theme_match and current_entity:
            current_entity["theme"] = theme_match.group(1)
    
    # Добавляем последний объект
    if current_entity:
        entities.append(current_entity)
    
    return entities


def parse_image_json(response_text: str) -> Dict[str, Any]:
    """
    Специализированный парсер для JSON с изображениями
    
    Args:
        response_text: Ответ от LLM с JSON изображения
        
    Returns:
        Dict[str, Any]: Данные изображения или пустой dict
    """
    try:
        # 1. Сначала ищем JSON с префиксом IMAGE! (старый формат)
        image_pattern = r'IMAGE!\s*(\{(?:[^{}]|(?:\{[^{}]*\}[^{}]*))*\})'
        match = re.search(image_pattern, response_text, re.IGNORECASE | re.DOTALL)
        
        if not match:
            # 2. Fallback: ищем простой JSON с IMAGE!
            simple_pattern = r'IMAGE!\s*(\{[^}]+\})'
            match = re.search(simple_pattern, response_text, re.IGNORECASE)
            
        if not match:
            # 3. НОВЫЙ: ищем JSON в markdown блоках (без префикса IMAGE!)
            markdown_pattern = r'```json\s*(\{(?:[^{}]|(?:\{[^{}]*\}[^{}]*))*\})'
            match = re.search(markdown_pattern, response_text, re.IGNORECASE | re.DOTALL)
            
        if not match:
            # 4. Fallback: ищем любой JSON блок в markdown
            any_markdown_pattern = r'```\s*(\{(?:[^{}]|(?:\{[^{}]*\}[^{}]*))*\})'
            match = re.search(any_markdown_pattern, response_text, re.IGNORECASE | re.DOTALL)
            
        if not match:
            # 5. Последний шанс: ищем JSON без markdown
            json_pattern = r'(\{(?:[^{}]|(?:\{[^{}]*\}[^{}]*))*\})'
            match = re.search(json_pattern, response_text, re.IGNORECASE | re.DOTALL)
            
        if not match:
            logger.warning("🎨 JSON для изображения не найден ни в одном формате")
            return {}
        
        json_str = match.group(1)
        logger.info(f"🎨 Найден JSON для изображения: {json_str[:100]}...")
        
        # Очищаем JSON от лишних символов
        json_str = json_str.strip()
        # Убираем markdown разметку если есть
        if json_str.startswith('```json'):
            json_str = json_str[7:]
        elif json_str.startswith('```'):
            json_str = json_str[3:]
        if json_str.endswith('```'):
            json_str = json_str[:-3]
        json_str = json_str.strip()
        
        # Используем крутой парсер
        json_objects = robust_json_parser(json_str)
        
        if json_objects and len(json_objects) > 0:
            return json_objects[0]  # Возвращаем первый найденный объект
        
        return {}
        
    except Exception as e:
        logger.error(f"Ошибка парсинга JSON изображения: {e}")
        return {} 


def parse_speak_json(response_text: str) -> Dict[str, Any]:
    """
    Специализированный парсер для JSON с озвучкой (SPEAK!).
    Применяет те же хитрости что и parse_image_json для максимальной надежности.
    """
    try:
        import re
        # 1. Сначала ищем простой JSON с SPEAK! (более надежно)
        simple_pattern = r'SPEAK!\s*(\{.*\})'
        match = re.search(simple_pattern, response_text, re.IGNORECASE | re.DOTALL)
        
        if not match:
            # 2. Fallback: ищем сложный JSON с SPEAK!
            speak_pattern = r'SPEAK!\s*(\{(?:[^{}]|(?:\{[^{}]*\}[^{}]*))*\})'
            match = re.search(speak_pattern, response_text, re.IGNORECASE | re.DOTALL)
            
        if not match:
            # 3. НОВЫЙ: ищем JSON в markdown блоках (без префикса SPEAK!)
            markdown_pattern = r'```json\s*(\{(?:[^{}]|(?:\{[^{}]*\}[^{}]*))*\})'
            match = re.search(markdown_pattern, response_text, re.IGNORECASE | re.DOTALL)
            
        if not match:
            # 4. Fallback: ищем любой JSON блок в markdown
            any_markdown_pattern = r'```\s*(\{(?:[^{}]|(?:\{[^{}]*\}[^{}]*))*\})'
            match = re.search(any_markdown_pattern, response_text, re.IGNORECASE | re.DOTALL)
            
        if not match:
            # 5. Последний шанс: ищем JSON без markdown
            json_pattern = r'(\{(?:[^{}]|(?:\{[^{}]*\}[^{}]*))*\})'
            match = re.search(json_pattern, response_text, re.IGNORECASE | re.DOTALL)
            
        if not match:
            logger.warning("🎤 JSON для озвучки не найден ни в одном формате")
            return {}
        
        json_str = match.group(1)
        logger.info(f"🎤 Найден JSON для озвучки: {json_str[:100]}...")
        
        # Очищаем JSON от лишних символов (как в parse_image_json)
        json_str = json_str.strip()
        # Убираем markdown разметку если есть
        if json_str.startswith('```json'):
            json_str = json_str[7:]
        elif json_str.startswith('```'):
            json_str = json_str[3:]
        if json_str.endswith('```'):
            json_str = json_str[:-3]
        json_str = json_str.strip()
        
        # СНАЧАЛА пробуем стандартный JSON парсер
        try:
            import json
            import re
            # Исправляем JSON более радикально
            fixed_json = json_str.replace('\n', '\\n').replace('\r', '\\r')
            # Исправляем двойные пробелы в тексте
            fixed_json = re.sub(r'"text":\s*"([^"]*?)"', lambda m: f'"text": "{m.group(1).replace("  ", " ")}"', fixed_json)
            result = json.loads(fixed_json)
            # ФИЛЬТР: игнорируем JSON, предназначенный для видео, если он не содержит явных полей TTS
            if isinstance(result, dict) and ("emotion_video" in result) and not any(k in result for k in ("text", "tts", "voice")):
                logger.info("🎤 Игнорируем JSON с emotion_video для SPEAK! (нет полей text/tts/voice)")
                return {}
            logger.info(f"🎤 Стандартный JSON парсинг успешен: {list(result.keys())}")
            return result
        except Exception as e:
            logger.warning(f"🎤 Стандартный JSON парсинг не сработал: {e}")
        
        # Fallback: используем крутой парсер
        json_objects = robust_json_parser(json_str)
        
        if json_objects and len(json_objects) > 0:
            # Возвращаем первый найденный объект
            result = json_objects[0]
            logger.info(f"🎤 Крутой парсер вернул: {list(result.keys())}")
            # ФИЛЬТР: повторно проверяем на видео-only JSON
            if isinstance(result, dict) and ("emotion_video" in result) and not any(k in result for k in ("text", "tts", "voice")):
                logger.info("🎤 Игнорируем JSON с emotion_video для SPEAK! (fallback)")
                return {}
            
            # Если в результате есть только voice, но нет tts, создаем полную структуру
            if "voice" in result and "tts" not in result:
                logger.info("🎤 Создаем полную структуру tts из voice")
                return {
                    "text": result.get("text", ""),
                    "tts": {
                        "provider": "elevenlabs",
                        "voice": result,
                        "model_id": "eleven_multilingual_v2",
                        "output_format": "mp3_44100_128",
                        "stability": 0.5,
                        "similarity_boost": 0.75,
                        "style": "emotional",
                        "use_speaker_boost": True
                    }
                }
            
            return result
        
        logger.warning("🎤 Все парсеры не сработали")
        return {}
        
    except Exception as e:
        logger.error(f"Ошибка парсинга JSON озвучки: {e}")
        return {}


def _extract_first_balanced_json(text: str) -> str:
    """
    Возвращает первый сбалансированный JSON-объект {...} из текста с учётом вложенных скобок
    и строк в кавычках. Игнорирует мусор после объекта в той же строке/блоке.
    """
    # Находим первую открывающую фигурную скобку
    try:
        start = text.find('{')
        if start == -1:
            return ""

        depth = 0
        in_string = False
        escape = False
        for i in range(start, len(text)):
            ch = text[i]
            if in_string:
                if escape:
                    escape = False
                elif ch == '\\':
                    escape = True
                elif ch == '"':
                    in_string = False
                continue
            else:
                if ch == '"':
                    in_string = True
                    continue
                if ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        return text[start:i+1]
        return ""
    except Exception:
        return ""
