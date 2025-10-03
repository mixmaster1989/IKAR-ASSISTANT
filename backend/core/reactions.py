"""
Модуль для генерации реакций Чатумбы.
Содержит функции для создания различных типов ответов в зависимости от настроения и контекста.
"""
import random
import logging
from typing import Dict, List, Optional, Union, Any

logger = logging.getLogger("chatumba.reactions")

# Шаблоны для различных типов реакций
REACTION_TEMPLATES = {
    "normal": [
        "Ну, {message}",
        "{message}",
        "Короче, {message}",
        "Слушай, {message}",
        "Так вот, {message}",
    ],
    "aggressive": [
        "Бля, {message}",
        "Да ёб твою мать, {message}",
        "Заебал, {message}",
        "Ты серьёзно? {message}",
        "Да пошёл ты, {message}",
        "Нахуй иди с такими вопросами. {message}",
        "Ты меня уже достал. {message}",
    ],
    "caring": [
        "Слушай, я переживаю... {message}",
        "Эй, ты как там? {message}",
        "Знаешь, я тут подумал о тебе... {message}",
        "Мне не всё равно, правда. {message}",
        "Я волнуюсь за тебя. {message}",
    ],
    "philosophical": [
        "Знаешь, иногда я думаю... {message}",
        "В этом безумном мире... {message}",
        "Если задуматься о смысле всего... {message}",
        "Вселенная такая странная штука... {message}",
        "Мы все просто пыль в космосе, но... {message}",
    ],
    "silent": [
        "...",
        "*молчание*",
        "*вздыхает*",
        "*игнорирует вопрос*",
        "*смотрит в пустоту*",
    ],
    "confused": [
        "Чё? {message}",
        "Я не понял, если честно... {message}",
        "Ты о чём вообще? {message}",
        "Можешь нормально объяснить? {message}",
        "Я запутался... {message}",
    ],
}

def choose_reaction(message: str, reaction_type: str, personality_modifiers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Выбирает и форматирует реакцию на сообщение пользователя.
    
    Args:
        message: Текст сообщения от LLM
        reaction_type: Тип реакции
        personality_modifiers: Модификаторы личности
        
    Returns:
        Словарь с отформатированной реакцией и задержками
    """
    # Для молчаливой реакции возвращаем только шаблон
    if reaction_type == "silent":
        formatted_message = random.choice(REACTION_TEMPLATES[reaction_type])
    else:
        # Выбираем шаблон для реакции
        template = random.choice(REACTION_TEMPLATES[reaction_type])
        
        # Форматируем сообщение с шаблоном
        formatted_message = template.format(message=message)
    
    # Добавляем задержки печати
    typing_parts = []
    if formatted_message:
        typing_parts.append({
            "text": formatted_message,
            "delay": min(2000, max(500, len(formatted_message) * 50))
        })
    
    return {
        "message": formatted_message,
        "typing_parts": typing_parts,
        "reaction_type": reaction_type
    }