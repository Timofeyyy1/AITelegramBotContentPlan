from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Reply-клавиатура с одной кнопкой
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔄 Изменить план")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard