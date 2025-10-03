"""
Модуль для управления голосовыми движками в Telegram.
"""
from typing import Optional
from voice.tts import TextToSpeech
from voice.stt import SpeechToText
from utils.logger import get_logger

logger = get_logger("chatumba.voice")

# Глобальные экземпляры движков
tts_engine: Optional[TextToSpeech] = None
stt_engine: Optional[SpeechToText] = None

def get_tts_engine() -> TextToSpeech:
    """Получает экземпляр TTS движка."""
    global tts_engine
    logger.debug("🔍 Запрос TTS движка")
    if tts_engine is None:
        logger.info("🆕 Создание нового TTS движка")
        tts_engine = TextToSpeech()
        logger.info("✅ TTS движок создан")
    else:
        logger.debug("🔄 Возвращаем существующий TTS движок")
    return tts_engine

def get_stt_engine() -> SpeechToText:
    """Получает экземпляр STT движка."""
    global stt_engine
    logger.debug("🔍 Запрос STT движка")
    if stt_engine is None:
        logger.info("🆕 Создание нового STT движка")
        stt_engine = SpeechToText()
        logger.info("✅ STT движок создан")
    else:
        logger.debug("🔄 Возвращаем существующий STT движок")
    return stt_engine

def clear_voice_engines():
    """Очищает голосовые движки."""
    global tts_engine, stt_engine
    logger.info("🧹 Очистка голосовых движков")
    tts_engine = None
    stt_engine = None