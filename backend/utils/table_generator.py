import matplotlib.pyplot as plt
from matplotlib import font_manager
import logging
import warnings
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import numpy as np
import re
from typing import List, Tuple, Optional
import io
import base64
import os

# Настройка шрифтов и эмодзи
# Предпочитаем доступные системные шрифты: DejaVu (кириллица), Noto Color Emoji (эмодзи)
preferred_fonts = ['DejaVu Sans', 'Liberation Sans', 'Noto Color Emoji', 'sans-serif']
plt.rcParams['font.family'] = preferred_fonts
plt.rcParams['font.sans-serif'] = preferred_fonts
plt.rcParams['font.size'] = 10
plt.rcParams['axes.unicode_minus'] = False

# Пытаемся добавить в список пути системных шрифтов, если установлены
def _ensure_font_available(font_name: str) -> bool:
    try:
        font_manager.findfont(font_name, fallback_to_default=False)
        return True
    except Exception:
        return False

# Тихо проверяем наличие ключевых шрифтов
_dejavu_ok = _ensure_font_available('DejaVu Sans')
_emoji_ok = _ensure_font_available('Noto Color Emoji')

# Явно регистрируем системные TTF, если Python их не видит
_font_candidates = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
    '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf',
]
for _path in _font_candidates:
    try:
        if os.path.exists(_path):
            font_manager.fontManager.addfont(_path)
    except Exception:
        pass

# Обновляем менеджер шрифтов после добавления
try:
    font_manager._load_fontmanager(try_read_cache=False)
except Exception:
    pass

# Снижаем болтливость findfont в логах
warnings.filterwarnings(
    "ignore",
    message=r"findfont: Font family '.*' not found.",
    category=UserWarning,
    module='matplotlib.font_manager'
)

# Глушим болтливость логгера matplotlib.font_manager
try:
    logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)
except Exception:
    pass

