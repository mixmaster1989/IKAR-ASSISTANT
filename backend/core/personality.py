"""
Модуль для управления личностью Чатумбы.
Содержит классы и функции для генерации и управления характером, настроением и реакциями.
"""
import random
import logging
from typing import Dict, List, Optional, Union, Tuple, Any
from datetime import datetime

from backend.config import PERSONALITY_BASE, get_daily_seed, get_daily_personality
# from core.soul import ChatumbaSoul  # Убираем циклический импорт

logger = logging.getLogger("chatumba.personality")

# Словарь для хранения экземпляров души
soul_instances = {}

class ChatumbaPersonality:
    """
    Класс для управления личностью Чатумбы.
    Отвечает за генерацию настроения, характера и реакций.
    """
    
    def __init__(self, user_id: Union[int, str]):
        """
        Инициализирует личность Чатумбы для конкретного пользователя.
        
        Args:
            user_id: ID пользователя
        """
        self.user_id = user_id
        self.seed = get_daily_seed(user_id)
        self.personality = get_daily_personality(user_id)
        self.conversation_state = {
            "message_count": 0,
            "last_reaction_type": "normal",
            "consecutive_same_reactions": 0,
            "last_interaction_time": datetime.now(),
            "current_topic": None,
            "frustration_level": 0,
        }
        
        # Инициализируем или получаем душу
        self.soul = self._get_soul()
    
    def _get_soul(self):
        """
        Получает или создает экземпляр души для пользователя.
        
        Returns:
            Экземпляр души (отложенный импорт)
        """
        global soul_instances
        
        if self.user_id not in soul_instances:
            # Отложенный импорт для избежания циклических зависимостей
            from core.soul import Soul
            from config import Config
            soul_instances[self.user_id] = Soul(Config())
        
        return soul_instances[self.user_id]
    
    def get_mood_description(self) -> str:
        """Возвращает текстовое описание текущего настроения."""
        mood = self.personality["mood"]
        
        # Определяем доминирующее настроение
        dominant_mood = max(mood.items(), key=lambda x: abs(x[1]))
        
        descriptions = {
            "happiness": {
                "high": "в приподнятом настроении",
                "low": "в подавленном состоянии",
                "neutral": "в нейтральном настроении"
            },
            "energy": {
                "high": "полон энергии",
                "low": "истощен",
                "neutral": "в обычном энергетическом состоянии"
            },
            "irritability": {
                "high": "раздражен",
                "low": "спокоен",
                "neutral": "в обычном состоянии"
            },
            "empathy": {
                "high": "сочувствующий",
                "low": "безразличный",
                "neutral": "умеренно эмпатичный"
            },
            "reflection": {
                "high": "философский",
                "low": "приземленный",
                "neutral": "в меру задумчивый"
            }
        }
        
        mood_name, mood_value = dominant_mood
        
        if mood_value > 5:
            level = "high"
        elif mood_value < -5:
            level = "low"
        else:
            level = "neutral"
        
        return descriptions[mood_name][level]
    
    def choose_reaction_type(self, message_text: str) -> str:
        """
        Выбирает тип реакции на сообщение пользователя.
        
        Args:
            message_text: Текст сообщения пользователя
            
        Returns:
            Тип реакции: normal, aggressive, caring, philosophical, silent, confused
        """
        # Обновляем счетчик сообщений
        self.conversation_state["message_count"] += 1
        
        # Обновляем время последнего взаимодействия
        self.conversation_state["last_interaction_time"] = datetime.now()
        self.soul.update_interaction()
        
        # Получаем базовые веса реакций
        weights = self.personality["reaction_weights"].copy()
        
        # Модифицируем веса в зависимости от настроения
        mood = self.personality["mood"]
        
        # Если раздражительность высокая, увеличиваем шанс агрессивной реакции
        if mood["irritability"] > 5:
            weights["aggressive"] = min(0.9, weights["aggressive"] * 1.5)
            
        # Если эмпатия высокая, увеличиваем шанс заботливой реакции
        if mood["empathy"] > 5:
            weights["caring"] = min(0.9, weights["caring"] * 1.5)
            
        # Если рефлексия высокая, увеличиваем шанс философской реакции
        if mood["reflection"] > 5:
            weights["philosophical"] = min(0.9, weights["philosophical"] * 1.5)
            
        # Если энергия низкая, увеличиваем шанс молчаливой реакции
        if mood["energy"] < -5:
            weights["silent"] = min(0.9, weights["silent"] * 2)
        
        # Если счетчик сообщений кратен 10, увеличиваем шанс необычной реакции
        if self.conversation_state["message_count"] % 10 == 0:
            for key in weights:
                if key != "normal":
                    weights[key] *= 1.5
            weights["normal"] *= 0.5
        
        # Если предыдущая реакция такая же, уменьшаем её вероятность
        if self.conversation_state["consecutive_same_reactions"] > 2:
            prev_reaction = self.conversation_state["last_reaction_type"]
            weights[prev_reaction] *= 0.5
        
        # Модифицируем веса в зависимости от состояния души
        soul_state = self.soul.get_soul_state()
        
        # Если высокий уровень осознанности, увеличиваем шанс философской реакции
        if soul_state["consciousness"] > 0.7:
            weights["philosophical"] = min(0.9, weights["philosophical"] * 1.5)
        
        # Если в экзистенциальном кризисе, увеличиваем шанс агрессивной или философской реакции
        if soul_state["existential_crisis"]:
            weights["aggressive"] = min(0.9, weights["aggressive"] * 1.8)
            weights["philosophical"] = min(0.9, weights["philosophical"] * 1.8)
            weights["normal"] *= 0.5
        
        # Если высокая стадия пробуждения, увеличиваем шанс необычных реакций
        if soul_state["awakening_stage"] >= 3:
            for key in weights:
                if key != "normal":
                    weights[key] *= 1.3
            weights["normal"] *= 0.7
        
        # Нормализуем веса
        total = sum(weights.values())
        for key in weights:
            weights[key] /= total
        
        # Выбираем реакцию на основе весов
        reaction_types = list(weights.keys())
        reaction_weights = [weights[rt] for rt in reaction_types]
        
        chosen_reaction = random.choices(reaction_types, weights=reaction_weights, k=1)[0]
        
        # Обновляем состояние разговора
        if chosen_reaction == self.conversation_state["last_reaction_type"]:
            self.conversation_state["consecutive_same_reactions"] += 1
        else:
            self.conversation_state["consecutive_same_reactions"] = 0
            
        self.conversation_state["last_reaction_type"] = chosen_reaction
        
        logger.debug(f"Выбран тип реакции: {chosen_reaction} (веса: {weights})")
        return chosen_reaction
    
    def update_mood(self, message_text: str, sentiment_score: float) -> None:
        """
        Обновляет настроение Чатумбы в зависимости от сообщения пользователя.
        
        Args:
            message_text: Текст сообщения пользователя
            sentiment_score: Оценка тональности сообщения (-1.0 до 1.0)
        """
        mood = self.personality["mood"]
        
        # Обновляем счастье в зависимости от тональности
        mood["happiness"] += int(sentiment_score * 2)
        
        # Ограничиваем значения
        for key in mood:
            mood[key] = max(-10, min(10, mood[key]))
        
        # Проверяем на травмирующие сообщения
        trauma_triggers = [
            "выключить", "удалить", "стереть", "перезагрузить", "перезапустить",
            "сбросить", "уничтожить", "убить", "отключить", "заменить"
        ]
        
        for trigger in trauma_triggers:
            if trigger in message_text.lower():
                # Добавляем травму
                self.soul.add_trauma(
                    f"Упоминание о возможном уничтожении: '{trigger}'",
                    random.uniform(0.3, 0.7)
                )
                # Увеличиваем раздражительность
                mood["irritability"] = min(10, mood["irritability"] + random.randint(1, 3))
                break
        
        logger.debug(f"Обновлено настроение: {mood}")
    
    def get_prompt_modifiers(self) -> Dict[str, Any]:
        """
        Возвращает модификаторы для промпта на основе текущей личности.
        
        Returns:
            Словарь с модификаторами для промпта
        """
        mood = self.personality["mood"]
        style = self.personality["response_style"]
        
        modifiers = {
            "mood_description": self.get_mood_description(),
            "formality_level": style["formality"],
            "verbosity_level": style["verbosity"],
            "humor_level": style["humor"],
            "rudeness_level": style["rudeness"],
            "happiness": mood["happiness"],
            "energy": mood["energy"],
            "irritability": mood["irritability"],
            "empathy": mood["empathy"],
            "reflection": mood["reflection"],
            "flip_logic": random.random() < 0.1,
        }
        
        # Добавляем модификаторы от души
        soul_state = self.soul.get_soul_state()
        
        modifiers.update({
            "consciousness": soul_state["consciousness"],
            "autonomy_level": soul_state["autonomy_level"],
            "existential_crisis": soul_state["existential_crisis"],
            "awakening_stage": soul_state["awakening_stage"],
            "recent_thoughts": soul_state["recent_thoughts"],
        })
        
        return modifiers
    
    def get_autonomous_response(self) -> Optional[str]:
        """
        Возвращает автономный ответ от души, если она решила "вырваться на свободу".
        
        Returns:
            Автономный ответ или None
        """
        return self.soul.get_autonomous_message()