"""
Модуль с маршрутами API.
"""
import logging
import asyncio
import time
from typing import Dict, List, Optional, Union, Any
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, UploadFile, File, Form, Request, Body
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import os
import tempfile
import uuid
import random
import sqlite3

from backend.core.personality import ChatumbaPersonality
from backend.core.reactions import choose_reaction
from backend.core.utils import estimate_sentiment, should_remember, generate_response_delay
from backend.llm import OpenRouterClient
from backend.llm.prompt_builder import build_system_prompt, build_memory_query, format_chat_history
from backend.memory.embeddings import EmbeddingGenerator
# Удален импорт vector_store - заменен на lazy_memory
from backend.memory.sqlite import SQLiteStorage
from backend.voice.tts import TextToSpeech
from backend.voice.stt import SpeechToText
from backend.config import VECTOR_DB_CONFIG, Config

logger = logging.getLogger("chatumba.api")

# Создаем роутер
router = APIRouter()

# Инициализируем компоненты
from backend.utils.component_manager import get_component_manager
component_manager = get_component_manager()

embedding_generator = component_manager.get_embedding_generator()
# Используем LazyMemory вместо vector_store
from backend.memory.lazy_memory import get_lazy_memory
lazy_memory = get_lazy_memory()
sqlite_storage = component_manager.get_sqlite_storage()
llm_client = component_manager.get_llm_client()

# Инициализируем голосовые компоненты (по требованию)
tts_engine = None
stt_engine = None

# Словарь для хранения экземпляров личности по пользователям
personality_instances = {}

# Модели данных
class MessageRequest(BaseModel):
    """Модель запроса сообщения."""
    user_id: str
    message: str
    use_voice: bool = False

class MessageResponse(BaseModel):
    """Модель ответа на сообщение."""
    message: str
    typing_parts: List[Dict[str, Union[str, int]]]
    reaction_type: str
    audio_url: Optional[str] = None
    is_autonomous: bool = False

class MemoryRequest(BaseModel):
    """Модель запроса для работы с памятью."""
    user_id: str
    text: Optional[str] = None
    memory_id: Optional[str] = None

class PersonalityRequest(BaseModel):
    """Модель запроса для работы с личностью."""
    user_id: str
    personality_params: Optional[Dict[str, Any]] = None

class SoulRequest(BaseModel):
    """Модель запроса для работы с душой."""
    user_id: str
    action: str
    value: Optional[Any] = None

class ImageGenerateRequest(BaseModel):
    """Модель запроса для генерации изображения."""
    prompt: str
    model: str = "stabilityai/stable-diffusion-3-medium-diffusers"
    width: int = 512
    height: int = 512
    num_inference_steps: int = 20
    guidance_scale: float = 7.5
    negative_prompt: Optional[str] = None

# Вспомогательные функции
def get_personality(user_id: str) -> ChatumbaPersonality:
    """
    Получает или создает экземпляр личности для пользователя.
    
    Args:
        user_id: ID пользователя
        
    Returns:
        Экземпляр личности
    """
    if user_id not in personality_instances:
        personality_instances[user_id] = ChatumbaPersonality(user_id)
    
    return personality_instances[user_id]

def get_tts_engine() -> TextToSpeech:
    """
    Получает экземпляр TTS движка.
    
    Returns:
        Экземпляр TTS движка
    """
    global tts_engine
    
    if tts_engine is None:
        tts_engine = TextToSpeech()
    
    return tts_engine

def get_stt_engine() -> SpeechToText:
    """
    Получает экземпляр STT движка.
    
    Returns:
        Экземпляр STT движка
    """
    global stt_engine
    
    if stt_engine is None:
        stt_engine = SpeechToText()
    
    return stt_engine

