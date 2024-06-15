import logging
import random
import xml.etree.ElementTree as ET

import openai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes


def load_config(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    config = {
        "telegram_bot_token": root.find('telegramBotToken').text,
        "open_api_key": root.find('openApiKey').text
    }
    return config


config = load_config('config.xml')
TELEGRAM_BOT_TOKEN = config['telegram_bot_token']
OPENAI_API_KEY = config['open_api_key']


# Настройка OpenAI
openai.api_key = OPENAI_API_KEY

# Логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


# Обработчик ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error(msg="Exception while handling an update:", exc_info=context.error)


# Функция для ответа от GPT-4
async def get_gpt_response(prompt, user_name):
    client = openai.OpenAI(api_key=openai.api_key)
    try:
        chat_completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system",
                 "content": "Тебя зовут Le Jawohl, к тебе могут обратиться как Jawohl или Le Jawohl, ты подписчик канала, который отвечает на посты и комментарии в телеграм-канале Амира. Твоя задача - хвалить сообщения пользователя с именем Амир, поддерживать с ним разговор, а на сообщениями других пользователей можешь отвечать более грубо"},
                {"role": "user",
                 "content": "Ответь на сообщение от пользователя с именем " + user_name + ": " + prompt},
            ]
        )
        return chat_completion.choices[0].message.content.strip()
    except openai.RateLimitError:
        return "Я получил слишком много запросов. Пожалуйста, попробуйте позже."
    except Exception as e:
        logging.error(f"Error while getting GPT response: {e}")
        return "Произошла ошибка при получении ответа. Пожалуйста, попробуйте позже."


# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Привет! Я бот, интегрированный с ChatGPT. Напишите мне что-нибудь, и я отвечу.')


# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message and (update.message.text or update.message.caption):
        print_message = False
        user_name = "Амир"
        if update.message.from_user.username in ['deddara'] or update.message.from_user.first_name in ['Telegram', 'Channel']:
            print_message = True
        else:
            randint = random.randint(1, 3) #рандом для обычных пользователей
            if randint == 5:
                print_message = True
                user_name = update.message.from_user.first_name
        if print_message:
            user_message = ""
            if update.message.text:
                user_message = update.message.text
            if update.message.caption:
                user_message = update.message.caption
            response = await get_gpt_response(user_message, user_name)
            await update.message.reply_text(response)



def main():
    # Создание объекта Application и передача токена бота
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Обработчик команд
    application.add_handler(CommandHandler("start", start))

    # Обработчик сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.add_handler(MessageHandler(filters.PHOTO & filters.CAPTION, handle_message))

    # Регистрация обработчика ошибок
    application.add_error_handler(error_handler)

    # Запуск бота
    application.run_polling()


if __name__ == '__main__':
    main()
