"""
Модуль для Telegram-специфичной обработки крипто-контента.
Отвечает за обработку фото, кнопок и callback-запросов в Telegram.
"""
import logging
import json
import os
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

logger = logging.getLogger("chatumba.crypto.telegram_handler")

# Импорты из других модулей
from .detector import detect_crypto_content, extract_trading_pair_from_description
from .data_fetcher import fetch_bingx_market_data, format_bingx_data_for_prompts
from .analyzer import analyze_trading_chart
from .cryptosud import cryptosud_analysis


class TelegramCryptoHandler:
    """
    Класс для обработки крипто-контента в Telegram.
    """
    
    def __init__(self):
        self.processed_photos = set()
        self.callback_cache = {}
        
    async def process_telegram_photo_with_crypto_detection(self, 
                                                         photo_path: str,
                                                         chat_id: str,
                                                         user_id: str,
                                                         message_text: str = "") -> Dict[str, Any]:
        """
        Обрабатывает фото из Telegram с детекцией крипто-контента.
        
        Args:
            photo_path: Путь к фото
            chat_id: ID чата
            user_id: ID пользователя
            message_text: Текст сообщения
            
        Returns:
            Результат обработки
        """
        try:
            logger.info(f"[TELEGRAM-CRYPTO] Обрабатываю фото: {photo_path}")
            
            # Проверяем, не обрабатывали ли уже это фото
            photo_hash = f"{chat_id}_{user_id}_{os.path.getmtime(photo_path)}"
            if photo_hash in self.processed_photos:
                return {"status": "already_processed", "message": "Фото уже обработано"}
            
            # 1. Анализируем график
            chart_analysis = await analyze_trading_chart(photo_path)
            logger.info(f"[TELEGRAM-CRYPTO] Результат анализа графика: {type(chart_analysis)} - {chart_analysis}")
            
            # 2. Детектируем крипто-контент в тексте
            has_crypto, crypto_terms = detect_crypto_content(message_text)
            
            # 3. Если крипто-контент найден
            if has_crypto or chart_analysis:
                # Извлекаем торговую пару
                trading_pair = extract_trading_pair_from_description(message_text, crypto_terms)
                
                # Получаем данные с BingX
                bingx_data = await fetch_bingx_market_data(trading_pair)
                
                # Форматируем данные для промптов
                formatted_data = format_bingx_data_for_prompts(bingx_data)
                
                # Выполняем CRYPTOSUD анализ
                logger.info(f"[TELEGRAM-CRYPTO] Вызываю cryptosud_analysis с chart_analysis типа: {type(chart_analysis)}")
                cryptosud_result = await cryptosud_analysis(
                    chat_id, message_text, crypto_terms, chart_analysis
                )
                
                # Формируем ответ
                response = {
                    "status": "success",
                    "has_crypto": True,
                    "trading_pair": trading_pair,
                    "crypto_terms": crypto_terms,
                    "chart_analysis": chart_analysis,
                    "bingx_data": bingx_data,
                    "formatted_data": formatted_data,
                    "cryptosud_analysis": cryptosud_result,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Добавляем фото в обработанные
                self.processed_photos.add(photo_hash)
                
                logger.info(f"[TELEGRAM-CRYPTO] Успешно обработано фото с крипто-контентом")
                return response
            
            else:
                # Крипто-контент не найден
                response = {
                    "status": "no_crypto",
                    "has_crypto": False,
                    "message": "Крипто-контент не обнаружен",
                    "timestamp": datetime.now().isoformat()
                }
                
                logger.info(f"[TELEGRAM-CRYPTO] Крипто-контент не найден в фото")
                return response
                
        except Exception as e:
            logger.error(f"[TELEGRAM-CRYPTO] Ошибка обработки фото: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def handle_crypto_callback(self, 
                                   callback_data: str,
                                   chat_id: str,
                                   user_id: str) -> Dict[str, Any]:
        """
        Обрабатывает callback-запросы для крипто-функций.
        
        Args:
            callback_data: Данные callback
            chat_id: ID чата
            user_id: ID пользователя
            
        Returns:
            Результат обработки
        """
        try:
            logger.info(f"[TELEGRAM-CRYPTO] Обрабатываю callback: {callback_data}")
            
            # Парсим callback данные
            callback_parts = callback_data.split(":")
            if len(callback_parts) < 2:
                return {"status": "error", "message": "Неверный формат callback"}
            
            action = callback_parts[0]
            params = callback_parts[1:]
            
            # Обрабатываем различные действия
            if action == "crypto_analysis":
                return await self._handle_crypto_analysis_callback(params, chat_id, user_id)
            elif action == "crypto_data":
                return await self._handle_crypto_data_callback(params, chat_id, user_id)
            elif action == "crypto_news":
                return await self._handle_crypto_news_callback(params, chat_id, user_id)
            else:
                return {"status": "error", "message": f"Неизвестное действие: {action}"}
                
        except Exception as e:
            logger.error(f"[TELEGRAM-CRYPTO] Ошибка обработки callback: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _handle_crypto_analysis_callback(self, 
                                             params: List[str],
                                             chat_id: str,
                                             user_id: str) -> Dict[str, Any]:
        """Обрабатывает callback для крипто-анализа."""
        try:
            if len(params) < 1:
                return {"status": "error", "message": "Недостаточно параметров"}
            
            trading_pair = params[0]
            
            # Получаем данные
            bingx_data = await fetch_bingx_market_data(trading_pair)
            
            # Выполняем анализ
            crypto_terms = [trading_pair.split('-')[0].lower()]
            cryptosud_result = await cryptosud_analysis(
                chat_id, f"Анализ {trading_pair}", crypto_terms
            )
            
            return {
                "status": "success",
                "action": "crypto_analysis",
                "trading_pair": trading_pair,
                "analysis": cryptosud_result,
                "data": bingx_data,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка обработки crypto_analysis callback: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _handle_crypto_data_callback(self, 
                                         params: List[str],
                                         chat_id: str,
                                         user_id: str) -> Dict[str, Any]:
        """Обрабатывает callback для получения крипто-данных."""
        try:
            if len(params) < 1:
                return {"status": "error", "message": "Недостаточно параметров"}
            
            trading_pair = params[0]
            
            # Получаем данные
            bingx_data = await fetch_bingx_market_data(trading_pair)
            formatted_data = format_bingx_data_for_prompts(bingx_data)
            
            return {
                "status": "success",
                "action": "crypto_data",
                "trading_pair": trading_pair,
                "data": bingx_data,
                "formatted_data": formatted_data,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка обработки crypto_data callback: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _handle_crypto_news_callback(self, 
                                         params: List[str],
                                         chat_id: str,
                                         user_id: str) -> Dict[str, Any]:
        """Обрабатывает callback для получения крипто-новостей."""
        try:
            if len(params) < 1:
                return {"status": "error", "message": "Недостаточно параметров"}
            
            crypto_terms = params[0].split(',')
            
            # Получаем новости
            from .data_fetcher import fetch_crypto_news
            news_data = await fetch_crypto_news(crypto_terms)
            
            return {
                "status": "success",
                "action": "crypto_news",
                "crypto_terms": crypto_terms,
                "news": news_data,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка обработки crypto_news callback: {e}")
            return {"status": "error", "error": str(e)}
    
    def create_crypto_keyboard(self, trading_pair: str, crypto_terms: List[str]) -> Dict[str, Any]:
        """
        Создает клавиатуру для крипто-функций.
        
        Args:
            trading_pair: Торговая пара
            crypto_terms: Криптотермины
            
        Returns:
            Клавиатура в формате Telegram
        """
        try:
            keyboard = {
                "inline_keyboard": [
                    [
                        {
                            "text": "📊 Анализ",
                            "callback_data": f"crypto_analysis:{trading_pair}"
                        },
                        {
                            "text": "📈 Данные",
                            "callback_data": f"crypto_data:{trading_pair}"
                        }
                    ],
                    [
                        {
                            "text": "📰 Новости",
                            "callback_data": f"crypto_news:{','.join(crypto_terms[:3])}"
                        },
                        {
                            "text": "🔍 CRYPTOSUD",
                            "callback_data": f"crypto_analysis:{trading_pair}"
                        }
                    ]
                ]
            }
            
            return keyboard
            
        except Exception as e:
            logger.error(f"Ошибка создания клавиатуры: {e}")
            return {"inline_keyboard": []}
    
    def cleanup_old_data(self):
        """Очищает старые данные."""
        try:
            # Очищаем старые обработанные фото (оставляем только последние 100)
            if len(self.processed_photos) > 100:
                self.processed_photos = set(list(self.processed_photos)[-100:])
            
            # Очищаем старые callback кэши (оставляем только последние 50)
            if len(self.callback_cache) > 50:
                self.callback_cache = dict(list(self.callback_cache.items())[-50:])
                
            logger.info("[TELEGRAM-CRYPTO] Очистка старых данных завершена")
            
        except Exception as e:
            logger.error(f"Ошибка очистки данных: {e}")


# Глобальный экземпляр для использования
telegram_crypto_handler = TelegramCryptoHandler()


# Основные функции для экспорта
async def process_telegram_photo_with_crypto_detection(photo_message, chat_id: str, user_id: str, temp_dir, download_telegram_file, send_telegram_message) -> Dict[str, Any]:
    """Основная функция для обработки фото с крипто-детекцией."""
    try:
        # Извлекаем информацию о фото из сообщения Telegram
        photos = photo_message.get('photo', [])
        if not photos:
            await send_telegram_message(chat_id, "❌ Не удалось найти фото для анализа.")
            return {"status": "error", "message": "No photo found"}
        
        # Берем фото с максимальным разрешением (последнее в списке)
        photo = photos[-1]
        file_id = photo.get('file_id')
        if not file_id:
            await send_telegram_message(chat_id, "❌ Не удалось получить file_id фото.")
            return {"status": "error", "message": "No file_id found"}
        
        # Скачиваем фото
        photo_path = await download_telegram_file(file_id)
        if not photo_path:
            await send_telegram_message(chat_id, "❌ Не удалось скачать фото для анализа.")
            return {"status": "error", "message": "Failed to download photo"}
        
        # Извлекаем текст подписи
        message_text = photo_message.get('caption', '')
        
        logger.info(f"[TELEGRAM-CRYPTO] Обрабатываю фото: {photo_path}")
        
        # Вызываем основную функцию обработки
        result = await telegram_crypto_handler.process_telegram_photo_with_crypto_detection(
            photo_path, chat_id, user_id, message_text
        )
        
        # Удаляем временный файл
        import os
        try:
            os.remove(photo_path)
        except Exception as e:
            logger.error(f"Ошибка при удалении временного файла: {e}")
        
        return result
        
    except Exception as e:
        logger.error(f"[TELEGRAM-CRYPTO] Ошибка обработки фото: {e}")
        await send_telegram_message(chat_id, f"❌ Ошибка при анализе изображения: {str(e)}")
        return {"status": "error", "message": str(e)}


async def handle_crypto_callback(callback_data: str,
                               chat_id: str,
                               user_id: str) -> Dict[str, Any]:
    """Основная функция для обработки крипто-callback."""
    return await telegram_crypto_handler.handle_crypto_callback(
        callback_data, chat_id, user_id
    )


def create_crypto_keyboard(trading_pair: str, crypto_terms: List[str]) -> Dict[str, Any]:
    """Основная функция для создания крипто-клавиатуры."""
    return telegram_crypto_handler.create_crypto_keyboard(trading_pair, crypto_terms)
