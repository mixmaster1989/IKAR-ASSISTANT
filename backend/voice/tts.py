"""
Модуль для преобразования текста в речь (Text-to-Speech).
"""
import os
import logging
import tempfile
import re
import random
from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path
import json
import requests
from pydub import AudioSegment

logger = logging.getLogger("chatumba.tts")

class TextToSpeech:
    """
    Класс для преобразования текста в речь.
    """
    
    def __init__(self):
        """
        Инициализирует TTS движок.
        """
        self.use_rhvoice = False
        self.use_gtts = False
        self.use_elevenlabs = False
        self.rhvoice = None
        # ElevenLabs настройки
        self.eleven_api_keys: List[str] = []
        self.eleven_voice_id: Optional[str] = None
        self.eleven_model_id: str = os.getenv("ELEVEN_MODEL_ID", "eleven_multilingual_v2")
        self.eleven_output_format: str = os.getenv("ELEVEN_OUTPUT_FORMAT", "mp3_44100_128")
        self.eleven_preset: Optional[str] = os.getenv("ELEVEN_PRESET")
        self.eleven_settings = self._load_eleven_settings()
        
        # Создаем папку для временных файлов в проекте
        self.temp_dir = Path(__file__).parent.parent.parent / "temp"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Сбор ключей ElevenLabs (если есть — будем использовать как облачный провайдер)
        self.eleven_api_keys = self._collect_eleven_api_keys()
        if self.eleven_api_keys:
            self.eleven_voice_id = os.getenv("ELEVEN_VOICE_ID")
            if not self.eleven_voice_id:
                try:
                    vid = self._resolve_eleven_voice_id()
                    self.eleven_voice_id = vid
                    logger.info(f"ElevenLabs: выбран голос по умолчанию: {self.eleven_voice_id}")
                except Exception as e:
                    logger.warning(f"Не удалось получить список голосов ElevenLabs: {e}")
            self.use_elevenlabs = bool(self.eleven_voice_id)

        # Пробуем инициализировать RHVoice
        try:
            import importlib.util
            rhvoice_spec = importlib.util.find_spec("rhvoice_wrapper_bin")
            if rhvoice_spec is None:
                logger.warning("Модуль rhvoice_wrapper_bin не найден")
                raise ImportError("Модуль rhvoice_wrapper_bin не найден")
            import rhvoice_wrapper_bin  # noqa: F401
            from rhvoice_wrapper import RHVoice
            self.rhvoice = RHVoice()
            logger.info("RHVoice TTS создан успешно")
            try:
                voices = self.rhvoice.get_voices()
                logger.info(f"Доступные голоса RHVoice: {voices}")
            except Exception as e:
                logger.warning(f"Не удалось получить список голосов RHVoice: {e}")
            try:
                self.rhvoice.set_voice("aleksandr")
                self.use_rhvoice = True
                logger.info("RHVoice инициализирован с голосом Aleksandr")
            except Exception as e1:
                logger.warning(f"Не удалось установить голос Aleksandr: {e1}")
                try:
                    self.rhvoice.set_voice("anna")
                    self.use_rhvoice = True
                    logger.info("RHVoice инициализирован с голосом Anna")
                except Exception as e2:
                    logger.warning(f"Не удалось установить голос Anna: {e2}")
                    try:
                        self.rhvoice.set_voice("elena")
                        self.use_rhvoice = True
                        logger.info("RHVoice инициализирован с голосом Elena")
                    except Exception as e3:
                        logger.warning(f"Не удалось установить голос Elena: {e3}")
                        logger.warning("Русские голоса RHVoice не найдены")
        except ImportError as e:
            logger.warning(f"RHVoice не установлен: {e}, пробуем gTTS")
        except Exception as e:
            logger.warning(f"Ошибка инициализации RHVoice: {e}, пробуем gTTS")
        
        # Fallback на gTTS
        if not self.use_rhvoice and not self.use_elevenlabs:
            try:
                from gtts import gTTS
                self.use_gtts = True
                logger.info("gTTS инициализирован как fallback")
            except ImportError:
                logger.error("Ни RHVoice, ни gTTS не доступны!")

    def _collect_eleven_api_keys(self) -> List[str]:
        """
        Собирает ключи ElevenLabs из переменных окружения: ELEVEN_API, ELEVEN_API_KEY, ELEVEN_API2..ELEVEN_API10
        """
        keys: List[str] = []
        base = os.getenv("ELEVEN_API") or os.getenv("ELEVEN_API_KEY")
        if base:
            keys.append(base.strip())
        for i in range(2, 11):
            val = os.getenv(f"ELEVEN_API{i}")
            if val:
                keys.append(val.strip())
        return keys

    def _load_eleven_settings(self) -> dict:
        """
        Загружает настройки ElevenLabs из пресета/окружения.
        """
        presets = {
            "neutral":   {"stability": 0.6,  "similarity_boost": 0.7,  "style_exaggeration": 0.2, "use_speaker_boost": False},
            "emotional": {"stability": 0.25, "similarity_boost": 0.8,  "style_exaggeration": 0.6, "use_speaker_boost": True},
            "calm":      {"stability": 0.75, "similarity_boost": 0.7,  "style_exaggeration": 0.1, "use_speaker_boost": False},
            "energetic": {"stability": 0.2,  "similarity_boost": 0.85, "style_exaggeration": 0.7, "use_speaker_boost": True}
        }
        settings = presets.get(self.eleven_preset or "", {})

        def _f(name: str, default: float) -> float:
            val = os.getenv(f"ELEVEN_{name.upper()}")
            if val is None:
                return settings.get(name, default)
            try:
                return float(val)
            except Exception:
                return settings.get(name, default)

        return {
            "stability": _f("stability", 0.5),
            "similarity_boost": _f("similarity_boost", 0.75),
            "style_exaggeration": _f("style_exaggeration", 0.3),
            "use_speaker_boost": str(os.getenv("ELEVEN_SPEAKER_BOOST", str(settings.get("use_speaker_boost", True)))).lower() in ("1", "true", "yes")
        }

    def _resolve_eleven_voice_id(self) -> Optional[str]:
        """
        Получает voice_id из кэшированного файла или API.
        """
        # Сначала пробуем из кэшированного файла
        try:
            voices_file = Path(__file__).parent.parent.parent / 'data' / 'eleven_voices_ru.json'
            if voices_file.exists():
                with open(voices_file, 'r', encoding='utf-8') as f:
                    voices = json.load(f)
                    if voices:
                        # Выбираем женский голос по умолчанию
                        for voice in voices:
                            if voice.get('gender') == 'female':
                                voice_id = voice.get('voice_id')
                                if voice_id:
                                    logger.info(f"🎤 Используем кэшированный женский голос: {voice.get('name')} ({voice_id})")
                                    return voice_id
                        # Если женского нет, берем первый
                        voice_id = voices[0].get('voice_id')
                        if voice_id:
                            logger.info(f"🎤 Используем кэшированный голос: {voices[0].get('name')} ({voice_id})")
                            return voice_id
        except Exception as e:
            logger.warning(f"Ошибка чтения кэшированных голосов: {e}")
        
        # Fallback: пробуем API
        url = "https://api.elevenlabs.io/v1/voices"
        
        # Прокси отключен
        proxies = {}
        
        for key in self.eleven_api_keys:
            headers = {"xi-api-key": key}
            try:
                resp = requests.get(url, headers=headers, timeout=15)
                if resp.ok:
                    data = resp.json()
                    voices = data.get("voices") or []
                    if voices:
                        return voices[0].get("voice_id")
                else:
                    try:
                        txt = resp.text
                    except Exception:
                        txt = ""
                    logger.warning(f"ElevenLabs voices HTTP {resp.status_code}: {txt[:120]}")
            except Exception as e:
                logger.warning(f"Ошибка запроса ElevenLabs voices: {e}")
        return None

    # Удалены silero-методы и усилители выражения

    def _create_elevenlabs_audio(self, text: str, is_action: bool = False) -> str:
        """
        Создает аудио через ElevenLabs TTS.
        """
        if not self.eleven_voice_id:
            return ""
        payload = {
            "text": text,
            "model_id": self.eleven_model_id,
            "voice_settings": {
                "stability": self.eleven_settings.get("stability", 0.5),
                "similarity_boost": self.eleven_settings.get("similarity_boost", 0.75),
                "style_exaggeration": self.eleven_settings.get("style_exaggeration", 0.3),
                "use_speaker_boost": self.eleven_settings.get("use_speaker_boost", True)
            },
            "output_format": self.eleven_output_format,
            "optimize_streaming_latency": 2
        }
        file_id = hash(text + str(is_action)) % 10000
        ext = ".mp3" if "mp3" in self.eleven_output_format else ".wav"
        output_path = self.temp_dir / f"eleven_part_{file_id}{ext}"
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.eleven_voice_id}"
        
        # Прокси отключен
        proxies = {}
        
        for key in self.eleven_api_keys:
            headers = {"xi-api-key": key, "Content-Type": "application/json"}
            try:
                resp = requests.post(url, headers=headers, data=json.dumps(payload).encode("utf-8"), timeout=60)
                if resp.ok and resp.content:
                    with open(output_path, "wb") as f:
                        f.write(resp.content)
                    logger.info(f"💬 ElevenLabs аудио: {text[:30]}...")
                    return str(output_path)
                else:
                    logger.warning(f"ElevenLabs ответ {resp.status_code}: {resp.text[:120]}")
            except Exception as e:
                logger.warning(f"Ошибка ElevenLabs ({key[:6]}...): {e}")
        return ""
    
    def _parse_text_with_actions(self, text: str) -> List[Tuple[str, str]]:
        """
        Парсит текст, выделяя обычную речь и действия в *.
        """
        parts = []
        pattern = r'\*([^*]+)\*'
        last_end = 0
        
        for match in re.finditer(pattern, text):
            if match.start() > last_end:
                speech_text = text[last_end:match.start()].strip()
                if speech_text:
                    parts.append((speech_text, 'speech'))
            
            action_text = match.group(1).strip()
            if action_text:
                parts.append((action_text, 'action'))
            
            last_end = match.end()
        
        if last_end < len(text):
            remaining_text = text[last_end:].strip()
            if remaining_text:
                parts.append((remaining_text, 'speech'))
        
        return parts
    
    # Удален silero-провайдер
    
    def _create_rhvoice_audio(self, text: str, is_action: bool = False) -> str:
        """
        Создает аудио через RHVoice.
        """
        try:
            file_id = hash(text + str(is_action)) % 10000
            output_path = self.temp_dir / f"rhvoice_part_{file_id}.wav"
            
            if is_action:
                # Для действий изменяем параметры речи
                modified_text = f"... {text} ..."
                # Замедляем речь для действий
                self.rhvoice.set_rate(30)  # Медленнее (0-100)
                self.rhvoice.set_pitch(80)  # Ниже тон (0-100)
            else:
                modified_text = text
                # Обычные параметры
                self.rhvoice.set_rate(50)  # Нормальная скорость
                self.rhvoice.set_pitch(100)  # Обычный тон
            
            # Генерируем аудио и сохраняем в файл
            self.rhvoice.to_file(modified_text, str(output_path))
            
            logger.info(f"{'🎭' if is_action else '💬'} RHVoice аудио: {text[:30]}...")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Ошибка RHVoice: {e}")
            return ""
    
    def _create_gtts_audio(self, text: str, is_action: bool = False) -> str:
        """
        Создает аудио через gTTS.
        """
        try:
            from gtts import gTTS
            
            file_id = hash(text + str(is_action)) % 10000
            output_path = self.temp_dir / f"gtts_part_{file_id}.mp3"
            
            if is_action:
                modified_text = f"... {text} ..."
                tts = gTTS(text=modified_text, lang='ru', slow=True, tld='com')
            else:
                tts = gTTS(text=text, lang='ru', slow=False, tld='ru')
            
            tts.save(str(output_path))
            logger.info(f"{'🎭' if is_action else '💬'} gTTS аудио: {text[:30]}...")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Ошибка gTTS: {e}")
            return ""
    
    def _combine_audio_files(self, audio_files: List[str], output_path: str):
        """
        Объединяет аудиофайлы в один.
        """
        # Проверяем, что есть хотя бы один файл
        if not audio_files:
            logger.error("Нет файлов для объединения")
            return
        
        # Если только один файл, просто копируем его
        if len(audio_files) == 1 and os.path.exists(audio_files[0]):
            import shutil
            shutil.copy2(audio_files[0], output_path)
            logger.info(f"Скопирован единственный файл: {audio_files[0]} -> {output_path}")
            return
        
        # Объединяем через pydub
        try:
            combined: Optional[AudioSegment] = None
            for audio_file in audio_files:
                if os.path.exists(audio_file):
                    try:
                        seg = AudioSegment.from_file(audio_file)
                        if combined is None:
                            combined = seg
                        else:
                            combined += AudioSegment.silent(duration=500)
                            combined += seg
                    except Exception as e:
                        logger.warning(f"Не удалось загрузить файл {audio_file}: {e}")
            if combined is None:
                raise ValueError("Не удалось загрузить ни один аудиофайл")
            combined.export(output_path, format=os.path.splitext(output_path)[1].lstrip('.') or 'mp3')
            logger.info(f"Аудио объединено через pydub: {output_path}")
            for audio_file in audio_files:
                try:
                    os.remove(audio_file)
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Ошибка объединения аудио: {e}")
            if audio_files and os.path.exists(audio_files[0]):
                import shutil
                shutil.copy2(audio_files[0], output_path)
                logger.info(f"Fallback: скопирован первый файл {audio_files[0]}")
            else:
                logger.error("Не удалось объединить аудио и нет файлов для копирования")
    
    def text_to_speech(self, text: str, output_path: Optional[str] = None) -> str:
        """
        Преобразует текст в речь с поддержкой действий в *.
        """
        if not self.use_rhvoice and not (self.use_elevenlabs or self.use_gtts):
            raise ValueError("TTS не доступен")
        
        # Определяем формат выходного файла
        if not output_path:
            ext = ".wav" if self.use_rhvoice else ".mp3"
            output_path = self.temp_dir / f"chatumba_tts_{hash(text) % 10000}{ext}"
        
        logger.info(f"🎤 СОЗДАЕМ TTS ДЛЯ: {text[:50]}...")
        engine_name = "RHVoice" if self.use_rhvoice else "gTTS"
        print(f"🎤 TTS ({engine_name}): {text[:50]}...")
        
        # Парсим текст на части
        parts = self._parse_text_with_actions(text)
        
        logger.info(f"📝 НАЙДЕНО ЧАСТЕЙ: {len(parts)}")
        for i, (part_text, part_type) in enumerate(parts):
            logger.info(f"  {i+1}. {part_type}: {part_text[:30]}...")
        
        # Если только одна часть без действий, создаем простое аудио
        if len(parts) == 1 and parts[0][1] == 'speech':
            if self.use_elevenlabs:
                audio_path = self._create_elevenlabs_audio(parts[0][0], False)
            elif self.use_rhvoice:
                audio_path = self._create_rhvoice_audio(parts[0][0], False)
            else:
                audio_path = self._create_gtts_audio(parts[0][0], False)
            
            if audio_path and os.path.exists(audio_path):
                import shutil
                shutil.move(audio_path, str(output_path))
            logger.info(f"✅ ПРОСТОЕ АУДИО: {output_path}")
            return str(output_path)
        
        # Создаем аудио для каждой части
        temp_files = []
        
        for i, (part_text, part_type) in enumerate(parts):
            is_action = (part_type == 'action')
            
            if self.use_elevenlabs:
                audio_path = self._create_elevenlabs_audio(part_text, is_action)
            elif self.use_rhvoice:
                audio_path = self._create_rhvoice_audio(part_text, is_action)
            else:
                audio_path = self._create_gtts_audio(part_text, is_action)
            
            if audio_path:
                temp_files.append(audio_path)
        
        # Объединяем все части
        if temp_files:
            self._combine_audio_files(temp_files, str(output_path))
            logger.info(f"✅ МНОГОСЛОЙНОЕ АУДИО: {output_path}")
        else:
            logger.error("❌ НЕ УДАЛОСЬ СОЗДАТЬ АУДИО ЧАСТИ")
        
        return str(output_path)

    def _create_elevenlabs_audio_custom(
        self,
        text: str,
        *,
        voice_id: Optional[str] = None,
        model_id: Optional[str] = None,
        output_format: Optional[str] = None,
        stability: Optional[float] = None,
        similarity_boost: Optional[float] = None,
        style_exaggeration: Optional[float] = None,
        use_speaker_boost: Optional[bool] = None,
    ) -> str:
        if not (self.use_elevenlabs and (voice_id or self.eleven_voice_id)):
            return ""
        vid = voice_id or self.eleven_voice_id
        mid = model_id or self.eleven_model_id
        fmt = output_format or self.eleven_output_format
        settings = {
            "stability": self.eleven_settings.get("stability", 0.5) if stability is None else stability,
            "similarity_boost": self.eleven_settings.get("similarity_boost", 0.75) if similarity_boost is None else similarity_boost,
            "style_exaggeration": self.eleven_settings.get("style_exaggeration", 0.3) if style_exaggeration is None else style_exaggeration,
            "use_speaker_boost": self.eleven_settings.get("use_speaker_boost", True) if use_speaker_boost is None else use_speaker_boost,
        }
        payload = {
            "text": text,
            "model_id": mid,
            "voice_settings": settings,
            "output_format": fmt,
            "optimize_streaming_latency": 2,
        }
        file_id = hash((text, vid, mid, fmt)) % 100000
        ext = ".mp3" if "mp3" in fmt else ".wav"
        output_path = self.temp_dir / f"eleven_custom_{file_id}{ext}"
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{vid}"
        for key in self.eleven_api_keys:
            headers = {"xi-api-key": key, "Content-Type": "application/json"}
            try:
                resp = requests.post(url, headers=headers, data=json.dumps(payload).encode("utf-8"), timeout=60)
                if resp.ok and resp.content:
                    with open(output_path, "wb") as f:
                        f.write(resp.content)
                    logger.info(f"💬 ElevenLabs аудио (custom): {text[:30]}...")
                    return str(output_path)
                else:
                    logger.warning(f"ElevenLabs ответ {resp.status_code}: {resp.text[:120]}")
            except Exception as e:
                logger.warning(f"Ошибка ElevenLabs ({key[:6]}...): {e}")
        return ""

    def text_to_speech_with_params(self, text: str, params: Optional[dict] = None, output_path: Optional[str] = None) -> str:
        """
        Преобразует текст в речь с пер-вызовными параметрами (для управления эмоциями/голосом).
        Поддерживаемые ключи params: voice_id, model_id, output_format,
        stability, similarity_boost, style_exaggeration, use_speaker_boost.
        """
        params = params or {}
        provider = params.get("provider", "")
        
        # Если явно указан ElevenLabs
        if provider == "elevenlabs" and self.use_elevenlabs:
            # Маппинг voice_id по полу при отсутствии явного voice_id
            voice_id = params.get("voice_id")
            voice = params.get("voice") or {}
            if not voice_id and isinstance(voice, dict):
                mapped = self._map_voice_id_by_gender(voice)
                if mapped:
                    voice_id = mapped

            audio_path = self._create_elevenlabs_audio_custom(
                text,
                voice_id=voice_id,
                model_id=params.get("model_id"),
                output_format=params.get("output_format"),
                stability=params.get("stability"),
                similarity_boost=params.get("similarity_boost"),
                style_exaggeration=params.get("style_exaggeration"),
                use_speaker_boost=params.get("use_speaker_boost"),
            )
            if audio_path:
                return audio_path
        
        # Явный провайдер silero более не поддерживается
        if provider == "silero":
            logger.warning("Silero TTS удален из проекта, используем доступный fallback")
        
        # Фолбэк на имеющиеся движки
        return self.text_to_speech(text, output_path)

    def _map_voice_id_by_gender(self, voice: dict) -> Optional[str]:
        """
        Возвращает voice_id из окружения по полу: ELEVEN_VOICE_ID_FEMALE / ELEVEN_VOICE_ID_MALE,
        иначе ELEVEN_VOICE_ID. Если ничего нет — None.
        """
        gender = str(voice.get("gender", "")).lower()
        # 1) Пробуем из .env
        if gender == "female":
            vid = os.getenv("ELEVEN_VOICE_ID_FEMALE") or os.getenv("ELEVEN_VOICE_ID")
            if vid:
                return vid
        if gender == "male":
            vid = os.getenv("ELEVEN_VOICE_ID_MALE") or os.getenv("ELEVEN_VOICE_ID")
            if vid:
                return vid
        env_vid = os.getenv("ELEVEN_VOICE_ID")
        if env_vid:
            return env_vid
        # 2) Пробуем выбрать из локального кэша voices (data/eleven_voices_ru.json)
        try:
            from pathlib import Path
            voices_path = Path(__file__).resolve().parents[2] / 'data' / 'eleven_voices_ru.json'
            if voices_path.exists():
                import json as _json
                data = _json.loads(voices_path.read_text(encoding='utf-8'))
                # Фильтр по полу на основе метаданных name/labels, если возможно
                def is_match(v: dict) -> bool:
                    nm = (v.get('name') or '').lower()
                    if gender == 'female':
                        return any(k in nm for k in ['female','woman','жен', 'anna','dariya','tatyana'])
                    if gender == 'male':
                        return any(k in nm for k in ['male','man','муж','alex','sergey','dmitry'])
                    return True
                for v in data:
                    if is_match(v):
                        vid = v.get('voice_id') or v.get('voiceID')
                        if vid:
                            return vid
        except Exception:
            pass
        return None