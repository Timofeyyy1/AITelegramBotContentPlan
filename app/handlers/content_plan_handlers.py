import os
import asyncio
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from app.utils.markdown_utils import escape_markdown_v2 as escape_markdown 
from app.utils.message_utils import split_text

# Импорты из других модулей
from app.utils.prompt_templates import CONTENT_PLAN_PROMPT
from app.database.requests import save_content_plan_answers
from app.handlers.general_handlers import router as general_router
from app.keyboards.main_kb import get_main_keyboard
from app.ai_generate import generate



router = Router()

# FSM для создания контент-плана
class FSMContentPlan(StatesGroup):
    topic_audience = State()
    goal = State()
    frequency_format = State()
    usp = State()
    examples = State()
    content_tone = State()
    specific_topics = State()

QUESTIONS = [
    "Какая тематика вашего канала и целевая аудитория?\n\n"
    "Пример:\n"
    "✅ Канал про искусственный интеллект для начинающих предпринимателей и студентов технических специальностей.",


    "Какие цели вы хотите достичь с помощью канала?\n\n"
    "Пример:\n"
    "✅ Повысить вовлечённость подписчиков и обучить их базовым навыкам работы с ИИ.",


    "Как часто будете публиковать посты и какие форматы контента предпочитаете?\n\n"
    "Пример:\n"
    "✅ Публиковать 4 раза в неделю: текстовые посты, видеообзоры и карточки с фактами.",


    "Что делает ваш канал уникальным? (УТП)\n\n"
    "Пример:\n"
    "✅ Мы рассказываем о сложных темах простым языком и показываем реальные кейсы применения ИИ.",


    "Есть ли у вас примеры каналов, которыми вдохновляетесь?\n\n"
    "Пример:\n"
    "✅ @ai_news, @future_of_ai",


    "Хотите ли вы, чтобы контент был более информативным или развлекательным?\n\n"
    "Пример:\n"
    "✅ Больше информативным, но с элементами юмора.",


    "Есть ли конкретные темы или направления, которые обязательно должны быть в плане?\n\n"
    "Пример:\n"
    "✅ Посты про этику ИИ, его влияние на рынок труда и практические гайды.",
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
async def ask_examples(message: Message, state: FSMContext):
    await state.update_data(usp=message.text)
    await state.set_state(FSMContentPlan.examples)
    await message.answer(QUESTIONS[4])

@router.message(FSMContentPlan.examples)
async def ask_content_tone(message: Message, state: FSMContext):
    await state.update_data(examples=message.text)
    await state.set_state(FSMContentPlan.content_tone)
    await message.answer(QUESTIONS[5])

@router.message(FSMContentPlan.content_tone)
async def ask_specific_topics(message: Message, state: FSMContext):
    await state.update_data(content_tone=message.text)
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
    prompt = template.render(**data)

    result = await generate(prompt) # generate() теперь возвращает полностью готовый к отправке текст

    parts = split_text(result, 4096) # Используем обновленный split_text

    for i, part in enumerate(parts):
        try:
            logging.info(f"Attempting to send part {i+1}/{len(parts)} (length: {len(part)} bytes).")
            logging.debug(f"Part content:\n---\n{part}\n---") 

            await message.answer(part, parse_mode="MarkdownV2")
        except Exception as e:
            logging.error(f"Telegram API Error sending part {i+1}: {e}", exc_info=True)
            logging.error(f"Problematic part content (full):\n---\n{part}\n---") # Логируем всю часть, которая вызвала ошибку
            await message.answer("Произошла ошибка при отправке части контент-плана. Сообщите разработчику и попробуйте позже.")
            raise 

    await message.answer("Настройки плана:", reply_markup=get_main_keyboard())
    await state.clear()
    