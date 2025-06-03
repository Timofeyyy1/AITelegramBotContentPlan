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
            model="google/gemini-2.5-flash-preview-05-20",  # Обновленная модель
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

                # --- ЛОГИКА УДАЛЕНИЯ ЭХО ПРОМТА И "ВСТУПЛЕНИЯ" ОТ LLM ---
                # Ищем начало контент-плана (например, "День 1:")
                # Удаляем все, что идет до первого такого вхождения.
                first_day_match = re.search(r'^(?:.*?)(?=День \d+:\s*\w+)', content, flags=re.DOTALL | re.MULTILINE | re.IGNORECASE)
                if first_day_match:
                    content = content[first_day_match.start():].strip()
                    logger.debug(f"Content after aggressive initial cleanup (before clean_content):\n---\n{content}\n---")
                else:
                    logger.warning("Не удалось найти начало контент-плана (День X:) в ответе ИИ. Пробуем обработать весь контент.")
                    content = content.strip()

                # 1. Очистка текста от лишних символов (ТОЛЬКО шум).
                content = clean_content(content)
                logger.debug(f"Content after clean_content:\n---\n{content}\n---")
                
                # 2. Форматирование текста (ТЕПЕРЬ ПРОЩЕ, ТАК КАК ИИ ГЕНЕРИРУЕТ MARKDOWN)
                # Эта функция будет выполнять минимальную доформатировку/нормализацию.
                content = format_content_minimal(content)  # Calling minimal formatting function
                logger.debug(f"Content after format_content_minimal (Markdown assumed):\n---\n{content}\n---")

                # 3. Экранирование MarkdownV2 (только здесь, только один раз, пропускает ** и _ )
                # Теперь мы используем улучшенную escape_markdown_v2.
                final_content = escape_markdown_v2(content)
                logger.debug(f"Content after final MarkdownV2 escaping:\n---\n{final_content}\n---")

                # Возвращаем "Модель не вернула содержание.", если content был пуст после всех обработок
                # или если final_content оказался пустым.
                return final_content.strip() if final_content.strip() else escape_markdown_v2("Модель не вернула содержание.")
            else:
                logger.error(f"Модель вернула пустой 'message.content' или 'message' отсутствует. Completion: {completion.model_dump_json(indent=2)}")
                return escape_markdown_v2("Модель не вернула содержание или вернула пустой ответ.")
        else:
            logger.error(f"Completion object has no choices or choices list is empty. Completion: {completion.model_dump_json(indent=2)}")
            return escape_markdown_v2("Модель не вернула варианты ответов.")
    except Exception as e:
        logger.error(f"Ошибка при работе с ИИ: {e}", exc_info=True)
        # Убедимся, что сообщение об ошибке тоже экранируется
        error_message = f"Произошла ошибка при генерации\\. Детали: `{escape_markdown_v2(str(e))}`\\. Пожалуйста, попробуйте еще раз\\."
        return error_message



def clean_content(content: str) -> str:
    """
    Очищает текст от лишних символов (бэкслешей, избыточных пробелов/переносов строк,
    возможных лишних разделителей).
    Ожидает сырой текст от ИИ.
    """
    content = re.sub(r'\\+', '', content) # Удалить все последовательности бэкслешей

    # Удаляем потенциальные лишние разделители (---), которые могут быть в начале или конце блоков,
    # так как теперь ИИ сам их генерирует.
    content = re.sub(r'(\n\n|^)(—{3,}|-{3,})(\n\n|$)', '\n\n', content)
    # Удаляет одиночные дефисы, если они не являются частью слова (например, "— мы выберем")
    content = re.sub(r'(?<!\S)—{1}(?!\S)', '', content) 

    # Удаляем двойные двоеточия (::)
    content = re.sub(r'::+', ':', content)

    # Удаляем удвоенные заголовки секций (например, "Заголовок: Заголовок:")
    # Ищем шаблон "слово: слово:" и заменяем на "слово:"
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
    """
    Минимальное форматирование текста.
    Предполагается, что ИИ уже сгенерировал большую часть Markdown.
    Эта функция занимается лишь нормализацией разделителей и хэштегов.
    """
    
    # Нормализация разделителей между днями.
    # ИИ может генерировать "---" или "— — —". Приводим к одному формату.
    content = re.sub(r'(\n\n\s*—{3,}\s*\n\n)|(\n\n\s*-{3,}\s*\n\n)', '\n\n— — —\n\n', content)
    
    # Убедимся, что нет более одного разделителя подряд в конце.
    content = re.sub(r'(\n\n— — —\n\n){2,}$', '\n\n— — —\n\n', content)

    # Нормализация абзацев (для избежания слишком частых \n)
    # Если строка не заканчивается \n и за ней следует не \n (т.е. одиночный \n), добавляем вторую \n
    content = re.sub(r'([^\n])\n(?!\n)', r'\1\n\n', content)
    # Убираем больше двух \n подряд
    content = re.sub(r'\n{3,}', '\n\n', content) 

    # Коррекция хэштегов: если ИИ сгенерировал #Хэштег, но не обернул в курсив,
    # мы это сделаем здесь, убедившись, что #Хэштег: не станет _#Хэштег_:
    # 1. Сначала обрабатываем #Хэштег: (оставляем двоеточие снаружи курсива)
    content = re.sub(r'(#\w+):', r'_\1_:', content)
    # 2. Затем обрабатываем все остальные #Хэштеги, которые не являются частью слова и не обернуты
    # (поиск #Хэштег, не окруженного другими символами или уже курсивом)
    content = re.sub(r'(?<![#_])(#\w+)(?![_#])', r'_\1_', content)
    
    return content.strip()
