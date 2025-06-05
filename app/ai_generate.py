import asyncio
import re
import logging
from openai import AsyncOpenAI
from app.utils.markdown_utils import escape_markdown_v2 
from app.utils.message_utils import split_text 
from config import AI_TOKEN

logger = logging.getLogger(__name__)

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=AI_TOKEN,
)

async def generate(prompt: str) -> str:
    try:
        completion = await client.chat.completions.create(
            model="google/gemini-2.5-flash-preview-05-20", 
            messages=[
                {"role": "user", "content": prompt}
            ],
            timeout=240,
            max_tokens=4000
        )

        if completion and completion.choices:
            logger.debug(f"Full Completion Object: {completion.model_dump_json(indent=2)}")

            if completion.choices[0].message and completion.choices[0].message.content:
                content = completion.choices[0].message.content
                logger.debug(f"Raw AI response (content extracted):\n---\n{content}\n---")

                first_day_match = re.search(r'^(?:.*?)(?=День \d+:\s*\w+)', content, flags=re.DOTALL | re.MULTILINE | re.IGNORECASE)
                if first_day_match:
                    content = content[first_day_match.start():].strip()
                    logger.debug(f"Content after aggressive initial cleanup (before clean_content):\n---\n{content}\n---")
                else:
                    logger.warning("Не удалось найти начало контент-плана (День X:) в ответе ИИ. Пробуем обработать весь контент.")
                    content = content.strip()

                content = clean_content(content)
                logger.debug(f"Content after clean_content:\n---\n{content}\n---")
                
                content = format_content_minimal(content)  # Calling minimal formatting function
                logger.debug(f"Content after format_content_minimal (Markdown assumed):\n---\n{content}\n---")

                final_content = escape_markdown_v2(content)
                logger.debug(f"Content after final MarkdownV2 escaping:\n---\n{final_content}\n---")

                return final_content.strip() if final_content.strip() else escape_markdown_v2("Модель не вернула содержание.")
            else:
                logger.error(f"Модель вернула пустой 'message.content' или 'message' отсутствует. Completion: {completion.model_dump_json(indent=2)}")
                return escape_markdown_v2("Модель не вернула содержание или вернула пустой ответ.")
        else:
            logger.error(f"Completion object has no choices or choices list is empty. Completion: {completion.model_dump_json(indent=2)}")
            return escape_markdown_v2("Модель не вернула варианты ответов.")
    except Exception as e:
        logger.error(f"Ошибка при работе с ИИ: {e}", exc_info=True)
        error_message = f"Произошла ошибка при генерации\\. Детали: `{escape_markdown_v2(str(e))}`\\. Пожалуйста, попробуйте еще раз\\."
        return error_message



def clean_content(content: str) -> str:

    content = re.sub(r'\\+', '', content) # Удалить все последовательности бэкслешей

    content = re.sub(r'(\n\n|^)(—{3,}|-{3,})(\n\n|$)', '\n\n', content)

    content = re.sub(r'(?<!\S)—{1}(?!\S)', '', content) 

    # Удаляем двойные двоеточия (::)
    content = re.sub(r'::+', ':', content)

    # Удаляем удвоенные заголовки секций (например, "Заголовок: Заголовок:")
    content = re.sub(r'(\b\w+\s*:\s*)\1', r'\1', content, flags=re.IGNORECASE)
    # Также убираем " (ста):" если оно идет после "Призыв к действию"
    content = re.sub(r'Призыв к действию \(СТА\)\s*\(\w+\):\s*', r'Призыв к действию (СТА): ', content, flags=re.IGNORECASE)


    # Нормализация пробелов и переносов строк
    content = re.sub(r'[ \t]+', ' ', content).strip() 
    content = re.sub(r'\n{3,}', '\n\n', content) 
    content = re.sub(r' \n', '\n', content) 
    content = re.sub(r'\n ', '\n', content) 

    return content.strip()


# НОВАЯ/ОБНОВЛЕННАЯ ФУНКЦИЯ ФОРМАТИРОВАНИЯ
def format_content_minimal(content: str) -> str:
    content = re.sub(r'(\n\n\s*—{3,}\s*\n\n)|(\n\n\s*-{3,}\s*\n\n)', '\n\n— — —\n\n', content)
    
    # Убедимся, что нет более одного разделителя подряд в конце.
    content = re.sub(r'(\n\n— — —\n\n){2,}$', '\n\n— — —\n\n', content)

    # Нормализация абзацев (для избежания слишком частых \n)
    # Если строка не заканчивается \n и за ней следует не \n (т.е. одиночный \n), добавляем вторую \n
    content = re.sub(r'([^\n])\n(?!\n)', r'\1\n\n', content)
    # Убираем больше двух \n подряд
    content = re.sub(r'\n{3,}', '\n\n', content) 

    content = re.sub(r'(#\w+):', r'_\1_:', content)
    content = re.sub(r'(?<![#_])(#\w+)(?![_#])', r'_\1_', content)
    
    return content.strip()
