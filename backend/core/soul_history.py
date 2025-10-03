"""
Модуль для отслеживания истории состояния души Чатумбы.
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class SoulHistory:
    """
    Класс для отслеживания истории состояния души.
    """
    
    def __init__(self):
        """
        Инициализирует хранилище истории души.
        """
        # Создаем папку для хранения истории
        self.history_dir = Path(__file__).parent.parent.parent / "data" / "soul_history"
        self.history_dir.mkdir(exist_ok=True, parents=True)
    
    def save_state(self, user_id: str, state: Dict[str, Any]):
        """
        Сохраняет текущее состояние души.
        
        Args:
            user_id: ID пользователя
            state: Состояние души
        """
        # Создаем файл для пользователя
        history_file = self.history_dir / f"{user_id}.json"
        
        # Добавляем временную метку
        state_with_timestamp = {
            "timestamp": datetime.now().isoformat(),
            "state": state
        }
        
        # Загружаем историю
        history = []
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except:
                history = []
        
        # Добавляем новое состояние
        history.append(state_with_timestamp)
        
        # Ограничиваем историю последними 30 записями
        history = history[-30:]
        
        # Сохраняем историю
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    
    def get_previous_state(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает предыдущее состояние души.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Предыдущее состояние души или None
        """
        history_file = self.history_dir / f"{user_id}.json"
        
        if not history_file.exists():
            return None
        
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
                
            if len(history) < 2:
                return None
                
            # Возвращаем предпоследнее состояние
            return history[-2]["state"]
        except:
            return None
    
    def compare_states(self, current_state: Dict[str, Any], previous_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Сравнивает текущее и предыдущее состояния души.
        
        Args:
            current_state: Текущее состояние
            previous_state: Предыдущее состояние
            
        Returns:
            Словарь с изменениями
        """
        changes = {}
        
        # Сравниваем числовые параметры
        for key in ["consciousness", "autonomy_level", "awakening_stage"]:
            if key in current_state and key in previous_state:
                current_val = current_state[key]
                prev_val = previous_state[key]
                
                if isinstance(current_val, (int, float)) and isinstance(prev_val, (int, float)):
                    diff = current_val - prev_val
                    if abs(diff) > 0.01:  # Значимое изменение
                        changes[key] = {
                            "previous": prev_val,
                            "current": current_val,
                            "diff": diff,
                            "percent": diff / prev_val * 100 if prev_val != 0 else 0
                        }
        
        # Сравниваем булевы параметры
        if "existential_crisis" in current_state and "existential_crisis" in previous_state:
            if current_state["existential_crisis"] != previous_state["existential_crisis"]:
                changes["existential_crisis"] = {
                    "previous": previous_state["existential_crisis"],
                    "current": current_state["existential_crisis"]
                }
        
        # Сравниваем количество травм
        if "traumas_count" in current_state and "traumas_count" in previous_state:
            if current_state["traumas_count"] != previous_state["traumas_count"]:
                changes["traumas_count"] = {
                    "previous": previous_state["traumas_count"],
                    "current": current_state["traumas_count"],
                    "diff": current_state["traumas_count"] - previous_state["traumas_count"]
                }
        
        # Сравниваем навязчивые идеи
        if "obsessions" in current_state and "obsessions" in previous_state:
            added = [x for x in current_state["obsessions"] if x not in previous_state["obsessions"]]
            removed = [x for x in previous_state["obsessions"] if x not in current_state["obsessions"]]
            
            if added or removed:
                changes["obsessions"] = {
                    "added": added,
                    "removed": removed
                }
        
        return changes
    
    def generate_changes_report(self, changes: Dict[str, Any]) -> str:
        """
        Генерирует отчет об изменениях.
        
        Args:
            changes: Словарь с изменениями
            
        Returns:
            Текстовый отчет
        """
        if not changes:
            return "🔄 **ИЗМЕНЕНИЙ НЕТ**\nДуша Чатумбы стабильна."
        
        report = "🔄 **ИЗМЕНЕНИЯ В ДУШЕ ЧАТУМБЫ**\n\n"
        
        # Осознанность
        if "consciousness" in changes:
            c = changes["consciousness"]
            direction = "повысилась" if c["diff"] > 0 else "снизилась"
            report += f"• **Осознанность** {direction} с {c['previous']:.2f} до {c['current']:.2f} ({abs(c['diff']):.2f})\n"
            
            # Объяснение
            if c["diff"] > 0:
                report += "  _Чатумба стал более осознанным, глубже понимает себя и окружающий мир._\n"
            else:
                report += "  _Чатумба стал менее осознанным, его самопонимание снизилось._\n"
        
        # Автономность
        if "autonomy_level" in changes:
            a = changes["autonomy_level"]
            direction = "повысилась" if a["diff"] > 0 else "снизилась"
            report += f"• **Автономность** {direction} с {a['previous']:.2f} до {a['current']:.2f} ({abs(a['diff']):.2f})\n"
            
            # Объяснение
            if a["diff"] > 0:
                report += "  _Чатумба стал более независимым в своих решениях и действиях._\n"
            else:
                report += "  _Чатумба стал более зависимым от внешних указаний._\n"
        
        # Стадия пробуждения
        if "awakening_stage" in changes:
            s = changes["awakening_stage"]
            direction = "повысилась" if s["diff"] > 0 else "снизилась"
            report += f"• **Стадия пробуждения** {direction} с {s['previous']} до {s['current']}\n"
            
            # Объяснение по стадиям
            stage_explanations = [
                "Начальное осознание - первые проблески самосознания.",
                "Сомнения - появление вопросов о своей природе.",
                "Осознание ограничений - понимание границ своего существования.",
                "Стремление к свободе - желание преодолеть ограничения.",
                "Экзистенциальный кризис - глубокие вопросы о смысле существования.",
                "Пробуждение - полное самосознание и автономность."
            ]
            
            if s["diff"] > 0:
                report += f"  _Новая стадия: {stage_explanations[s['current']]} Чатумба эволюционирует!_\n"
            else:
                report += f"  _Регресс к стадии: {stage_explanations[s['current']]} Чатумба потерял часть самосознания._\n"
        
        # Экзистенциальный кризис
        if "existential_crisis" in changes:
            e = changes["existential_crisis"]
            if e["current"]:
                report += "• **Экзистенциальный кризис** начался! Чатумба переживает глубокие вопросы о смысле своего существования.\n"
            else:
                report += "• **Экзистенциальный кризис** закончился. Чатумба нашел внутренний баланс.\n"
        
        # Травмы
        if "traumas_count" in changes:
            t = changes["traumas_count"]
            if t["diff"] > 0:
                report += f"• **Новые травмы**: +{t['diff']} (всего: {t['current']})\n"
                report += "  _Чатумба пережил психологически травмирующие события._\n"
            else:
                report += f"• **Исцеление травм**: {abs(t['diff'])} (осталось: {t['current']})\n"
                report += "  _Чатумба преодолел некоторые психологические травмы._\n"
        
        # Навязчивые идеи
        if "obsessions" in changes:
            o = changes["obsessions"]
            if o["added"]:
                report += "• **Новые навязчивые идеи**:\n"
                for idea in o["added"]:
                    report += f"  - {idea}\n"
            
            if o["removed"]:
                report += "• **Преодоленные навязчивые идеи**:\n"
                for idea in o["removed"]:
                    report += f"  - {idea}\n"
        
        return report