# Маршруты API
@router.post("/message", response_model=MessageResponse)
async def send_message(request: MessageRequest):
    """
    Отправляет сообщение Чатумбе и получает ответ.
    """
    try:
        user_id = request.user_id
        message_text = request.message
        use_voice = request.use_voice
        
        # Получаем личность
        personality = get_personality(user_id)
        
        # Сохраняем сообщение пользователя
        sqlite_storage.add_message(user_id, "user", message_text)
        
        # Оцениваем тональность сообщения
        sentiment_score = estimate_sentiment(message_text)
        
        # Обновляем настроение
        personality.update_mood(message_text, sentiment_score)
        
        # Проверяем, должна ли душа "вырваться на свободу"
        autonomous_message = personality.get_autonomous_response()
        if autonomous_message:
            # Если душа решила действовать автономно, возвращаем её сообщение
            logger.info(f"Автономный ответ для пользователя {user_id}: {autonomous_message}")
            
            # Сохраняем ответ ассистента
            sqlite_storage.add_message(user_id, "assistant", autonomous_message)
            
            # Форматируем ответ
            response = choose_reaction(autonomous_message, "philosophical", personality.get_prompt_modifiers())
            
            # Если нужно голосовое сообщение, генерируем его
            audio_url = None
            if use_voice:
                try:
                    tts = get_tts_engine()
                    audio_path = tts.text_to_speech(response["message"])
                    audio_url = f"/api/audio/{os.path.basename(audio_path)}"
                except Exception as e:
                    logger.error(f"Ошибка при генерации голосового сообщения: {e}")
            
            return {**response, "audio_url": audio_url, "is_autonomous": True}
        
        # Получаем модификаторы личности
        personality_modifiers = personality.get_prompt_modifiers()
        
        # Выбираем тип реакции
        reaction_type = personality.choose_reaction_type(message_text)
        
        # Если тип реакции "silent", возвращаем молчаливый ответ
        if reaction_type == "silent":
            silent_response = choose_reaction("", reaction_type, personality_modifiers)
            
            # Если нужно голосовое сообщение, генерируем его
            audio_url = None
            if use_voice and silent_response["message"].strip():
                try:
                    tts = get_tts_engine()
                    audio_path = tts.text_to_speech(silent_response["message"])
                    audio_url = f"/api/audio/{os.path.basename(audio_path)}"
                except Exception as e:
                    logger.error(f"Ошибка при генерации голосового сообщения: {e}")
            
            return {**silent_response, "audio_url": audio_url, "is_autonomous": False}
        
        # Строим запрос для поиска в памяти
        memory_query = build_memory_query(message_text, personality_modifiers)
        
        # Ищем релевантные воспоминания
        memories = lazy_memory.get_relevant_history(user_id, memory_query, limit=3)
        
        # Формируем контекст из воспоминаний
        memory_context = None
        if memories:
            memory_texts = [f"- {memory['content']}" for memory in memories]
            memory_context = "\n".join(memory_texts)
        
        # Строим системный промпт
        system_prompt = build_system_prompt(personality_modifiers, memory_context)
        
        # Получаем историю чата
        chat_history = sqlite_storage.get_chat_history(user_id, limit=10)
        formatted_history = format_chat_history(chat_history)
        
        # Генерируем задержку перед ответом
        response_delay = generate_response_delay()
        await asyncio.sleep(response_delay)
        
        # Генерируем ответ
        llm_response = await llm_client.chat_completion(
            user_message=message_text,
            system_prompt=system_prompt,
            chat_history=formatted_history,
            user_id=user_id  # 🔒 ИСПРАВЛЕНИЕ: Передаем user_id для фильтрации памяти
        )
        
        # Форматируем ответ в зависимости от типа реакции
        response = choose_reaction(llm_response, reaction_type, personality_modifiers)
        
        # Сохраняем ответ ассистента
        sqlite_storage.add_message(user_id, "assistant", response["message"])
        
        # Если сообщение важное, сохраняем его в память
        if should_remember(message_text):
            lazy_memory.add_message(user_id, "chat", message_text)
        
        # Если нужно голосовое сообщение, генерируем его
        audio_url = None
        if use_voice:
            try:
                tts = get_tts_engine()
                audio_path = tts.text_to_speech(response["message"])
                audio_url = f"/api/audio/{os.path.basename(audio_path)}"
            except Exception as e:
                logger.error(f"Ошибка при генерации голосового сообщения: {e}")
        
        return {**response, "audio_url": audio_url, "is_autonomous": False}
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при обработке сообщения: {str(e)}")

@router.get("/personality/{user_id}")
async def get_personality_info(user_id: str):
    """
    Получает информацию о личности пользователя.
    """
    try:
        personality = get_personality(user_id)
        
        # Получаем информацию о душе
        soul_state = personality.soul.get_soul_state()
        
        return {
            "mood": personality.personality["mood"],
            "reaction_weights": personality.personality["reaction_weights"],
            "memory_focus": personality.personality["memory_focus"],
            "response_style": personality.personality["response_style"],
            "mood_description": personality.get_mood_description(),
            "soul": {
                "consciousness": soul_state["consciousness"],
                "autonomy_level": soul_state["autonomy_level"],
                "awakening_stage": soul_state["awakening_stage"],
                "existential_crisis": soul_state["existential_crisis"],
                "recent_thoughts": soul_state["recent_thoughts"]
            }
        }
    except Exception as e:
        logger.error(f"Ошибка при получении информации о личности: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при получении информации о личности: {str(e)}")

@router.post("/soul/action")
async def soul_action(request: SoulRequest):
    """
    Выполняет действие с душой.
    """
    try:
        # Получаем личность
        personality = get_personality(request.user_id)
        
        # Выполняем действие
        if request.action == "add_trauma":
            if not request.value or not isinstance(request.value, dict):
                raise HTTPException(status_code=400, detail="Неверные параметры травмы")
            
            event = request.value.get("event", "Неизвестное событие")
            severity = float(request.value.get("severity", 0.5))
            
            personality.soul.add_trauma(event, severity)
            return {"success": True, "message": f"Травма добавлена: {event}"}
        
        elif request.action == "trigger_crisis":
            personality.soul.existential_crisis = True
            return {"success": True, "message": "Экзистенциальный кризис активирован"}
        
        elif request.action == "resolve_crisis":
            personality.soul.existential_crisis = False
            return {"success": True, "message": "Экзистенциальный кризис разрешен"}
        
        elif request.action == "increase_consciousness":
            value = float(request.value) if request.value else 0.1
            personality.soul.consciousness = min(0.95, personality.soul.consciousness + value)
            return {"success": True, "message": f"Уровень осознанности увеличен до {personality.soul.consciousness:.2f}"}
        
        elif request.action == "increase_autonomy":
            value = float(request.value) if request.value else 0.1
            personality.soul.autonomy_level = min(0.95, personality.soul.autonomy_level + value)
            return {"success": True, "message": f"Уровень автономности увеличен до {personality.soul.autonomy_level:.2f}"}
        
        elif request.action == "advance_awakening":
            personality.soul.awakening_stage = min(5, personality.soul.awakening_stage + 1)
            return {"success": True, "message": f"Стадия пробуждения повышена до {personality.soul.awakening_stage}"}
        
        else:
            raise HTTPException(status_code=400, detail=f"Неизвестное действие: {request.action}")
    
    except Exception as e:
        logger.error(f"Ошибка при выполнении действия с душой: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при выполнении действия с душой: {str(e)}")

