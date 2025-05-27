import asyncio
import re
from openai import AsyncOpenAI
from app.utils.markdown_utils import escape_markdown_v2 
from app.utils.message_utils import split_text
from config import AI_TOKEN

# Инициализация клиента OpenRouter
client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=AI_TOKEN,
)

async def generate(prompt: str) -> str:
    try:
        completion = await client.chat.completions.create(
            model="google/gemma-3n-e4b-it:free", 
            messages=[
                {"role": "user", "content": prompt}
            ],
            timeout=40
        )

        if completion and hasattr(completion, 'choices') and len(completion.choices):
            content = completion.choices[0].message.content

            # 1. Очистка текста от лишних символов (ТОЛЬКО шум, оставляем маркеры для format_content)
            content = clean_content(content)
            
            # 2. Форматирование текста (добавление Markdown на основе чистых данных)
            content = format_content(content)

            # 3. Экранирование MarkdownV2 (только здесь и только один раз)
            content = escape_markdown_v2(content) 

            return content.strip() if content else "Модель не вернула содержание."
        else:
            return "Не удалось получить ответ от модели."
    except Exception as e:
        print(f"Ошибка при работе с ИИ: {e}")
        return "Произошла ошибка при генерации. Пожалуйста, попробуйте еще раз."


def clean_content(content: str) -> str:

    # Удалить все последовательности бэкслешей (\)
    content = re.sub(r'\\+', '', content)

    content = re.sub(r'__+', '', content) 
    content = re.sub(r'---+', '', content)

    # Нормализация пробелов и переносов строк
    content = re.sub(r'[ \t]+', ' ', content).strip() 
    content = re.sub(r'\n{3,}', '\n\n', content) 
    content = re.sub(r' \n', '\n', content) 
    content = re.sub(r'\n ', '\n', content) 

    return content.strip()


def format_content(content: str) -> str:
  
    # Разделяем весь контент на блоки по заголовкам дней.
    day_blocks = re.findall(r'(День \d+:\s*\w+\s*(?:(?:\n|\s)*.*?(?=\n\n*День \d+:\s*\w+|$))?)', content, re.DOTALL | re.IGNORECASE)
    
    formatted_output = []
    
    # Обработка первой части, если она не является заголовком дня
    if day_blocks and not re.match(r'День \d+:\s*\w+:', day_blocks[0].strip(), re.IGNORECASE):

        if day_blocks[0].strip():
            
            formatted_output.append(f"**Вступление:**\n\n{day_blocks[0].strip()}")
        day_blocks = day_blocks[1:]

    for day_block_raw in day_blocks:
        day_header_match = re.match(r'(День \d+:\s*\w+)', day_block_raw, re.IGNORECASE)
        if not day_header_match:
            continue

        day_header = day_header_match.group(1).strip()
        day_content_raw = day_block_raw[day_header_match.end():].strip()

        formatted_day_header = f"**{day_header}**"
        formatted_output.append(formatted_day_header)
        
        section_pattern = r'(Тема дня:|Краткое описание:|В примерах —|Примеры:|Бонус:|СТА:|Spoiler:|Хэштеги:|Визуальные материалы:|Результаты:|Инфографика:|Карточка с мемом:|Гифка с роботом-котом:|Скачайте чек-лист:|Дополнительно:|Примеры использования:|Ключевые выводы:)(.*?)(?=\n\n*(?:Тема дня:|Краткое описание:|В примерах —|Примеры:|Бонус:|СТА:|Spoiler:|Хэштеги:|Визуальные материалы:|Результаты:|Инфографика:|Карточка с мемом:|Гифка с роботом-котом:|Скачайте чек-лист:|Дополнительно:|Примеры использования:|Ключевые выводы:)|$)'
        
        sections = re.findall(section_pattern, day_content_raw, re.DOTALL | re.IGNORECASE)
        
        formatted_day_sections = []
        
        # Обрабатываем текст, который идет до первой секции (считаем это названием темы)
        initial_text_match = re.match(r'^(.*?)(?:Тема дня:|Краткое описание:|В примерах —|Примеры:|Бонус:|СТА:|Spoiler:|Хэштеги:|Визуальные материалы:|Результаты:|Инфографика:|Карточка с мемом:|Гифка с роботом-котом:|Скачайте чек-лист:|Дополнительно:|Примеры использования:|Ключевые выводы:|$)', day_content_raw, re.DOTALL | re.IGNORECASE)
        if initial_text_match and initial_text_match.group(1).strip():
            formatted_day_sections.append(f'\n\n**{initial_text_match.group(1).strip()}**')
            day_content_raw = day_content_raw[initial_text_match.end():].strip() 

        # Обрабатываем найденные секции
        for title, content_block in sections:
            title = title.strip().replace(':', '') 
            content_block = content_block.strip()

            # Нормализация названия секции для отображения
            if title.lower() == 'ста':
                display_title = 'Призыв к действию (СТА)'
            elif title.lower() in ['в примерах —', 'примеры', 'примеры использования']:
                display_title = 'Примеры'
            elif title.lower() == 'spoiler':
                display_title = 'Спойлер'
            elif title.lower() in ['визуальные материалы', 'гифка с роботом-котом', 'карточка с мемом', 'инфографика']:
                display_title = 'Визуальные материалы'
            elif title.lower() == 'скачайте чек-лист':
                display_title = 'Чек-лист'
            elif title.lower() == 'тема дня':
                display_title = 'Тема дня' 
            elif title.lower() == 'краткое описание':
                display_title = 'Краткое описание'
            else:
                display_title = title.capitalize() 

            # Добавляем заголовок секции жирным шрифтом и её содержимое
            if content_block:
                # Если секция - это список, убедимся, что формат списка сохранен
                if re.match(r'^- ', content_block) or re.match(r'^\d+\. ', content_block):
                    formatted_day_sections.append(f'\n\n**{display_title}:**\n{content_block}')
                else:
                    formatted_day_sections.append(f'\n\n**{display_title}:** {content_block}')
            elif display_title: 
                formatted_day_sections.append(f'\n\n**{display_title}:**')


        day_text_final = "\n".join(formatted_day_sections)

        # Это должно быть после всех остальных форматирований, но перед escape_markdown_v2
        day_text_final = re.sub(r'(#\w+)', r'_\1_', day_text_final) 
        
        # Нормализация абзацев (замена одиночных \n на \n\n)
        day_text_final = re.sub(r'([^\n])\n(?!\n)', r'\1\n\n', day_text_final)
        day_text_final = re.sub(r'\n{3,}', '\n\n', day_text_final) 

        formatted_output.append(day_text_final)
        
    return "\n\n— — —\n\n".join(formatted_output)