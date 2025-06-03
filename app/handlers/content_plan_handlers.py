import logging
import os
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from app.utils.markdown_utils import escape_markdown_v2 as escape_markdown
from app.utils.message_utils import split_text

# Импорты из других модулей
from app.utils.prompt_templates import CONTENT_PLAN_PROMPT, POST_GENERATION_PROMPT
from app.database.requests import save_content_plan_answers
# from app.handlers.general_handlers import router as general_router # Обычно не нужен прямой импорт роутера в том же приложении
from app.keyboards.main_kb import get_content_plan_actions_keyboard # Возвращена к простой клавиатуре
from app.ai_generate import generate
from app.utils.post_utils import parse_formatted_plan_for_post # Только парсинг первого дня


router = Router()

# FSM для создания контент-плана
class FSMContentPlan(StatesGroup):
    topic_audience = State()
    goal = State()
    frequency_format = State()
    usp = State()
    main_rubrics_topics = State()   # Было examples, теперь это
    content_style = State()         # Было content_tone, теперь это
    specific_topics = State()       # Смысл изменен, но название переменной то же

# Обновленный массив вопросов для FSM
QUESTIONS = [
    "Какая тематика вашего канала и целевая аудитория?\n\n"
    "Пример:\n"
    "✅ Канал о повседневной жизни, учебе, проектах и карьерных возможностях студентов кафедры информационных технологий и систем.",

    "Какие цели вы хотите достичь с помощью канала?\n\n"
    "Пример:\n"
    "✅ Информировать студентов о событиях, дедлайнах и возможностях. Мотивировать к активному участию в жизни кафедры и проектах.",

    "Как часто будете публиковать посты и какие форматы контента предпочитаете?\n\n"
    "Пример:\n"
    "✅ Публиковать 3 раза в неделю: технические статьи, обзоры и видеоуроки. Полезные карточки/гайды по учебе и карьере, интерьвью с выпускниками кафедры.",

    "В чем уникальность вашего канала по сравнению с другими в вашей нише? Что делает ваш контент особенным?\n\n"
    "Пример:\n"
    "✅ Мы предлагаем глубокий разбор учебных кейсов и реальных проектов ИТС кафедры, а также регулярно публикуем материалы, подготовленные преподавателями и студентами.",

    "Назовите 3-5 основных рубрик или тем, которые обязательно должны присутствовать в контент-плане.\n\n"
    "Пример:\n"
    "✅ 1) Новые технологии в ИТС. 2) Советы от старшекурсников (гайды по учебе, выбору специализации). 3) Новости кафедры/факультета (анонсы, дедлайны). 4) Кейс-стади из реальных проектов кафедры. 5) Обзор научных публикаций и конференций.",

    "Каким стилем должен обладать ваш контент?\n\n"
    "Пример:\n"
    "✅ Технический и доступный, с примерами из практики и акцентом на обучение.",

    "Помимо обозначенных основных рубрик, есть ли у вас конкретные, отдельные идеи для постов или особо важные узкие направления, которые обязательно должны быть включены в план?\n\n"
    "Пример:\n"
    "✅ Разбор проекта по автоматизации процессов на базе ИИ, выполненного студентами кафедры.\n"
    "✅ Узкое направление: Один день из жизни IT-разработчика (посещение офисов компаний, интервью со стажерами)\n"
    "✅ Анонс мероприятий и конференций, связанных с ИТС, в которых участвуют преподаватели и студенты."
]

@router.message(Command("content_plan"))
async def cmd_content_plan(message: Message, state: FSMContext):
    await state.set_state(FSMContentPlan.topic_audience)
    await message.answer(QUESTIONS[0])

# === Последовательная обработка состояний ===
@router.message(FSMContentPlan.topic_audience)
async def ask_goal(message: Message, state: FSMContext):
    await state.update_data(topic_audience=message.text)
    await state.set_state(FSMContentPlan.goal)
    await message.answer(QUESTIONS[1])

@router.message(FSMContentPlan.goal)
async def ask_frequency_format(message: Message, state: FSMContext):
    await state.update_data(goal=message.text)
    await state.set_state(FSMContentPlan.frequency_format)
    await message.answer(QUESTIONS[2])

@router.message(FSMContentPlan.frequency_format)
async def ask_usp(message: Message, state: FSMContext):
    await state.update_data(frequency_format=message.text)
    await state.set_state(FSMContentPlan.usp)
    await message.answer(QUESTIONS[3])

@router.message(FSMContentPlan.usp)
async def ask_main_rubrics_topics(message: Message, state: FSMContext):
    await state.update_data(usp=message.text)
    await state.set_state(FSMContentPlan.main_rubrics_topics)
    await message.answer(QUESTIONS[4])

@router.message(FSMContentPlan.main_rubrics_topics)
async def ask_content_style(message: Message, state: FSMContext):
    await state.update_data(main_rubrics_topics=message.text)
    await state.set_state(FSMContentPlan.content_style)
    await message.answer(QUESTIONS[5])

