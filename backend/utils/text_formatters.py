import re
from typing import List


def _split_markdown_row(row: str) -> List[str]:
    # Убираем крайние | и сплитим по |, сохраняя пустые ячейки
    trimmed = row.strip()
    if trimmed.startswith('|'):
        trimmed = trimmed[1:]
    if trimmed.endswith('|'):
        trimmed = trimmed[:-1]
    parts = [cell.strip() for cell in trimmed.split('|')]
    return parts


def _is_separator_row(row: str) -> bool:
    # Строка вида |---|:---:|---|
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


def _format_table_block(lines: List[str], max_width: int = 50) -> str:
    # Парсим заголовок, разделитель и последующие строки до разрыва таблицы
    header = _split_markdown_row(lines[0])
    sep = lines[1]
    rows = []
    for r in lines[2:]:
        if not r.strip().startswith('|'):
            break
        if _is_separator_row(r):
            break
        rows.append(_split_markdown_row(r))

    # Выравниваем количество колонок
    num_cols = max(len(header), *(len(r) for r in rows)) if rows else len(header)
    header += [''] * (num_cols - len(header))
    for i in range(len(rows)):
        rows[i] += [''] * (num_cols - len(rows[i]))

    # Рассчитываем оптимальные ширины колонок
    widths = [0] * num_cols
    for i in range(num_cols):
        # Берем максимальную длину в колонке
        max_len = max(len(header[i]), *(len(r[i]) for r in rows) if rows else [0])
        # Ограничиваем максимальную ширину, но не слишком сильно
        widths[i] = min(max_len, max_width)
        # Минимальная ширина для читаемости
        widths[i] = max(widths[i], 8)

    def smart_cut(cell: str, w: int) -> str:
        """Умная обрезка с сохранением смысла"""
        if len(cell) <= w:
            return cell
        if w <= 3:
            return cell[:w]
        # Пытаемся обрезать по словам
        words = cell.split()
        if len(words) == 1:
            return cell[:w-1] + '…'
        result = ""
        for word in words:
            if len(result + " " + word) <= w:
                result += (" " if result else "") + word
            else:
                break
        if not result:
            result = cell[:w-1] + '…'
        return result

    def fmt_row(cells: List[str]) -> str:
        """Форматирование строки с выравниванием"""
        parts = []
        for i in range(num_cols):
            cell = smart_cut(cells[i], widths[i])
            # Выравниваем по левому краю с отступами
            parts.append(cell.ljust(widths[i]))
        return ' │ '.join(parts)

    # Формируем таблицу
    lines_out = []
    
    # Заголовок
    lines_out.append(fmt_row(header))
    
    # Разделитель (более красивый)
    separator = '─' * (sum(widths) + (num_cols - 1) * 3)  # 3 символа на разделитель
    lines_out.append(separator)
    
    # Строки данных
    for r in rows:
        lines_out.append(fmt_row(r))

    mono = '\n'.join(lines_out)
    # Возвращаем как Markdown-кодблок с подписью
    return f"```\n{mono}\n```"


def format_markdown_tables_for_telegram(text: str) -> str:
    """
    Находит markdown-таблицы и конвертирует их в моноширинный формат (code block)
    с выравниванием колонок. Если ширина слишком большая, ячейки обрезаются.
    """
    lines = text.splitlines()
    i = 0
    out: List[str] = []
    while i < len(lines):
        line = lines[i]
        # Ищем начало таблицы: строка с |... и следующая - разделитель
        if line.strip().startswith('|') and i + 1 < len(lines) and _is_separator_row(lines[i + 1]):
            # Собираем блок таблицы
            tbl_lines = [lines[i], lines[i + 1]]
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith('|') and not _is_separator_row(lines[j]):
                tbl_lines.append(lines[j])
                j += 1
            out.append(_format_table_block(tbl_lines))
            i = j
            continue
        out.append(line)
        i += 1
    return '\n'.join(out)


async def send_formatted_markdown_to_telegram(chat_id: str, raw_text: str):
    """
    Форматирует markdown-таблицы под Telegram и отправляет сообщением.
    Возвращает message_id либо None.
    Импорт отправки выполняется лениво, чтобы избежать циклических импортов.
    """
    formatted = format_markdown_tables_for_telegram(raw_text)
    from backend.api.telegram_core import send_telegram_message  # локальный импорт
    return await send_telegram_message(chat_id, formatted, parse_mode="Markdown")


