import re
import logging

logger = logging.getLogger(__name__)

def parse_formatted_plan_for_post(formatted_plan_text: str) -> dict | None:
    """
    Парсит уже отформатированный контент-план (MarkdownV2) и извлекает данные для первого дня.
    Эта функция предназначена для парсинга *всего* сгенерированного плана, чтобы найти ДЕНЬ 1.
    Ожидает, что заголовки дня и секций уже в Markdown (**День 1: Понедельник**).
    """
    # Ищем блок первого дня. Он начинается с жирного заголовка "**День 1: <День недели>**"
    # и заканчивается либо следующим разделителем "— — —" или "---", либо концом текста.
    day_1_block_match = re.search(
        r'^\s*\*\*(День 1:\s*\w+)\*\*(.*?)(?=\n\n(?:— — —|---|\*{2,4})|\Z)', # Added \*{2,4} to stop at extra asterisks
        formatted_plan_text, re.DOTALL | re.MULTILINE | re.IGNORECASE
    )
    
    if not day_1_block_match:
        logger.error("parse_formatted_plan_for_post: Failed to find Day 1 block (expected '**Day 1:**'). Full text start:\n---\n%s\n---" % formatted_plan_text[:500])
        return None 

    day_data = {
        'day_title': day_1_block_match.group(1).strip(), # Получаем "День 1: Понедельник"
        'topic_title': '',
        'description': '',
        'cta': '',
        'hashtags': '',
        'visuals': ''
    }
    
    day_content_raw_body = day_1_block_match.group(2).strip() # Содержимое дня 1 без заголовка дня
    
    # НОВОЕ: Удаляем любые лишние звездочки/разделители в начале содержимого дня
    day_content_raw_body = re.sub(r'^\s*(\*{2,4}\s*\n*)+', '', day_content_raw_body, flags=re.MULTILINE).strip()
    day_content_raw_body = re.sub(r'^\s*(?:—{3,}|-{3,})\s*\n*', '', day_content_raw_body).strip() # Удаляем разделители в начале блока

    # Тема дня (она должна быть жирной и идти сразу после заголовка дня)
    # Более гибкий поиск темы, игнорируя лишние звездочки и дубликаты
    topic_title_match = re.search(r'^\s*(?:\*{2,4}\s*)?\*\*(.*?)\*\*(?:\s*\*{2,4}\s*)?(?:Тема дня:\s*)?', day_content_raw_body, re.MULTILINE | re.DOTALL)
    if topic_title_match:
        topic_text = topic_title_match.group(1).strip()
        day_data['topic_title'] = topic_text
        day_content_raw_body = day_content_raw_body[topic_title_match.end():].strip()

    # Извлекаем остальные поля. Заголовки сами жирные: **Заголовок:**
    
    # Краткое описание
    desc_match = re.search(r'\*\*Краткое описание:\*\*\s*(?:Краткое описание:\s*)?(.*?)(?=\n\n\*\*|$)', day_content_raw_body, re.DOTALL | re.IGNORECASE)
    if desc_match:
        day_data['description'] = desc_match.group(1).strip()

    # Призыв к действию (СТА)
    cta_match = re.search(r'\*\*Призыв к действию \(СТА\):\*\*\s*(?:Призыв к действию \(СТА\):\s*)?(?:СТА:\s*)?(.*?)(?=\n\n\*\*|$)', day_content_raw_body, re.DOTALL | re.IGNORECASE)
    if cta_match:
        day_data['cta'] = cta_match.group(1).strip()

    # Хэштеги
    hashtags_match = re.search(r'\*\*Хэштеги:\*\*\s*(?:Хэштеги:\s*)?(.*?)(?=\n\n\*\*|$)', day_content_raw_body, re.DOTALL | re.IGNORECASE)
    if hashtags_match:
        tags_raw = hashtags_match.group(1).strip()
        tags_raw = re.sub(r'\*{1,4}', '', tags_raw) # Удаляем любые лишние звездочки
        day_data['hashtags'] = ' '.join([tag.strip('_') for tag in re.findall(r'_#\w+_|#\w+', tags_raw)]) # Ищем и _#_ и #_


    # Визуальные материалы
    visuals_match = re.search(r'\*\*Визуальные материалы:\*\*\s*(?:\*{2,4}\s*)?(?:Визуальные материалы:\s*)?(.*?)(?=\n\n\*\*|$)', day_content_raw_body, re.DOTALL | re.IGNORECASE)
    if visuals_match:
        day_data['visuals'] = visuals_match.group(1).strip()
    
    if not all(day_data[key] for key in ['topic_title', 'description', 'cta', 'hashtags', 'visuals']):
        logger.warning(f"parse_formatted_plan_for_post: Some critical fields are empty for Day 1: {day_data.get('day_title', 'Unknown Day')}.")

    return day_data