# Жестко задаем главные шрифты, если доступны
for fam, path in [
    ('DejaVu Sans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
    ('Noto Color Emoji', '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'),
    ('Liberation Sans', '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'),
]:
    if os.path.exists(path):
        try:
            font_manager.fontManager.addfont(path)
        except Exception:
            pass



def _split_markdown_row(row: str) -> List[str]:
    """Разбивает строку markdown таблицы на ячейки"""
    trimmed = row.strip()
    if trimmed.startswith('|'):
        trimmed = trimmed[1:]
    if trimmed.endswith('|'):
        trimmed = trimmed[:-1]
    parts = [cell.strip() for cell in trimmed.split('|')]
    return parts

def _is_separator_row(row: str) -> bool:
    """Проверяет, является ли строка разделителем таблицы"""
    trimmed = row.strip()
    if not (trimmed.startswith('|') and trimmed.endswith('|')):
        return False
    inner = trimmed[1:-1]
    cells = [c.strip() for c in inner.split('|')]
    if not cells:
        return False
    for c in cells:
        if not re.fullmatch(r':?-{3,}:?', c):
            return False
    return True

def create_table_image(markdown_text: str, output_path: str = None) -> str:
    """
    Создает изображение таблицы из markdown текста
    
    Args:
        markdown_text: Текст с markdown таблицей
        output_path: Путь для сохранения (если None, создается временный файл)
    
    Returns:
        Путь к созданному изображению
    """
    lines = markdown_text.splitlines()
    
    # Находим таблицу
    table_start = None
    table_end = None
    
    for i, line in enumerate(lines):
        if line.strip().startswith('|') and not _is_separator_row(line):
            if table_start is None:
                table_start = i
        elif table_start is not None and not line.strip().startswith('|'):
            table_end = i
            break
    
    if table_start is None:
        raise ValueError("Таблица не найдена в тексте")
    
    if table_end is None:
        table_end = len(lines)
    
    # Парсим таблицу
    table_lines = lines[table_start:table_end]
    header = _split_markdown_row(table_lines[0])
    
    # Пропускаем разделитель
    data_rows = []
    for line in table_lines[2:]:
        if line.strip().startswith('|') and not _is_separator_row(line):
            data_rows.append(_split_markdown_row(line))
    
    # Подготавливаем данные + нормализация переносов/пробелов
    all_rows = [header] + data_rows
    for r in range(len(all_rows)):
        for c in range(len(all_rows[r])):
            val = all_rows[r][c] if all_rows[r][c] is not None else ""
            val = re.sub(r"<br\s*/?>", "\n", str(val), flags=re.IGNORECASE)
            val = val.replace("&nbsp;", " ")
            val = "\n".join(s.strip() for s in val.splitlines())
            all_rows[r][c] = val
    num_cols = len(header)
    num_rows = len(all_rows)
    
    # Ширины колонок: последняя (описание) шире
    col_weights = [1.0] * num_cols
    if num_cols >= 1:
        col_weights[-1] = 2.4  # расширяем правый столбец
    total_w = sum(col_weights)

    # Создаем фигуру
    fig_width = max(12, int(total_w) * 3)
    fig_height = max(6, num_rows * 0.85)
    
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.set_xlim(0, total_w)
    ax.set_ylim(0, num_rows)
    ax.axis('off')
    
    # Цвета
    header_color = '#4A90E2'  # Синий
    row_colors = ['#F8F9FA', '#FFFFFF']  # Чередующиеся цвета строк
    text_color = '#2C3E50'
    border_color = '#BDC3C7'
    
    # Определяем столбцы-цены → выравнивание вправо
    price_re = re.compile(r"^(?:\d+[\s\u00A0]?)+(?:₽|р\.?|RUB)?$", re.IGNORECASE)
    align_right_cols = [False] * num_cols
    for c in range(num_cols):
        price_like = 0
        checked = 0
        for r in range(1, num_rows):
            if c < len(all_rows[r]):
                sample = all_rows[r][c].strip().replace(' ', '')
                if sample:
                    checked += 1
                    if price_re.match(sample):
                        price_like += 1
        if checked and price_like / max(1, checked) >= 0.6:
            align_right_cols[c] = True

    # Преподсчет X-координат
    x_positions = [0.0]
    for i in range(num_cols - 1):
        x_positions.append(x_positions[-1] + col_weights[i])

    # Хелпер переноса текста по ширине столбца (грубая оценка символов)
    def wrap_text(text: str, weight: float, base_chars: int = 22) -> str:
        if not text:
            return ""
        max_chars = max(12, int(base_chars * weight))
        words = str(text).split()
        lines = []
        cur = ""
        for w in words:
            if len(cur) + (1 if cur else 0) + len(w) <= max_chars:
                cur = (cur + " " + w) if cur else w
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return "\n".join(lines)

    # Создаем ячейки
    for row_idx in range(num_rows):
        for col_idx in range(num_cols):
            # Цвет фона
            if row_idx == 0:  # Заголовок
                bg_color = header_color
                text_color_cell = 'white'
            else:
                bg_color = row_colors[row_idx % 2]
                text_color_cell = text_color
            
            # Создаем прямоугольник
            rect = FancyBboxPatch(
                (x_positions[col_idx], num_rows - row_idx - 1),
                col_weights[col_idx], 1,
                boxstyle="round,pad=0.01",
                facecolor=bg_color,
                edgecolor=border_color,
                linewidth=1.5
            )
            ax.add_patch(rect)
            
            # Добавляем текст
            if col_idx < len(all_rows[row_idx]):
                cell_text = all_rows[row_idx][col_idx]
                # Убираем markdown форматирование
                cell_text = re.sub(r'\*\*(.*?)\*\*', r'\1', cell_text)  # **bold**
                cell_text = re.sub(r'\*(.*?)\*', r'\1', cell_text)      # *italic*
                # Перенос по ширине столбца
                cell_text = wrap_text(cell_text, col_weights[col_idx], base_chars=24 if col_idx == num_cols - 1 else 20)

                ha_val = 'center' if row_idx == 0 else ('right' if align_right_cols[col_idx] else 'left')
                x_text = (
                    x_positions[col_idx] + col_weights[col_idx] / 2.0 if ha_val == 'center'
                    else x_positions[col_idx] + col_weights[col_idx] - 0.06 if ha_val == 'right'
                    else x_positions[col_idx] + 0.06
                )
                ax.text(
                    x_text,
                    num_rows - row_idx - 0.5,
                    cell_text,
                    ha=ha_val, va='center',
                    fontsize=9,
                    color=text_color_cell,
                    weight='bold' if row_idx == 0 else 'normal',
                    linespacing=1.0,
                )
    
    # Настройка осей
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Заголовок
    # Заменяем на поддерживаемый символ галочки (без предупреждений)
    title_text = "✓ Сравнение кассовых систем Evotor и Atol Sigma"
    fig.suptitle(title_text, fontsize=14, fontweight='bold', y=0.95)
    
    # Сохраняем
    if output_path is None:
        output_path = f"/tmp/table_{hash(markdown_text) % 10000}.png"
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()
    
    return output_path

def create_table_from_markdown(markdown_text: str) -> str:
    """
    Создает изображение таблицы и возвращает путь к файлу
    """
    return create_table_image(markdown_text)

# Функция для отправки таблицы в Telegram
async def send_table_to_telegram(chat_id: str, markdown_text: str, caption: str = None):
    """
    Создает таблицу как изображение и отправляет в Telegram
    """
    try:
        # Создаем изображение таблицы
        image_path = create_table_from_markdown(markdown_text)
        
        # Импортируем функцию отправки фото
        from backend.api.telegram_core import send_telegram_photo
        
        # Отправляем
        result = await send_telegram_photo(chat_id, image_path, caption)
        
        # Удаляем временный файл
        if os.path.exists(image_path):
            os.remove(image_path)
            
        return result
        
    except Exception as e:
        print(f"Ошибка создания таблицы: {e}")
        return None
