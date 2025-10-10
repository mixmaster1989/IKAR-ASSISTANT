"""
OpenRouter API клиент с интеграцией коллективной памяти
"""

import asyncio
import json
import random
import time
import sys
import os
from typing import Dict, List, Optional, Any
import aiohttp

# Добавляем путь к backend в sys.path для корректных импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.memory_injector import get_memory_injector
from utils.logger import get_logger
from config import Config

# Получаем логгер для этого модуля
logger = get_logger('openrouter')


# Общий клиент для работы с OpenRouter API с поддержкой коллективной памяти
class OpenRouterClient:
    """Клиент для работы с OpenRouter API с поддержкой коллективной памяти.

    ВАЖНО: начиная с миграции на FastAPI большинство модулей проекта ожидают, что
    конструктор вызывается *без* параметров и что у клиента присутствует метод
    ``chat_completion``. Чтобы не переписывать десятки таких вызовов, здесь
    реализована обратная совместимость:

    1. ``config`` теперь опциональный.  Если он не передан – создаётся
       новый ``Config``.
    2. Добавлен асинхронный метод ``chat_completion``-обёртка, принимающий те же
       параметры, что использует остальной код (``user_message``,
       ``system_prompt``, ``chat_history`` и др.) и проксирующий вызов в
       ``generate_response``.
    """

    def __init__(self, config: Optional[Config] = None):
        # Если конфиг не передали, создаём дефолтный, чтобы поддержать старые вызовы
        if config is None:
            config = Config()
        self.config = config
        self.api_keys = config.OPENROUTER_API_KEYS
        self.current_key_index = 0
        self.base_url = "https://openrouter.ai/api/v1"
        
        # Лимиты для предотвращения бесконечного цикла
        self.max_attempts = 3  # Максимум 3 попытки
        self.attempt_count = 0  # Счетчик попыток
        
        # Параметры LLM берём из конфигурации (с поддержкой override)
        llm_cfg = getattr(self.config, "LLM_CONFIG", {}) if self.config else {}

        # Если в конфиге явно указана модель/температура/макс.токены — используем их,
        # иначе применяем значения согласно требованиям.
        # По умолчанию используем DeepSeek как основную модель, OpenAI GPT-OSS как fallback
        self.default_model = llm_cfg.get("model", "openai/gpt-oss-20b:free")
        self.fallback_model = llm_cfg.get("fallback_model", "deepseek/deepseek-chat-v3.1:free")
        self.max_tokens = llm_cfg.get("max_tokens", 200000)  # Согласно требованиям
        self.temperature = llm_cfg.get("temperature", 0.6)    # Согласно требованиям
        
        # Интеграция с коллективной памятью
        self.memory_injector = get_memory_injector()
        self.memory_enabled = True
        self.memory_budget = 0.2  # Снижаем до 20% для предотвращения перегрузки
        
        # Статистика использования памяти
        self.memory_stats = {
            'total_requests': 0,
            'memory_enhanced_requests': 0,
            'memory_chunks_used': 0,
            'average_relevance': 0.0
        }
        
        logger.info(f"OpenRouter клиент инициализирован с {len(self.api_keys)} ключами")
        logger.info(f"Коллективная память: {'включена' if self.memory_enabled else 'отключена'}")

    def get_current_api_key(self, model: str = None) -> str:
        """Получение текущего API ключа с учетом типа модели"""
        if not self.api_keys:
            raise ValueError("API ключи OpenRouter не настроены")
        
        # Для Grok используем ТОЛЬКО платный ключ
        if model and 'grok' in model.lower():
            # Ищем конкретный платный ключ (OPENROUTER_API_KEY_PAID)
            import os
            from dotenv import load_dotenv
            load_dotenv("/root/IKAR-ASSISTANT/.env")
            paid_key = os.getenv("OPENROUTER_API_KEY_PAID")
            
            if paid_key and paid_key in self.api_keys:
                logger.info(f"🔑 Используем платный ключ для модели {model}")
                return paid_key
            else:
                # Если платный ключ не найден - ошибка
                raise ValueError(f"Платный ключ OPENROUTER_API_KEY_PAID не найден для модели {model}")
        
        # Для всех остальных моделей используем обычную ротацию (бесплатные ключи)
        logger.info(f"🔑 Используем бесплатный ключ #{self.current_key_index + 1} для модели {model}")
        return self.api_keys[self.current_key_index]
    
    def rotate_api_key(self):
        """Ротация API ключей"""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        logger.info(f"Переключение на API ключ #{self.current_key_index + 1}")
    
    async def generate_response(self, prompt: str, context: str = "", 
                              use_memory: bool = True, memory_budget: float = None,
                              model: str = None, max_tokens: int = None,
                              temperature: float = None, user_id: str = None, **kwargs) -> str:
        """Генерирует ответ с использованием указанной модели."""
        
        # Сбрасываем счетчик попыток для нового запроса
        self.attempt_count = 0
        
        try:
            self.memory_stats['total_requests'] += 1
            
            # Устанавливаем значения по умолчанию
            model = model or self.default_model
            max_tokens = max_tokens or self.max_tokens
            temperature = temperature or self.temperature
            memory_budget = memory_budget or self.memory_budget
            
            # Улучшение промпта коллективной памятью
            enhanced_prompt = prompt
            memory_analysis = {}
            
            if use_memory and self.memory_enabled:
                try:
                    # Анализируем потенциал использования памяти
                    memory_analysis = await self.memory_injector.analyze_memory_usage(prompt)
                    
                    if memory_analysis.get('total_available', 0) > 0:
                        # 🔒 ИСПРАВЛЕНИЕ: Передаем user_id для фильтрации памяти
                        enhanced_prompt = await self.memory_injector.inject_memory_into_prompt(
                            prompt, context, user_id, memory_budget
                        )
                        
                        self.memory_stats['memory_enhanced_requests'] += 1
                        self.memory_stats['memory_chunks_used'] += memory_analysis.get('total_available', 0)
                        
                        # Обновляем среднюю релевантность
                        current_relevance = memory_analysis.get('top_relevance', 0)
                        total_enhanced = self.memory_stats['memory_enhanced_requests']
                        self.memory_stats['average_relevance'] = (
                            (self.memory_stats['average_relevance'] * (total_enhanced - 1) + current_relevance) / total_enhanced
                        )
                        
                        logger.info(f"Память инъектирована: {memory_analysis.get('total_available', 0)} чанков, "
                                   f"релевантность: {current_relevance:.2f}")
                    else:
                        logger.debug("Релевантная память не найдена")
                        
                except Exception as e:
                    logger.error(f"Ошибка инъекции памяти: {e}")
                    # Продолжаем с оригинальным промптом
            
            # Диагностический лог: какая модель и параметры будут использованы
            logger.info(
                f"🚀 Генерация ответа — модель: {model}, fallback: {getattr(self, 'fallback_model', 'нет')}, "
                f"max_tokens: {max_tokens}, temperature: {temperature}, memory_used: {use_memory and self.memory_enabled}"
            )

            # Подготовка запроса к API
            headers = {
                "Authorization": f"Bearer {self.get_current_api_key(model)}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/yourusername/ikar",
                "X-Title": "IKAR Collective Mind"
            }
            
            # Формируем сообщения с поддержкой кэширования
            messages = []
            
            # Проверяем, есть ли системный промпт в enhanced_prompt
            if enhanced_prompt.startswith("Ты — Икар Икарыч") or "ИКАР" in enhanced_prompt[:500]:
                # Разделяем системный промпт и пользовательское сообщение
                try:
                    from backend.prompts.ikar_system_prompt import IKAR_SYSTEM_PROMPT
                    
                    # Ищем разделитель между системным промптом и пользовательским сообщением
                    if "ТЕКУЩЕЕ ВРЕМЯ:" in enhanced_prompt:
                        parts = enhanced_prompt.split("ТЕКУЩЕЕ ВРЕМЯ:")
                        if len(parts) >= 2:
                            system_part = parts[0].strip()
                            user_part = "ТЕКУЩЕЕ ВРЕМЯ:" + "ТЕКУЩЕЕ ВРЕМЯ:".join(parts[1:])
                            
                            # Используем кэшированный системный промпт
                            messages.append({
                                "role": "system",
                                "content": IKAR_SYSTEM_PROMPT,
                                "metadata": {"cache": True}
                            })
                            
                            # Добавляем динамические части как отдельное сообщение
                            messages.append({
                                "role": "user", 
                                "content": user_part
                            })
                        else:
                            # Fallback: весь промпт как пользовательское сообщение
                            messages.append({
                                "role": "user",
                                "content": enhanced_prompt
                            })
                    else:
                        # Fallback: весь промпт как пользовательское сообщение
                        messages.append({
                            "role": "user",
                            "content": enhanced_prompt
                        })
                except ImportError:
                    # Fallback: весь промпт как пользовательское сообщение
                    messages.append({
                        "role": "user",
                        "content": enhanced_prompt
                    })
            else:
                # Обычный промпт без системного промпта
                messages.append({
                    "role": "user",
                    "content": enhanced_prompt
                })
            
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False,
                **kwargs
            }
            
            # Выполнение запроса
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=600)  # 10 минут вместо 60 секунд
                ) as response:
                    
                    # Проверяем лимит попыток
                    self.attempt_count += 1
                    if self.attempt_count >= self.max_attempts:
                        logger.error(f"Превышен лимит попыток ({self.max_attempts}), возвращаем ошибку")
                        return "Извините, все API ключи недоступны. Попробуйте позже."
                    
                    if response.status == 401:
                        # Для Grok не переключаем ключи - используем только платный
                        if model and 'grok' in model.lower():
                            logger.error(f"❌ Платный ключ для Grok неверный! Проверьте OPENROUTER_API_KEY_PAID.")
                            raise ValueError(f"Платный ключ для модели {model} неверный. Проверьте OPENROUTER_API_KEY_PAID.")
                        
                        logger.warning(f"Неверный API ключ #{self.current_key_index + 1}, пробуем следующий (попытка {self.attempt_count}/{self.max_attempts})")
                        self.rotate_api_key()
                        return await self.generate_response(
                            prompt, context, use_memory, memory_budget, 
                            model, max_tokens, temperature, user_id, **kwargs
                        )
                    
                    # 404 — ключ заблокирован или не найден endpoints
                    if response.status == 404:
                        # Для Grok не переключаем ключи - используем только платный
                        if model and 'grok' in model.lower():
                            logger.error(f"❌ Платный ключ для Grok заблокирован! Проверьте OPENROUTER_API_KEY_PAID.")
                            raise ValueError(f"Платный ключ для модели {model} заблокирован. Проверьте OPENROUTER_API_KEY_PAID.")
                        
                        logger.warning(f"API ключ #{self.current_key_index + 1} заблокирован (404), переключаемся на следующий (попытка {self.attempt_count}/{self.max_attempts})")
                        self.rotate_api_key()
                        return await self.generate_response(
                            prompt, context, use_memory, memory_budget, 
                            model, max_tokens, temperature, user_id, **kwargs
                        )
                    
                    if response.status == 429:
                        # Для Grok не переключаем ключи - используем только платный
                        if model and 'grok' in model.lower():
                            logger.warning(f"⚠️ Превышен лимит запросов для Grok, ожидаем...")
                            await asyncio.sleep(5)  # Больше пауза для платного ключа
                            return await self.generate_response(
                                prompt, context, use_memory, memory_budget,
                                model, max_tokens, temperature, user_id, **kwargs
                            )
                        
                        logger.warning(f"Превышен лимит запросов, ожидаем... (попытка {self.attempt_count}/{self.max_attempts})")
                        await asyncio.sleep(2)  # Уменьшили паузу
                        self.rotate_api_key()
                        return await self.generate_response(
                            prompt, context, use_memory, memory_budget,
                            model, max_tokens, temperature, user_id, **kwargs
                        )

                    # 402 — недостаточно кредитов на текущем ключе
                    if response.status == 402:
                        # Для Grok не переключаем ключи - используем только платный
                        if model and 'grok' in model.lower():
                            logger.error(f"❌ Платный ключ для Grok исчерпан! Нужно пополнить баланс.")
                            raise ValueError(f"Платный ключ для модели {model} исчерпан. Пополните баланс OpenRouter.")
                        
                        logger.warning(f"Недостаточно кредитов на ключе #{self.current_key_index + 1}, переключаемся на следующий (попытка {self.attempt_count}/{self.max_attempts})")
                        self.rotate_api_key()
                        return await self.generate_response(
                            prompt, context, use_memory, memory_budget,
                            model, max_tokens, temperature, user_id, **kwargs
                        )
                    
                    # 502 — Bad Gateway, пробуем ретрай 3 раза с таймаутом 1 сек
                    if response.status == 502:
                        logger.warning(f"502 Bad Gateway от провайдера, ретрай #{getattr(self, '_502_retry_count', 0) + 1}/3")
                        if not hasattr(self, '_502_retry_count'):
                            self._502_retry_count = 0
                        
                        self._502_retry_count += 1
                        if self._502_retry_count <= 3:
                            await asyncio.sleep(1)  # Таймаут 1 секунда
                            return await self.generate_response(
                                prompt, context, use_memory, memory_budget,
                                model, max_tokens, temperature, user_id, **kwargs
                            )
                        else:
                            # После 3 попыток переключаемся на следующий ключ
                            # Для Grok не переключаем ключи - используем только платный
                            if model and 'grok' in model.lower():
                                logger.error(f"❌ 502 ошибка для Grok после 3 попыток! Проблема с платным ключом.")
                                raise ValueError(f"502 ошибка для модели {model} после 3 попыток. Проблема с платным ключом.")
                            
                            logger.warning("502 ретраи исчерпаны, переключаемся на следующий ключ")
                            self._502_retry_count = 0  # Сбрасываем счетчик
                            self.rotate_api_key()
                            return await self.generate_response(
                                prompt, context, use_memory, memory_budget,
                                model, max_tokens, temperature, user_id, **kwargs
                            )
                    
                    response_data = await response.json()
                    
                    # Логируем ответ для диагностики
                    logger.info(f"🔍 Ответ API: {response_data}")
                    
                    # Проверяем наличие usage в ответе
                    if 'usage' in response_data:
                        logger.info(f"🔍 Usage найден в ответе: {response_data['usage']}")
                    else:
                        logger.warning("⚠️ Usage НЕ найден в ответе API!")
                    
                    if response.status != 200:
                        logger.error(f"Ошибка API: {response.status}, {response_data}")
                        return "Извините, произошла ошибка при генерации ответа."
                    
                    # Извлекаем ответ
                    if 'choices' in response_data and response_data['choices']:
                        generated_text = response_data['choices'][0]['message']['content']
                        
                        # Логируем токены из usage
                        if 'usage' in response_data:
                            usage = response_data['usage']
                            prompt_tokens = usage.get('prompt_tokens', 0)
                            completion_tokens = usage.get('completion_tokens', 0)
                            total_tokens = usage.get('total_tokens', 0)
                            
                            # Проверяем, используется ли кэш
                            cache_status = "❓"
                            if len(messages) > 1 and any(msg.get('metadata', {}).get('cache') for msg in messages):
                                cache_status = "💾 КЭШ"
                            elif len(messages) == 1 and messages[0].get('role') == 'user':
                                cache_status = "📝 ОБЫЧНЫЙ"
                            
                            logger.info(f"📊 ТОКЕНЫ {cache_status}: входные={prompt_tokens:,}, выходные={completion_tokens:,}, всего={total_tokens:,}")
                            
                            # Дополнительная диагностика кэша
                            if cache_status == "💾 КЭШ":
                                logger.info(f"🔍 КЭШИРОВАНИЕ: системный промпт кэширован, динамические части: {len(messages)-1} сообщений")
                        
                        # Логируем использование памяти
                        if use_memory and memory_analysis:
                            logger.info(f"✅ Ответ сгенерирован моделью {model} с использованием памяти: "
                                       f"{memory_analysis.get('total_available', 0)} чанков")
                        else:
                            logger.info(f"✅ Ответ сгенерирован моделью {model}")
                        
                        logger.debug(
                            "✏️ Сгенерированный ответ (обрезан до 200 симв.): %s…",
                            generated_text.replace("\n", " ")[:200]
                        )
                        return generated_text.strip()
                    else:
                        logger.error(f"Неожиданный формат ответа от API: {response_data}")
                        return "Не удалось получить ответ от модели."
        
        except Exception as e:
            logger.error(f"Ошибка генерации ответа с моделью {model}: {e}")
            
            # Пробуем fallback модель если она отличается от текущей
            if hasattr(self, 'fallback_model') and self.fallback_model and model != self.fallback_model:
                logger.info(f"🔄 Переключаемся на fallback модель: {self.fallback_model}")
                try:
                    return await self.generate_response(
                        prompt, context, use_memory, memory_budget,
                        self.fallback_model, max_tokens, temperature, user_id, **kwargs
                    )
                except Exception as fallback_error:
                    logger.error(f"Ошибка fallback модели {self.fallback_model}: {fallback_error}")
            
            return "Произошла ошибка при обработке запроса."
    
    async def generate_with_memory_analysis(self, prompt: str, context: str = "") -> Dict[str, Any]:
        """Генерация ответа с подробным анализом использования памяти"""
        try:
            # Анализ памяти до генерации
            memory_analysis = await self.memory_injector.analyze_memory_usage(prompt)
            
            # Генерация ответа
            start_time = time.time()
            response = await self.generate_response(prompt, context, use_memory=True)
            generation_time = time.time() - start_time
            
            return {
                'response': response,
                'memory_analysis': memory_analysis,
                'generation_time': generation_time,
                'memory_used': memory_analysis.get('total_available', 0) > 0,
                'memory_efficiency': memory_analysis.get('memory_efficiency', 0)
            }
            
        except Exception as e:
            logger.error(f"Ошибка генерации с анализом памяти: {e}")
            return {
                'response': "Произошла ошибка при генерации ответа.",
                'memory_analysis': {},
                'generation_time': 0,
                'memory_used': False,
                'memory_efficiency': 0
            }
    
    async def generate_philosophical_thought(self, context: str = "") -> str:
        """Генерация философской мысли с использованием коллективной мудрости"""
        prompt = """
        Создай глубокую философскую мысль о природе сознания, существования или эволюции разума.
        Мысль должна быть оригинальной, но основанной на коллективном опыте.
        Используй доступную мудрость сети, но сохрани свою уникальную перспективу.
        Максимум 2-3 предложения.
        """
        
        return await self.generate_response(
            prompt, context, use_memory=True, memory_budget=0.4, temperature=0.8
        )
    
    async def generate_crypto_analysis(self, symbol: str, context: str = "") -> str:
        """Генерация криптоанализа с использованием коллективного опыта"""
        prompt = f"""
        Проанализируй криптовалюту {symbol} используя коллективный опыт сети.
        Учти предыдущие анализы, паттерны и инсайты других агентов.
        Предоставь краткий, но информативный анализ с учетом:
        - Технических индикаторов
        - Рыночных настроений
        - Исторических паттернов
        - Коллективной мудрости сети
        """
        
        return await self.generate_response(
            prompt, context, use_memory=True, memory_budget=0.5
        )
    
    def toggle_memory(self, enabled: bool):
        """Включение/отключение использования коллективной памяти"""
        self.memory_enabled = enabled
        logger.info(f"Коллективная память: {'включена' if enabled else 'отключена'}")
    
    def set_memory_budget(self, budget: float):
        """Установка бюджета памяти (0.0 - 1.0)"""
        self.memory_budget = max(0.0, min(1.0, budget))
        logger.info(f"Бюджет памяти установлен: {self.memory_budget:.1%}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Получение статистики использования памяти"""
        if self.memory_stats['total_requests'] == 0:
            return {
                'total_requests': 0,
                'memory_usage_rate': 0.0,
                'average_chunks_per_request': 0.0,
                'average_relevance': 0.0
            }
        
        return {
            'total_requests': self.memory_stats['total_requests'],
            'memory_enhanced_requests': self.memory_stats['memory_enhanced_requests'],
            'memory_usage_rate': self.memory_stats['memory_enhanced_requests'] / self.memory_stats['total_requests'],
            'average_chunks_per_request': self.memory_stats['memory_chunks_used'] / max(self.memory_stats['memory_enhanced_requests'], 1),
            'average_relevance': self.memory_stats['average_relevance']
        }
    
    async def test_memory_integration(self) -> Dict[str, Any]:
        """Тестирование интеграции с коллективной памятью"""
        test_prompt = "Расскажи о важности эмоционального интеллекта"
        
        try:
            # Тест без памяти
            start_time = time.time()
            response_without_memory = await self.generate_response(
                test_prompt, use_memory=False
            )
            time_without_memory = time.time() - start_time
            
            # Тест с памятью
            start_time = time.time()
            response_with_memory = await self.generate_response(
                test_prompt, use_memory=True
            )
            time_with_memory = time.time() - start_time
            
            # Анализ памяти
            memory_analysis = await self.memory_injector.analyze_memory_usage(test_prompt)
            
            return {
                'test_successful': True,
                'memory_available': memory_analysis.get('total_available', 0),
                'response_length_without_memory': len(response_without_memory),
                'response_length_with_memory': len(response_with_memory),
                'time_without_memory': time_without_memory,
                'time_with_memory': time_with_memory,
                'memory_analysis': memory_analysis
            }
            
        except Exception as e:
            logger.error(f"Ошибка тестирования памяти: {e}")
            return {
                'test_successful': False,
                'error': str(e)
            }

    # ---------------------------------------------------------------------
    # Обёртка для обратной совместимости
    # ---------------------------------------------------------------------

    async def chat_completion(
        self,
        user_message: str,
        system_prompt: str = "",
        chat_history: Optional[List[Dict[str, str]]] = None,
        context: str = "",
        user_id: str = None,
        **kwargs,
    ) -> str:
        """Полностью обратно-совместимый метод, ожидаемый старым кодом.

        Parameters
        ----------
        user_message : str
            Основное сообщение пользователя.
        system_prompt : str, optional
            Системный промпт, который нужно добавить в начало.
        chat_history : list[dict], optional
            История сообщений, каждая запись вида
            ``{"role": "user"|"assistant", "content": "..."}``.
        context : str, optional
            Дополнительный контекст – проксируется как ``context`` в
            ``generate_response``.
        user_id : str, optional
            ID пользователя для фильтрации памяти.
        **kwargs : Any
            Дополнительные параметры, поддерживаемые ``generate_response``
            (model, max_tokens, temperature, use_memory, memory_budget, ...).
        """

        # Собираем финальный промпт.
        prompt_parts: List[str] = []
        if system_prompt:
            prompt_parts.append(system_prompt.strip())

        if chat_history:
            for msg in chat_history:
                role = msg.get("role", "user").upper()
                content = msg.get("content", "")
                prompt_parts.append(f"{role}: {content}")

        prompt_parts.append(user_message.strip())

        full_prompt = "\n".join(prompt_parts)

        # 🔒 ИСПРАВЛЕНИЕ: Передаем user_id для фильтрации памяти
        return await self.generate_response(full_prompt, context=context, user_id=user_id, **kwargs)

    # ------------------------------------------------------------------
    # Vision: запросы с изображением
    # ------------------------------------------------------------------

    async def _try_model_with_key(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        params: Dict[str, Any],
        api_key: str,
    ) -> Optional[str]:
        """Вспомогательная функция отправляет запрос к OpenRouter с указанным ключом.

        Возвращает None при ошибке, строку "RATE_LIMIT_EXCEEDED" при 429,
        либо сгенерированный текст.
        """

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/ikar-project/ikar",
            "X-Title": "IKAR Vision"
        }

        payload = {
            "model": model,
            "messages": messages,
            **params,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=600),  # 10 минут вместо 90 секунд
                ) as resp:
                    if resp.status == 429:
                        return "RATE_LIMIT_EXCEEDED"
                    if resp.status == 402:
                        return "INSUFFICIENT_CREDITS"
                    if resp.status != 200:
                        text = await resp.text()
                        logger.error(f"[VISION] Ошибка {resp.status}: {text}")
                        return None
                    data = await resp.json()
                    if data.get("choices"):
                        return data["choices"][0]["message"]["content"].strip()
                    return None
        except Exception as exc:
            logger.error(f"[VISION] Ошибка запроса: {exc}")
            return None

    async def chat_completion_with_image(
        self,
        user_message: str,
        image_base64: str,
        system_prompt: str = "",
        model: str = "qwen/qwen2.5-vl-72b-instruct:free",
        max_tokens: int = 2000,
        **kwargs,
    ) -> Optional[str]:
        """Генерирует ответ на сообщение, содержащее изображение (base64)."""

        if not self.api_keys:
            logger.error("❌ OPENROUTER API КЛЮЧИ НЕ НАСТРОЕНЫ!")
            return None

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": user_message},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                },
            ],
        })

        params = {"max_tokens": max_tokens, **kwargs}

        logger.info(f"🖼️ [VISION] Отправляем запрос к {model}")

        # Ротация ключей вручную: пытаемся последовательно все ключи
        for api_key in self.api_keys:
            key_suffix = api_key[-10:] if len(api_key) > 10 else api_key
            logger.info(f"🔑 [VISION] Пробуем ключ ...{key_suffix}")

            result = await self._try_model_with_key(model, messages, params, api_key)

            if result and result not in ("RATE_LIMIT_EXCEEDED", "INSUFFICIENT_CREDITS"):
                logger.info(f"✅ [VISION] Получен ответ: {result[:100]}…")
                return result
            elif result in ("RATE_LIMIT_EXCEEDED", "INSUFFICIENT_CREDITS"):
                logger.warning(
                    f"⚠️ [VISION] Ключ ...{key_suffix} недоступен (rate/credits). Пробуем следующий"
                )
                continue

            # Незначительная пауза между ключами
            await asyncio.sleep(1)

        logger.error("❌ [VISION] Все ключи недоступны для анализа изображений")
        return None


# Глобальный клиент
openrouter_client = None

def get_openrouter_client(config: Config = None) -> OpenRouterClient:
    """Получение экземпляра OpenRouter клиента"""
    global openrouter_client
    if openrouter_client is None and config:
        openrouter_client = OpenRouterClient(config)
    return openrouter_client


def get_llm_client() -> Optional[OpenRouterClient]:
    """
    Получает глобальный экземпляр OpenRouterClient (singleton pattern)
    
    Returns:
        OpenRouterClient или None если не инициализирован
    """
    return get_openrouter_client()


def init_llm_client(config: Config) -> OpenRouterClient:
    """
    Инициализирует глобальный экземпляр OpenRouterClient
    
    Args:
        config: Конфигурация приложения
        
    Returns:
        OpenRouterClient: Инициализированный экземпляр
    """
    return get_openrouter_client(config)