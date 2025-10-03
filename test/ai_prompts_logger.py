#!/usr/bin/env python3
"""
🧠 ЛОГГЕР ПРОМПТОВ И ОТВЕТОВ AI МОДЕЛЕЙ
Отдельный файл логов для отслеживания взаимодействия с AI моделями
"""

import logging
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import hashlib
import time

class AIPromptsLogger:
    """Специализированный логгер для промптов и ответов AI моделей"""
    
    def __init__(self, log_file: str = "ai_prompts.log"):
        self.log_file = Path(log_file)
        self.setup_logger()
        
    def setup_logger(self):
        """Настройка логгера"""
        # Создаем форматтер с подробной информацией
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Создаем файловый обработчик
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # Создаем консольный обработчик
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Настраиваем основной логгер
        self.logger = logging.getLogger('ai_prompts')
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()  # Очищаем существующие обработчики
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.propagate = False  # Предотвращаем дублирование логов
        
        # ОТКЛЮЧАЕМ DEBUG ЛОГИ ОТ СТОРОННИХ БИБЛИОТЕК
        try:
            from internet_intelligence_logger import disable_third_party_debug_logs
            disable_third_party_debug_logs()
        except ImportError:
            # Fallback если функция недоступна
            third_party_loggers = ['htmldate', 'trafilatura', 'newspaper', 'readability', 'justext',
                                  'bs4', 'urllib3', 'aiohttp', 'asyncio', 'charset_normalizer',
                                  'requests', 'feedparser', 'nltk', 'lxml', 'html5lib']
            for logger_name in third_party_loggers:
                logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    def log_prompt_request(self, 
                          model: str, 
                          system_prompt: str, 
                          user_prompt: str, 
                          context: Dict[str, Any] = None,
                          request_id: str = None):
        """Логирование запроса промпта к AI модели"""
        if not request_id:
            request_id = self._generate_request_id()
        
        self.logger.info(f"🧠 AI ЗАПРОС: {request_id}")
        self.logger.info(f"   Модель: {model}")
        self.logger.info(f"   Системный промпт:")
        self.logger.info(f"   {system_prompt}")
        self.logger.info(f"   Пользовательский промпт:")
        self.logger.info(f"   {user_prompt}")
        
        if context:
            self.logger.info(f"   Контекст: {json.dumps(context, ensure_ascii=False, indent=2)}")
        
        # Сохраняем полные промпты в отдельный файл
        self._save_full_prompt(request_id, model, system_prompt, user_prompt, context)
        
        return request_id
    
    def log_prompt_response(self, 
                           request_id: str, 
                           response: str, 
                           model: str, 
                           tokens_used: int = None,
                           processing_time: float = None,
                           success: bool = True,
                           error: str = None):
        """Логирование ответа от AI модели"""
        status_emoji = "✅" if success else "❌"
        self.logger.info(f"{status_emoji} AI ОТВЕТ: {request_id}")
        self.logger.info(f"   Модель: {model}")
        self.logger.info(f"   Ответ:")
        self.logger.info(f"   {response}")
        
        if tokens_used:
            self.logger.info(f"   Токенов использовано: {tokens_used}")
        
        if processing_time:
            self.logger.info(f"   Время обработки: {processing_time:.2f}с")
        
        if error:
            self.logger.error(f"   Ошибка: {error}")
        
        # Сохраняем полный ответ в отдельный файл
        self._save_full_response(request_id, response, model, tokens_used, processing_time, success, error)
    
    def log_prompt_conversation(self, 
                               conversation_id: str,
                               messages: List[Dict[str, str]], 
                               model: str,
                               context: Dict[str, Any] = None):
        """Логирование полной беседы с AI"""
        self.logger.info(f"💬 AI БЕСЕДА: {conversation_id}")
        self.logger.info(f"   Модель: {model}")
        self.logger.info(f"   Количество сообщений: {len(messages)}")
        
        if context:
            self.logger.info(f"   Контекст: {json.dumps(context, ensure_ascii=False, indent=2)}")
        
        # Сохраняем полную беседу
        self._save_full_conversation(conversation_id, messages, model, context)
    
    def log_prompt_analysis(self, 
                           request_id: str,
                           analysis_type: str,
                           analysis_result: Dict[str, Any]):
        """Логирование анализа промпта или ответа"""
        self.logger.info(f"🔬 AI АНАЛИЗ: {request_id}")
        self.logger.info(f"   Тип анализа: {analysis_type}")
        self.logger.info(f"   Результат: {json.dumps(analysis_result, ensure_ascii=False, indent=2)}")
    
    def log_prompt_performance(self, 
                              model: str,
                              operation: str,
                              duration: float,
                              tokens_used: int = None,
                              cost: float = None):
        """Логирование производительности AI операций"""
        self.logger.info(f"⚡ AI ПРОИЗВОДИТЕЛЬНОСТЬ: {operation}")
        self.logger.info(f"   Модель: {model}")
        self.logger.info(f"   Время выполнения: {duration:.2f}с")
        
        if tokens_used:
            self.logger.info(f"   Токенов: {tokens_used}")
        
        if cost:
            self.logger.info(f"   Стоимость: ${cost:.6f}")
    
    def log_prompt_error(self, 
                        request_id: str,
                        error: Exception,
                        context: str = "",
                        additional_info: Dict[str, Any] = None):
        """Логирование ошибок AI операций"""
        self.logger.error(f"❌ AI ОШИБКА: {request_id}")
        self.logger.error(f"   Контекст: {context}")
        self.logger.error(f"   Тип ошибки: {type(error).__name__}")
        self.logger.error(f"   Сообщение: {str(error)}")
        
        if additional_info:
            self.logger.error(f"   Дополнительная информация: {json.dumps(additional_info, ensure_ascii=False, indent=2)}")
    
    def log_model_config(self, 
                        model: str,
                        config: Dict[str, Any]):
        """Логирование конфигурации модели"""
        self.logger.info(f"⚙️ КОНФИГУРАЦИЯ МОДЕЛИ: {model}")
        for key, value in config.items():
            self.logger.info(f"   {key}: {value}")
    
    def log_prompt_quality(self, 
                          request_id: str,
                          quality_metrics: Dict[str, float]):
        """Логирование метрик качества промпта"""
        self.logger.info(f"📊 КАЧЕСТВО ПРОМПТА: {request_id}")
        for metric, value in quality_metrics.items():
            self.logger.info(f"   {metric}: {value:.3f}")
    
    def _generate_request_id(self) -> str:
        """Генерация уникального ID запроса"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        return f"ai_{timestamp}_{random_suffix}"
    
    def _save_full_prompt(self, 
                         request_id: str,
                         model: str,
                         system_prompt: str,
                         user_prompt: str,
                         context: Dict[str, Any] = None):
        """Сохранение полного промпта в отдельный файл"""
        prompt_data = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "context": context or {}
        }
        
        prompt_file = self.log_file.parent / f"prompts/{request_id}_prompt.json"
        prompt_file.parent.mkdir(exist_ok=True)
        
        try:
            with open(prompt_file, 'w', encoding='utf-8') as f:
                json.dump(prompt_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Ошибка сохранения промпта: {e}")
    
    def _save_full_response(self, 
                           request_id: str,
                           response: str,
                           model: str,
                           tokens_used: int = None,
                           processing_time: float = None,
                           success: bool = True,
                           error: str = None):
        """Сохранение полного ответа в отдельный файл"""
        response_data = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "response": response,
            "tokens_used": tokens_used,
            "processing_time": processing_time,
            "success": success,
            "error": error
        }
        
        response_file = self.log_file.parent / f"responses/{request_id}_response.json"
        response_file.parent.mkdir(exist_ok=True)
        
        try:
            with open(response_file, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Ошибка сохранения ответа: {e}")
    
    def _save_full_conversation(self, 
                               conversation_id: str,
                               messages: List[Dict[str, str]],
                               model: str,
                               context: Dict[str, Any] = None):
        """Сохранение полной беседы в отдельный файл"""
        conversation_data = {
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "messages": messages,
            "context": context or {}
        }
        
        conversation_file = self.log_file.parent / f"conversations/{conversation_id}_conversation.json"
        conversation_file.parent.mkdir(exist_ok=True)
        
        try:
            with open(conversation_file, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Ошибка сохранения беседы: {e}")
    
    def get_log_file_path(self) -> Path:
        """Получение пути к файлу логов"""
        return self.log_file
    
    def get_log_file_size(self) -> int:
        """Получение размера файла логов в байтах"""
        try:
            return self.log_file.stat().st_size
        except FileNotFoundError:
            return 0
    
    def get_prompts_stats(self) -> Dict[str, Any]:
        """Получение статистики промптов"""
        try:
            prompts_dir = self.log_file.parent / "prompts"
            responses_dir = self.log_file.parent / "responses"
            
            stats = {
                "total_prompts": 0,
                "total_responses": 0,
                "successful_responses": 0,
                "failed_responses": 0,
                "models_used": set(),
                "average_processing_time": 0.0,
                "total_tokens": 0
            }
            
            # Подсчитываем промпты
            if prompts_dir.exists():
                stats["total_prompts"] = len(list(prompts_dir.glob("*_prompt.json")))
            
            # Подсчитываем ответы
            if responses_dir.exists():
                response_files = list(responses_dir.glob("*_response.json"))
                stats["total_responses"] = len(response_files)
                
                processing_times = []
                for response_file in response_files:
                    try:
                        with open(response_file, 'r', encoding='utf-8') as f:
                            response_data = json.load(f)
                            
                        if response_data.get("success", True):
                            stats["successful_responses"] += 1
                        else:
                            stats["failed_responses"] += 1
                        
                        stats["models_used"].add(response_data.get("model", "unknown"))
                        
                        if response_data.get("processing_time"):
                            processing_times.append(response_data["processing_time"])
                        
                        if response_data.get("tokens_used"):
                            stats["total_tokens"] += response_data["tokens_used"]
                            
                    except Exception as e:
                        self.logger.warning(f"Ошибка чтения файла ответа {response_file}: {e}")
                
                if processing_times:
                    stats["average_processing_time"] = sum(processing_times) / len(processing_times)
            
            # Преобразуем set в list для JSON сериализации
            stats["models_used"] = list(stats["models_used"])
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики: {e}")
            return {}

# Глобальный экземпляр логгера
ai_prompts_logger = None

def get_ai_prompts_logger() -> AIPromptsLogger:
    """Получение глобального экземпляра логгера промптов"""
    global ai_prompts_logger
    if ai_prompts_logger is None:
        ai_prompts_logger = AIPromptsLogger()
    return ai_prompts_logger

def log_ai_prompt_operation(operation: str, **kwargs):
    """Удобная функция для логирования операций с промптами"""
    logger = get_ai_prompts_logger()
    
    if operation == "prompt_request":
        logger.log_prompt_request(
            kwargs.get('model'),
            kwargs.get('system_prompt'),
            kwargs.get('user_prompt'),
            kwargs.get('context'),
            kwargs.get('request_id')
        )
    elif operation == "prompt_response":
        logger.log_prompt_response(
            kwargs.get('request_id'),
            kwargs.get('response'),
            kwargs.get('model'),
            kwargs.get('tokens_used'),
            kwargs.get('processing_time'),
            kwargs.get('success', True),
            kwargs.get('error')
        )
    elif operation == "prompt_conversation":
        logger.log_prompt_conversation(
            kwargs.get('conversation_id'),
            kwargs.get('messages'),
            kwargs.get('model'),
            kwargs.get('context')
        )
    elif operation == "prompt_analysis":
        logger.log_prompt_analysis(
            kwargs.get('request_id'),
            kwargs.get('analysis_type'),
            kwargs.get('analysis_result')
        )
    elif operation == "prompt_performance":
        logger.log_prompt_performance(
            kwargs.get('model'),
            kwargs.get('operation'),
            kwargs.get('duration'),
            kwargs.get('tokens_used'),
            kwargs.get('cost')
        )
    elif operation == "prompt_error":
        logger.log_prompt_error(
            kwargs.get('request_id'),
            kwargs.get('error'),
            kwargs.get('context'),
            kwargs.get('additional_info')
        )
    elif operation == "model_config":
        logger.log_model_config(
            kwargs.get('model'),
            kwargs.get('config')
        )
    elif operation == "prompt_quality":
        logger.log_prompt_quality(
            kwargs.get('request_id'),
            kwargs.get('quality_metrics')
        )
    else:
        logger.logger.info(f"📝 AI ОПЕРАЦИЯ: {operation}")
        for key, value in kwargs.items():
            logger.logger.info(f"   {key}: {value}")

# Декоратор для автоматического логирования AI функций
def log_ai_function_call(func_name: str = None):
    """Декоратор для логирования вызовов AI функций"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_ai_prompts_logger()
            func_name_to_log = func_name or func.__name__
            
            logger.logger.debug(f"🔧 ВЫЗОВ AI ФУНКЦИИ: {func_name_to_log}")
            logger.logger.debug(f"   Аргументы: {args}")
            logger.logger.debug(f"   Ключевые аргументы: {kwargs}")
            
            start_time = datetime.now()
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                logger.logger.debug(f"✅ AI ФУНКЦИЯ ЗАВЕРШЕНА: {func_name_to_log} за {duration:.2f}с")
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.log_prompt_error(e, f"Ошибка в AI функции {func_name_to_log}", {
                    "duration": f"{duration:.2f}с",
                    "args": str(args),
                    "kwargs": str(kwargs)
                })
                raise
        return wrapper
    return decorator

if __name__ == "__main__":
    # Тестирование логгера
    logger = get_ai_prompts_logger()
    
    # Тест промпта
    request_id = logger.log_prompt_request(
        model="gpt-4",
        system_prompt="Ты полезный ассистент",
        user_prompt="Расскажи о погоде",
        context={"user_id": "test_user", "chat_id": "test_chat"}
    )
    
    # Тест ответа
    logger.log_prompt_response(
        request_id=request_id,
        response="Погода сегодня солнечная, температура 25°C",
        model="gpt-4",
        tokens_used=150,
        processing_time=2.5
    )
    
    # Тест производительности
    logger.log_prompt_performance(
        model="gpt-4",
        operation="text_generation",
        duration=2.5,
        tokens_used=150,
        cost=0.003
    )
    
    # Тест статистики
    stats = logger.get_prompts_stats()
    print(f"📊 Статистика промптов: {stats}")
    
    print(f"✅ Логгер промптов протестирован. Файл: {logger.get_log_file_path()}")
    print(f"📊 Размер файла: {logger.get_log_file_size()} байт") 