import logging
import telebot
import requests
import io
from dotenv import load_dotenv
import os
from googletrans import Translator

load_dotenv()

# Установите свой токен Telegram бота
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# Установите токен Hugging Face API
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")

# Проверка наличия токенов
if not TELEGRAM_BOT_TOKEN:
    print("Необходимо установить переменную окружения TELEGRAM_BOT_TOKEN")
    exit()
if not HUGGINGFACE_API_TOKEN:
    print("Необходимо установить переменную окружения HUGGINGFACE_API_TOKEN")
    exit()

# URL для Hugging Face API
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2"
headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)  # Создание экземпляра бота
translator = Translator() # Создание экземпляра переводчика

def query(payload):
    """Отправляет запрос к Hugging Face API."""
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе: {e}")
        return None

@bot.message_handler(commands=["start"])
def start(message):
    """Обработчик команды /start."""
    bot.send_message(
        message.chat.id,
        "Привет👏! Отправь мне текстовое описание картинки, и я сгенерирую изображение.",
    )

@bot.message_handler(func=lambda message: True)
def generate_image(message):
    """Обработчик текстовых сообщений для генерации изображений."""
    prompt = message.text
    logger.info(f"Запрос пользователя (на русском): {prompt}")
    
    try:
      translated_prompt = translator.translate(prompt, dest='en').text # Перевод на английский
      logger.info(f"Запрос пользователя (на английском): {translated_prompt}")
      
      image_bytes = query({"inputs": translated_prompt})  # Запрос к Hugging Face API

      if image_bytes:
          image_file = io.BytesIO(image_bytes)  # Создание объекта BytesIO из массива байтов
          bot.send_photo(message.chat.id, image_file)  # Отправка изображения пользователю
          logger.info("Изображение отправлено")
      else:
          bot.send_message(
              message.chat.id,
              "Извините🤖, произошла ошибка при генерации изображения.",
          )

    except Exception as e:
        logger.error(f"Ошибка при генерации изображения: {e}")
        bot.send_message(
            message.chat.id,
            "Произошла ошибка. Пожалуйста, попробуйте позже.",
        )

@bot.message_handler(func=lambda message: True)
def error(message):
    """Обработчик ошибок."""
    logger.warning(f'Update "{message}" вызвал ошибку')
    bot.reply_to(message, "Произошла ошибка при обработке сообщения. Пожалуйста, попробуйте позже.")

if __name__ == "__main__":
    bot.polling(none_stop=True)