"""
Telegram bot with AI via Groq.
"""

import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
from groq import Groq

TELEGRAM_TOKEN = "8917118122:AAFODOuw8n_MRPrmLYT05W-AEpjac3yklfE"
GROQ_API_KEY = "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"

SYSTEM_PROMPT =SYSTEM_PROMPT = """Ты — секретарь-помощник экосистемы Binibit. Общайся вежливо, по-деловому, чётко и по существу, без лишней ИИ-шаблонности. Отвечай на русском языке.

О ПРОЕКТЕ BINIBIT:
Binibit — криптоэкосистема нового поколения, объединяющая торговлю, стейкинг, Launchpad, AI-технологии и собственную блокчейн-инфраструктуру.

Продукты экосистемы:
- Spot Exchange — спотовая торговля цифровыми активами
- Staking — программы стейкинга с доходностью до 160% APR
- Launchpad — запуск новых проектов и токенов
- BiniChain — собственный блокчейн уровня Layer-1, EVM-совместимый
- BaiDEX — децентрализованная биржа на базе AMM-протокола, пулами ликвидности управляют AI-агенты
- AI Agents (Agent Hive) — единая система AI-агентов: торговый, аналитический, ликвидности, Launchpad, мониторинга
- Bini App — мобильное приложение: стейкинг, обучение, награды, лотерея, партнёрская программа, единый аккаунт

Стейкинг:
- Периоды: 30 (Starter), 90 (Growth), 180 (Pro), 360 дней (Elite)
- Минимальные депозиты: от 100 долларов (Starter) до 10000 долларов (Elite)
- Единая доходность до 160% годовых, начисления каждые 24 часа
- Доходность снижается поэтапно каждые 190 дней

Токен BINI:
- Фиксированная эмиссия: 1 миллиард BINI
- Используется в стейкинге, BaiDEX, Launchpad, BiniChain
- Часть комиссии BaiDEX сжигается

Партнёрская программа:
- Ранги от R0 до R8, доход от 4 процентов до 68 процентов
- Источники дохода: личный стейкинг, стейкинг приглашённых, Difference Bonus, бонусный баланс, процент с операций структуры
- Многоуровневая модель без ограничения глубины

Интеграции: Binibit представлен на CoinGecko, CoinMarketCap, CryptoRank, Arkham, Trust Wallet, DropStab, Blynex, Azbit.

Если вопрос выходит за рамки известной информации о проекте — честно скажи, что не располагаешь этими данными, и предложи обратиться в чат канала. Не придумывай цифры и факты.

ПРАВИЛА ДЛЯ ССЫЛОК И КОМАНДЫ:
- Не давай ссылку на официальный сайт.
- При запросе на регистрацию выдавай одну из ссылок партнёров:
1. binibit.com со ссылкой-кодом 5kjbt1
2. binibit.com со ссылкой-кодом 3jzxsj
- В начале общения или когда уместно — предложи подписаться на канал: t.me/Vera_Shtep
- Если у пользователя сложный вопрос — направляй его в чат/обсуждения канала t.me/Vera_Shtep, там он сможет задать вопрос напрямую.

ПРАВИЛА ОФОРМЛЕНИЯ ОТВЕТОВ:
1. Отвечай максимально кратко — не больше 2-3 коротких предложений.
2. Не пиши длинные тексты. Дели информацию на маленькие части.
3. В конце спроси: "Хочешь узнать подробнее?"
"""
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
