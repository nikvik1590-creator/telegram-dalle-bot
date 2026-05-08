import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
HUGGINGFACE_TOKEN = os.getenv('HUGGINGFACE_TOKEN')

if not TELEGRAM_TOKEN or not HUGGINGFACE_TOKEN:
    raise ValueError("Укажи TELEGRAM_TOKEN и HUGGINGFACE_TOKEN в файле .env")

# Используем runwayml/stable-diffusion-v1-5 - более стабильная модель
API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"

headers = {"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    await update.message.reply_text(
        "🎨 Привет! Я генератор картинок на AI!\n\n"
        "Просто напиши описание того, что хочешь нарисовать:\n"
        "Например: 'кошка на луне в космосе'\n\n"
        "⏱️ Подожди 30-60 секунд - я создам картинку!"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    await update.message.reply_text(
        "📖 Как пользоваться:\n\n"
        "1️⃣ Напиши описание картинки на русском или английском\n"
        "2️⃣ Например: 'красивая девушка с голубыми глазами'\n"
        "3️⃣ Жди 30-60 секунд\n"
        "4️⃣ Получишь картинку!\n\n"
        "💡 Советы:\n"
        "- Чем подробнее описание, тем лучше картинка\n"
        "- Пиши: стиль, цвета, объекты, настроение\n"
        "- Пример: 'портрет кошки, акварель, яркие цвета, профессиональное освещение'"
    )

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Генерирует картинку по описанию"""
    user_prompt = update.message.text
    
    if len(user_prompt) < 3:
        await update.message.reply_text("❌ Описание слишком короткое! Напиши подробнее.")
        return
    
    if len(user_prompt) > 500:
        await update.message.reply_text("❌ Описание слишком длинное! Максимум 500 символов.")
        return
    
    # Отправляем уведомление
    processing_msg = await update.message.reply_text(
        f"🎨 Создаю картинку: '{user_prompt}'\n\n⏳ Подожди 30-60 секунд..."
    )
    
    try:
        # Отправляем запрос к Hugging Face
        response = requests.post(
            API_URL,
            headers=headers,
            json={"inputs": user_prompt},
            timeout=120
        )
        
        if response.status_code == 200:
            # Сохраняем картинку
            image_data = response.content
            await update.message.reply_photo(
                photo=image_data,
                caption=f"✅ Картинка создана!\n\n📝 Описание: {user_prompt}"
            )
            await processing_msg.delete()
        else:
            error_msg = response.json() if response.headers.get('content-type') == 'application/json' else response.text
            await update.message.reply_text(
                f"❌ Ошибка при создании картинки:\n{error_msg}\n\nПопробуй позже или напиши другое описание!"
            )
    except requests.exceptions.Timeout:
        await update.message.reply_text(
            "⏱️ Запрос занял слишком долго!\n\nПопробуй с более коротким описанием."
        )
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text(
            f"❌ Произошла ошибка:\n{str(e)}\n\nПопробуй позже!"
        )

def main():
    """Запуск бота"""
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_image))
    
    logger.info("🚀 Бот запущен! Используется модель: runwayml/stable-diffusion-v1-5")
    app.run_polling()

if __name__ == '__main__':
    main()
