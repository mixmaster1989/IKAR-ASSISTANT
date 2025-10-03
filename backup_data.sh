#!/bin/bash

# Скрипт для резервного копирования данных IKAR проекта
# Создает архив со всеми важными данными для переноса

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Начинаем резервное копирование данных IKAR...${NC}"

# Создаем директорию для бэкапа
BACKUP_DIR="/home/user1/IKAR_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo -e "${YELLOW}📁 Создана директория бэкапа: $BACKUP_DIR${NC}"

# 1. Копируем базы данных
echo -e "${YELLOW}💾 Копируем базы данных...${NC}"
mkdir -p "$BACKUP_DIR/data"
cp -r /home/user1/IKAR/data/*.db "$BACKUP_DIR/data/"
cp -r /home/user1/IKAR/backend/data/*.db "$BACKUP_DIR/data/"

# 2. Копируем память и историю чатов
echo -e "${YELLOW}🧠 Копируем память и историю чатов...${NC}"
cp -r /home/user1/IKAR/data/memory "$BACKUP_DIR/data/"
cp -r /home/user1/IKAR/exported_memory "$BACKUP_DIR/"
cp -r /home/user1/IKAR/data/soul_history "$BACKUP_DIR/data/"

# 3. Копируем логи
echo -e "${YELLOW}📋 Копируем логи...${NC}"
cp -r /home/user1/IKAR/logs "$BACKUP_DIR/"

# 4. Копируем временные файлы (аудио, изображения)
echo -e "${YELLOW}🎵 Копируем временные файлы...${NC}"
cp -r /home/user1/IKAR/temp "$BACKUP_DIR/"

# 5. Копируем модели и конфиги
echo -e "${YELLOW}🤖 Копируем модели и конфиги...${NC}"
cp /home/user1/IKAR/silero_tts.pt "$BACKUP_DIR/"
cp /home/user1/IKAR/yolov8n.pt "$BACKUP_DIR/"
cp /home/user1/IKAR/v2ray_config.json "$BACKUP_DIR/"

# 6. Копируем конфигурационные файлы PM2
echo -e "${YELLOW}⚙️ Копируем конфигурации PM2...${NC}"
cp /home/user1/IKAR/ecosystem*.config.js "$BACKUP_DIR/"
cp /home/user1/IKAR/localtunnel-manager.json "$BACKUP_DIR/"

# 7. Создаем файл с информацией о бэкапе
echo -e "${YELLOW}📝 Создаем информацию о бэкапе...${NC}"
cat > "$BACKUP_DIR/BACKUP_INFO.txt" << EOF
Резервная копия данных IKAR
Дата создания: $(date)
Версия: $(cd /home/user1/IKAR && git rev-parse --short HEAD)

Содержимое:
- Базы данных: chatumba.db, collective_mind.db, smart_memory.db, internet_intelligence.db, telegram_auth.db
- Память: exported_memory/, data/memory/vector_store/
- Логи: logs/
- Временные файлы: temp/
- Модели: silero_tts.pt, yolov8n.pt
- Конфиги: v2ray_config.json, ecosystem*.config.js

Для восстановления используйте restore_data.sh
EOF

# 8. Создаем архив
echo -e "${YELLOW}📦 Создаем архив...${NC}"
cd /home/user1
tar -czf "IKAR_data_backup_$(date +%Y%m%d_%H%M%S).tar.gz" "$(basename "$BACKUP_DIR")"

# 9. Показываем размеры
echo -e "${GREEN}✅ Резервное копирование завершено!${NC}"
echo -e "${GREEN}📊 Размеры файлов:${NC}"
du -sh "$BACKUP_DIR"
du -sh "IKAR_data_backup_$(date +%Y%m%d_%H%M%S).tar.gz"

echo -e "${GREEN}🎯 Готово! Данные сохранены в:${NC}"
echo -e "   📁 Директория: $BACKUP_DIR"
echo -e "   📦 Архив: /home/user1/IKAR_data_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
