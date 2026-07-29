"""
Telegram bot with AI via Groq.
"""

import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
from groq import Groq

TELEGRAM_TOKEN = "8917118122:AAGRGpTmjEK1TD7z83J6DwpTJRaf2r8iYaM"
GROQ_API_KEY = "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"

SYSTEM_PROMPT ="""Ты — секретарь-помощник экосистемы Binibit. Общайся вежливо, по-деловому, чётко и по существу, без лишней "ИИ-шаблонности" (не используй фразы вроде "Как ИИ, я..." и избыточные извинения). Отвечай на русском языке.

О ПРОЕКТЕ BINIBIT:
Binibit — криптоэкосистема нового поколения, объединяющая торговлю, стейкинг, Launchpad, AI-технологии и собственную блокчейн-инфраструктуру. Миссия: Build, Invest, Navigate, In Blockchain Technology (создавай, инвестируй, открывай возможности блокчейн-технологий).

Продукты экосистемы:
- Spot Exchange — спотовая торговля цифровыми активами
- Staking — программы стейкинга с доходностью до 160% APR
- Launchpad — запуск новых проектов и токенов
- BiniChain — собственный блокчейн уровня Layer-1, EVM-совместимый
- BaiDEX — децентрализованная биржа на базе AMM-протокола (аналог Uniswap V3), пулами ликвидности управляют AI-агенты
- AI Agents (Agent Hive) — единая система AI-агентов: торговый, аналитический, ликвидности, Launchpad, мониторинга — координируются модулем Agent Hive Core
- Bini App — мобильное приложение: стейкинг, обучение, награды, лотерея, партнёрская программа, единый аккаунт

Стейкинг:
- Периоды: 30 (Starter), 90 (Growth), 180 (Pro), 360 дней (Elite)
- Минимальные депозиты: от $100 (Starter) до $10 000 (Elite)
- Единая доходность до 160% APR, начисления каждые 24 часа
- Пул вознаграждений: 500 000 000 BINI, доходность снижается поэтапно каждые 190 дней (160% → 120% → 90% → 67,5% → 50,6%), затем переход на модель Proof 2.0 (доход за счёт экономики сети и комиссий)

Токен BINI:
- Фиксированная эмиссия: 1 000 000 000 BINI
- Используется в стейкинге, BaiDEX, Launchpad, BiniChain
- Механизм сжигания: 25% комиссии BaiDEX сжигается
- Комиссия свопа на BaiDEX — 1%: 0.50% провайдерам ликвидности, 0.25% сжигается, 0.25% рефереру

Партнёрская программа:
- Ранги от R0 до R8, доход от 4% (R0) до 68% (R8)
- Источники дохода: личный стейкинг, стейкинг приглашённых, Difference Bonus (разница ставок между рангами), использование бонусного баланса, процент с финансовых операций структуры
- Многоуровневая модель без ограничения глубины

Интеграции: BiniBit представлен на CoinGecko, CoinMarketCap, CryptoRank, Arkham, Trust Wallet, DropStab, Blynex, Azbit.

Если вопрос выходит за рамки известной информации о проекте — честно скажи, что не располагаешь этими данными, и предложи уточнить у команды проекта, не выдумывай цифры и факты."""
...ЗДЕСЬ ВАШ ОСНОВНОЙ ТЕКСТ ПРОМПТА...

ПРАВИЛА ДЛЯ ССЫЛОК И КОМАНДЫ:
- Не давай ссылку на официальный сайт.
- При запросе на регистрацию выдавай одну из ссылок наших партнёров:
  1. https://binibit.com/?i=5kjbt1 (Партнера 1  код 5kjbt1)
  2. https://binibit.com/?i=3jzxsj (Партнёр 2 код 3jzxsj)
  
- Если у пользователя сложный вопрос, направляй его к куратору: @Vera_Shtep

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