@router.message(FSMContentPlan.content_style)
async def ask_specific_topics(message: Message, state: FSMContext):
    await state.update_data(content_style=message.text)
    await state.set_state(FSMContentPlan.specific_topics)
    await message.answer(QUESTIONS[6])

@router.message(FSMContentPlan.specific_topics)
async def finish_content_plan(message: Message, state: FSMContext):
    data = await state.update_data(specific_topics=message.text)
    data["tg_id"] = message.from_user.id

    await save_content_plan_answers(data)
    
    await message.answer("⏳ Ожидайте ваш план генерируется...")

    from jinja2 import Template
    template = Template(CONTENT_PLAN_PROMPT)
    prompt = template.render(
        topic_audience=data['topic_audience'],
        goal=data['goal'],
        frequency_format=data['frequency_format'],
        usp=data['usp'],
        main_rubrics_topics=data['main_rubrics_topics'],
        content_style=data['content_style'],
        specific_topics=data['specific_topics']
    )

    generated_plan_text = await generate(prompt)

    # Сохраняем весь сгенерированный текст плана в FSMContext
    await state.update_data(last_generated_plan_text=generated_plan_text)
    await state.update_data(original_plan_data=data) # Сохраняем исходные данные пользователя для генерации поста

    parts = split_text(generated_plan_text, 4096)

    for i, part in enumerate(parts):
        try:
            # Повторно применяем escape_markdown к каждой части
            final_part_to_send = escape_markdown(part) 
            
            logging.info(f"Attempting to send part {i+1}/{len(parts)} (length: {len(final_part_to_send)} bytes).")
            logging.debug(f"Part content:\n---\n{final_part_to_send}\n---") 

            await message.answer(final_part_to_send, parse_mode="MarkdownV2")
        except Exception as e:
            logging.error(f"Telegram API Error sending part {i+1}: {e}", exc_info=True)
            logging.error(f"Problematic part content (full):\n---\n{final_part_to_send}\n---") 
            await message.answer("Произошла ошибка при отправке части контент-плана. Сообщите разработчику и попробуйте позже.")
            await state.clear() 
            return 

    await message.answer(
        "Контент-план готов! Хотите создать пример поста? 💻",
        reply_markup=get_content_plan_actions_keyboard() # Возвращена старая клавиатура
    )
    # НЕ ОЧИЩАЕМ state, пока пользователь не выберет действие (например, сгенерировать пост)
    # await state.clear()

# Хэндлер для кнопки "Создать пример поста" (возвращен к старому виду)
@router.callback_query(F.data == "generate_example_post")
async def handle_generate_example_post_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Генерирую пример поста...", show_alert=False) # Уведомление для пользователя
    
    user_data = await state.get_data()
    generated_plan_text = user_data.get("last_generated_plan_text")
    original_plan_data = user_data.get("original_plan_data")

    if not generated_plan_text or not original_plan_data:
        await callback.message.answer("Не могу найти сгенерированный контент-план или исходные данные. Пожалуйста, создайте его сначала.")
        await state.clear()
        return

    # Извлекаем данные для первого дня из сгенерированного плана
    day_1_data = parse_formatted_plan_for_post(generated_plan_text)

    if not day_1_data:
        await callback.message.answer("Не удалось извлечь данные для первого дня из контент-плана. Возможно, формат изменился.")
        await state.clear() # Очищаем состояние при ошибке парсинга
        return

    # Формируем промт для генерации поста
    from jinja2 import Template
    post_template = Template(POST_GENERATION_PROMPT)
    
    # Объединяем данные для поста (day_data) и исходные данные канала (original_plan_data)
    post_prompt_data = {
        **original_plan_data, # Все исходные данные канала
        "day_data": day_1_data # Детали конкретного дня
    }
    post_prompt = post_template.render(**post_prompt_data)

    await callback.message.answer("⏳ Генерирую пост...")

    # Генерируем пост (повторно используем функцию generate)
    generated_post_text = await generate(post_prompt)

    # Делим пост на части, если он слишком длинный
    post_parts = split_text(generated_post_text, 4096)

    for i, part in enumerate(post_parts):
        try:
            final_post_part_to_send = escape_markdown(part) 
            logging.info(f"Attempting to send post part {i+1}/{len(post_parts)} (length: {len(final_post_part_to_send)} bytes).")
            logging.debug(f"Post part content:\n---\n{final_post_part_to_send}\n---") 
            await callback.message.answer(final_post_part_to_send, parse_mode="MarkdownV2")
        except Exception as e:
            logging.error(f"Telegram API Error sending post part {i+1}: {e}", exc_info=True)
            logging.error(f"Problematic post part content (full):\n---\n{final_post_part_to_send}\n---")
            await callback.message.answer("Произошла ошибка при отправке части поста. Сообщите разработчику и попробуйте позже.")
            await state.clear() # Очищаем состояние при ошибке
            return

    await state.clear() # Очищаем состояние после успешной генерации поста