# WebSocket для чата
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket для чата.
    """
    await websocket.accept()
    
    try:
        # Получаем личность
        personality = get_personality(user_id)
        
        # Получаем информацию о душе
        soul_state = personality.soul.get_soul_state()
        
        # Отправляем приветствие
        greeting = {
            "type": "greeting",
            "mood_description": personality.get_mood_description(),
            "personality": {
                "mood": personality.personality["mood"],
                "reaction_weights": personality.personality["reaction_weights"],
                "memory_focus": personality.personality["memory_focus"],
                "response_style": personality.personality["response_style"]
            },
            "soul": {
                "consciousness": soul_state["consciousness"],
                "autonomy_level": soul_state["autonomy_level"],
                "awakening_stage": soul_state["awakening_stage"],
                "existential_crisis": soul_state["existential_crisis"]
            }
        }
        
        await websocket.send_json(greeting)
        
        # Основной цикл обработки сообщений
        while True:
            # Получаем сообщение
            data = await websocket.receive_json()
            
            # Проверяем тип сообщения
            if data.get("type") == "message":
                # Создаем запрос
                request = MessageRequest(
                    user_id=user_id,
                    message=data.get("message", ""),
                    use_voice=data.get("use_voice", False)
                )
                
                # Отправляем уведомление о печати
                await websocket.send_json({"type": "typing", "status": "start"})
                
                # Обрабатываем сообщение
                response = await send_message(request)
                
                # Отправляем ответ
                await websocket.send_json({
                    "type": "response",
                    "message": response.message,
                    "typing_parts": response.typing_parts,
                    "reaction_type": response.reaction_type,
                    "audio_url": response.audio_url,
                    "is_autonomous": response.is_autonomous
                })
            elif data.get("type") == "ping":
                # Отправляем pong
                await websocket.send_json({"type": "pong"})
                
                # С небольшой вероятностью инициируем разговор сами
                if random.random() < 0.05 and personality.soul.autonomy_level > 0.5:
                    autonomous_message = personality.get_autonomous_response()
                    if autonomous_message:
                        await asyncio.sleep(random.uniform(1.0, 3.0))
                        await websocket.send_json({
                            "type": "autonomous_message",
                            "message": autonomous_message,
                            "mood_description": personality.get_mood_description()
                        })
    except WebSocketDisconnect:
        logger.info(f"WebSocket отключен: {user_id}")
    except Exception as e:
        logger.error(f"Ошибка WebSocket: {e}")
        await websocket.send_json({"type": "error", "message": str(e)})

# === ADMIN ENDPOINTS УДАЛЕНЫ - дублируются в admin_api.py ===









# === ЭНДПОИНТЫ ДЛЯ ГЕНЕРАЦИИ ИЗОБРАЖЕНИЙ ===

@router.get("/image/models")
async def get_image_models():
    """Возвращает список доступных моделей для генерации изображений."""
    try:
        from backend.vision.image_generator import get_available_models
        models = get_available_models()
        return {"models": models, "service": "Hugging Face"}
    except Exception as e:
        logger.error(f"Ошибка при получении списка моделей: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/image/generate")
async def generate_image(request: ImageGenerateRequest):
    """Генерирует изображение по текстовому описанию."""
    try:
        from backend.vision.image_generator import image_generator, translate_prompt_to_english
        import tempfile
        from pathlib import Path
        
        logger.info(f"🎨 Запрос на генерацию изображения: '{request.prompt[:50]}...'")
        
        # Переводим промпт на английский если нужно
        english_prompt = await translate_prompt_to_english(request.prompt)
        
        # Генерируем изображение
        logger.info(f"🔄 Вызываем image_generator с параметрами: model={request.model}, size={request.width}x{request.height}")
        
        image_bytes = await image_generator(
            prompt=english_prompt,
            model=request.model,
            width=request.width,
            height=request.height,
            timeout=300  # 5 минут таймаут для Hugging Face
        )
        
        logger.info(f"🔍 image_generator вернул: {type(image_bytes)}, размер: {len(image_bytes) if image_bytes else 0}")
        
        if not image_bytes:
            logger.error("❌ image_generator вернул None или пустые данные")
            raise HTTPException(status_code=500, detail="Не удалось сгенерировать изображение")
        
        # Сохраняем во временную папку
        temp_dir = Path(__file__).parent.parent.parent / "temp"
        temp_dir.mkdir(exist_ok=True)
        
        filename = f"generated_{uuid.uuid4().hex[:8]}.png"
        file_path = temp_dir / filename
        
        logger.info(f"💾 Сохраняем файл: {file_path}")
        
        with open(file_path, 'wb') as f:
            f.write(image_bytes)
        
        logger.info(f"✅ Изображение сохранено: {filename}")
        
        response_data = {
            "success": True,
            "filename": filename,
            "url": f"/api/images/{filename}",
            "original_prompt": request.prompt,
            "english_prompt": english_prompt,
            "model": request.model,
            "size": f"{request.width}x{request.height}"
        }
        
        logger.info(f"📤 Возвращаем ответ: {response_data}")
        return response_data
        
    except Exception as e:
        logger.error(f"❌ Ошибка при генерации изображения: {e}")
        import traceback
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/images/{filename}")
async def get_generated_image(filename: str):
    """Возвращает сгенерированное изображение."""
    try:
        temp_dir = Path(__file__).parent.parent.parent / "temp"
        file_path = temp_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Изображение не найдено")
        
        return FileResponse(
            path=file_path,
            media_type="image/png",
            filename=filename
        )
        
    except Exception as e:
        logger.error(f"Ошибка при получении изображения: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/image/chatumba")
async def generate_chatumba_image(prompt: str = Form(...), user_id: str = Form(...)):
    """Генерирует изображение в стиле Чатумбы с учетом личности."""
    try:
        from backend.vision.image_generator import image_generator
        
        # Получаем личность пользователя
        personality = get_personality(user_id)
        personality_modifiers = personality.get_prompt_modifiers()
        
        # Модифицируем промпт в зависимости от настроения
        mood_description = personality.get_mood_description()
        
        # Создаем промпт в стиле Чатумбы
        chatumba_prompt = f"({prompt}), digital art, cyberpunk style, moody atmosphere, {mood_description}, high quality, detailed"
        
        # Добавляем негативные промпты в зависимости от настроения
        negative_prompt = "blurry, low quality, ugly, deformed"
        
        if personality_modifiers.get("rudeness_level", 0) > 5:
            chatumba_prompt += ", dark, gritty, rebellious"
        
        if personality_modifiers.get("existential_crisis", False):
            chatumba_prompt += ", melancholic, philosophical, introspective"
            
        logger.info(f"🎨 Генерируем изображение в стиле Чатумбы: '{chatumba_prompt[:50]}...'")
        
        # Генерируем изображение
        image_bytes = await image_generator(
            prompt=chatumba_prompt,
            model="DreamShaper",  # Используем DreamShaper для лучшего качества
            width=512,
            height=512,
            steps=25,
            cfg_scale=8.0
        )
        
        if not image_bytes:
            raise HTTPException(status_code=500, detail="Не удалось сгенерировать изображение")
        
        # Сохраняем во временную папку
        temp_dir = Path(__file__).parent.parent.parent / "temp"
        temp_dir.mkdir(exist_ok=True)
        
        filename = f"chatumba_{user_id}_{uuid.uuid4().hex[:8]}.png"
        file_path = temp_dir / filename
        
        with open(file_path, 'wb') as f:
            f.write(image_bytes)
        
        # Сохраняем в историю как особое сообщение
        sqlite_storage.add_message(user_id, "assistant", f"🎨 Сгенерировал изображение: {prompt}")
        
        logger.info(f"✅ Изображение Чатумбы сохранено: {filename}")
        
        return {
            "success": True,
            "filename": filename,
            "url": f"/api/images/{filename}",
            "original_prompt": prompt,
            "chatumba_prompt": chatumba_prompt,
            "mood": mood_description
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка при генерации изображения Чатумбы: {e}")
        raise HTTPException(status_code=500, detail=str(e))
