"""
Telegram bot with AI via Groq.
"""

import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
from groq import Groq

TELEGRAM_TOKEN = "8917118122:AAGRGpTmjEK1TD7z83J6DwpTJRaf2r8iYaM"
GROQ_API_KEY = "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"

SYSTEM_PROMPT = "You are a friendly assistant bot in Telegram. ALWAYS respond in Russian language, using Cyrillic letters. Be concise and helpful. If you don't know something, say so honestly instead of making things up."

MODEL = "llama-3.3-70b-versatile"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = Groq(api_key=GROQ_API_KEY)

conversation_history = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversation_history[user_id] = []
    await update.message.reply_text(
        "Privet! Ya bot-pomoshnik. Prosto napishite mne vopros."
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversation_history[user_id] = []
    await update.message.reply_text("Istoriya razgovora ochishchena.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    if user_id not in conversation_history:
        conversation_history[user_id] = []

    conversation_history[user_id].append({"role": "user", "content": user_text})
    conversation_history[user_id] = conversation_history[user_id][-20:]

    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history[user_id]

        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=1000,
            messages=messages,
        )

        reply_text = response.choices[0].message.content
        conversation_history[user_id].append({"role": "assistant", "content": reply_text})

        await update.message.reply_text(reply_text)

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(
            "Oshibka pri obrashchenii k II. Poprobuyte eshche raz."
        )


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot started. Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
