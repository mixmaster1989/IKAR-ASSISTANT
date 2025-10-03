"""
Локальные модели для анализа изображений.
"""
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger("chatumba.local_vision")

class LocalVisionAnalyzer:
    """
    Локальный анализатор изображений с использованием OCR и детекции объектов.
    """
    
    def __init__(self):
        self.ocr_available = False
        self.yolo_available = False
        self._init_models()
    
    def _init_models(self):
        """Инициализация локальных моделей."""
        # EasyOCR отключен в ассистенте для снижения веса и зависимостей
        self.ocr_available = False
        
        # YOLO отключен в ассистенте для снижения веса и зависимостей
        self.yolo_available = False
    
    async def analyze_image(self, image_path: str, prompt: str = "") -> Optional[str]:
        """
        Анализирует изображение локально.
        
        Args:
            image_path: Путь к изображению
            prompt: Подсказка для анализа (игнорируется в локальной версии)
            
        Returns:
            Описание изображения
        """
        if not (self.ocr_available or self.yolo_available):
            return "Локальные модели анализа изображений не доступны."
        
        results = []
        
        # OCR - извлечение текста
        if self.ocr_available:
            try:
                ocr_results = self.ocr_reader.readtext(image_path)
                if ocr_results:
                    texts = [result[1] for result in ocr_results if result[2] > 0.5]  # Уверенность > 50%
                    if texts:
                        results.append(f"Текст на изображении: {', '.join(texts)}")
            except Exception as e:
                logger.error(f"Ошибка OCR: {e}")
        
        # YOLO - детекция объектов
        if self.yolo_available:
            try:
                yolo_results = self.yolo_model(image_path)
                if yolo_results:
                    objects = []
                    for result in yolo_results:
                        for box in result.boxes:
                            if box.conf > 0.5:  # Уверенность > 50%
                                class_id = int(box.cls)
                                class_name = self.yolo_model.names[class_id]
                                confidence = float(box.conf)
                                objects.append(f"{class_name} ({confidence:.1%})")
                    
                    if objects:
                        results.append(f"Объекты на изображении: {', '.join(objects)}")
            except Exception as e:
                logger.error(f"Ошибка YOLO: {e}")
        
        if results:
            return "На изображении обнаружено:\n" + "\n".join(results)
        else:
            return "Не удалось распознать содержимое изображения."