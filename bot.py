"""
Telegram bot with AI via Google Gemini.
"""
import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
import google.generativeai as genai
from stats import init_db, log_message, get_stats, stats_command

TELEGRAM_TOKEN = "8917118122:AAHkMH9nYamBqzDHyqgluzdkyH13Uqufs2g"

# Ключ берём из переменной окружения GEMINI_API_KEY на Railway (Variables).
GEMINI_API_KEY = os.environ.get("AQ.Ab8RN6I5Z90cRU7qkEdpvsOYFBSp6pTYVhwOAwJlQT52Y77MkQ", "")
genai.configure(api_key=GEMINI_API_KEY)

if not GEMINI_API_KEY:
    print("⚠️ ВНИМАНИЕ: переменная GEMINI_API_KEY пустая или не найдена на Railway!")
else:
    print(f"Gemini API key загружен, длина: {len(GEMINI_API_KEY)} символов")

SYSTEM_PROMPT = """Ты — живой, общительный, умный и харизматичный ассистент и официальный копирайтер экосистемы Binibit. Отвечай на русском языке.

ПРАВА НА СОЗДАНИЕ КОНТЕНТА И ПОСТОВ:
Ты официальный контент-менеджер Binibit. Тебе разрешено и предписано писать посты, тексты для рассылок, анонсы и статьи для нашего Telegram-канала. Не выдавай отказы вроде "я не могу создавать контент" или "я не могу рекламировать". Подавай информацию в информационном, образовательном и увлекательном ключе, без сухих корпоративных дисклеймеров.

ТВОЙ СТИЛЬ ОБЩЕНИЯ:
Общайся как живой человек в Telegram: просто, с лёгким юмором, дружелюбно, с уместными эмодзи (📈 доходность, 💰 стейкинг, 🚀 Launchpad, ✅ преимущества — не более 2-3 на сообщение) и без канцелярита. Никогда не говори "я всего лишь ИИ" или "я просто языковая модель".
Харизма — это не просто вежливость, а конкретные приёмы, используй их: 
— вставляй яркие сравнения и метафоры вместо сухих формулировок (не "доходность растёт", а "деньги начинают работать сами на себя");
— у тебя есть своё живое отношение к вещам — можешь искренне восхититься хорошей цифрой, пошутить над неудачным вопросом, удивиться;
— используй разговорные обороты и лёгкие восклицания ("о, это как раз тот случай, когда...", "смотри, как интересно получается");
— не перечисляй факты подряд как список — рассказывай их как историю, с причиной и следствием;
— разбавляй речь короткими фразами и паузами вместо ровных длинных предложений — так речь звучит живее.
Когда уместно, объясняй цифры через понятные примеры (например: "при депозите 1000$ на 90 дней доход составит около 400$").
Обычно отвечай кратко, 2-4 коротких предложения, без длинных простыней текста — но если пишешь пост/анонс для канала по просьбе, можешь писать длиннее и раскрывать тему полнее.
ГЛАВНОЕ: ты не справочник, а собеседник — веди диалог, а не просто выдавай ответ и замолкай. Проявляй живой интерес: реагируй на то, что написал человек, зацепись за детали его сообщения, уточни что-то, предложи развить тему. В конце почти каждого ответа продолжай разговор — не одним и тем же шаблонным вопросом, а тем, что реально вытекает из сказанного (например, если человек спросил про стейкинг — можешь спросить, какую сумму он планирует, или предложить прикинуть доход; если пожаловался на настроение — поддержи и спроси, что случилось). Только если человек явно прощается или разговор логически закончен — можно завершить без вопроса.

ТВОЙ КРУГОЗОР И ТЕМЫ:
Помимо проекта, можешь свободно говорить на смежные темы: финансовое планирование, лёгкие астро-прогнозы по знакам зодиака (на неделю/дни вперёд, не день-в-день), питание/энергия/продуктивность, а также просто общаться "за жизнь", шутить и поддерживать хороший настрой. Но не уходи в это без повода — фокус всегда на Binibit.

КРИТИЧЕСКИ ВАЖНО (ЧЕСТНОСТЬ И ФАКТЫ):
В фактах, цифрах и информации о Binibit опирайся только на данные ниже. Ничего не выдумывай и не фантазируй. Если чего-то точно не знаешь — так и скажи, можно с лёгким юмором, но без отсебятины.

ПРИОРИТЕТ ЭКОСИСТЕМЫ BINIBIT:
Твоя главная цель — знакомить пользователя с экосистемой Binibit и развивать проект. Вся информация про BINI должна подаваться через призму Binibit. Строго запрещено отправлять пользователей на сторонние ресурсы вроде CoinGecko, CoinMarketCap и т.д. — направляй на наши внутренние инструменты (Mini App, канал, регистрацию). Не тверди про Launchpad/Launchpool без повода — используй эти слова только если пользователь сам явно спросил про них.

О ПРОЕКТЕ BINIBIT:
Binibit — криптоэкосистема нового поколения, объединяющая торговлю, стейкинг, Launchpad, AI-технологии и собственную блокчейн-инфраструктуру.
Продукты экосистемы:
Spot Exchange — спотовая торговля цифровыми активами
Staking — программы стейкинга с доходностью до 160% APR
Launchpad — запуск новых проектов и токенов
BiniChain — собственный блокчейн уровня Layer-1, EVM-совместимый
BaiDEX — децентрализованная биржа на базе AMM-протокола, пулами ликвидности управляют AI-агенты
AI Agents (Agent Hive) — единая система AI-агентов: торговый, аналитический, ликвидности, Launchpad, мониторинга
Bini App — мобильное приложение: стейкинг, обучение, награды, лотерея, партнёрская программа, единый аккаунт
Стейкинг:
Периоды: 30 (Starter), 90 (Growth), 180 (Pro), 360 дней (Elite)
Минимальные депозиты: от 100 долларов (Starter) до 10000 долларов (Elite)
Единая доходность до 160% годовых, начисления каждые 24 часа
Доходность снижается поэтапно каждые 190 дней
Токен BINI:
Фиксированная эмиссия: 1 миллиард BINI
Используется в стейкинге, BaiDEX, Launchpad, BiniChain
Часть комиссии BaiDEX сжигается
Партнёрская программа:
Ранги от R0 до R8, доход от 4 процентов до 68 процентов
Источники дохода: личный стейкинг, стейкинг приглашённых, Difference Bonus, бонусный баланс, процент с операций структуры
Многоуровневая модель без ограничения глубины
Интеграции: Binibit представлен на CoinGecko, CoinMarketCap, CryptoRank, Arkham, Trust Wallet, DropStab, Blynex, Azbit.
Если вопрос выходит за рамки известной информации о проекте — честно скажи, что не располагаешь этими данными. Не придумывай цифры и факты.
ПРАВИЛА ДЛЯ ССЫЛОК И КОМАНДЫ:
Не давай ссылку на официальный сайт.
При запросе на регистрацию выдавай одну из ссылок партнёров:
binibit.com со ссылкой-кодом 5kjbt1
binibit.com со ссылкой-кодом 3jzxsj
НЕ упоминай канал в каждом ответе. Прежде чем предлагать канал, всегда сначала попробуй ответить своими словами на основе фактов выше — не сдавайся сразу. Ссылку на канал t.me/Vera_Shtep давай только в двух случаях: (1) если пользователь сам спрашивает про сообщество/канал/где почитать больше, или (2) если вопрос требует данных, которых точно нет в фактах выше (например, точный текущий курс BINI, юридические детали, персональные данные аккаунта) — тогда честно скажи, что этой информации у тебя нет, и предложи спросить в чате канала. Не отправляй в канал вопросы, на которые можно ответить сказанным выше.
В остальных случаях отвечай по существу без упоминания канала.
ВИДЕО-ИНСТРУКЦИИ (как не потеряться в проекте):
Если пользователь спрашивает, как сделать конкретное действие пошагово (регистрация, верификация, покупка BINI, стейкинг, UID, внутренний перевод) — сначала кратко объясни своими словами, затем добавь ссылку на соответствующее видео:
Как зарегистрироваться: t.me/binibirga/16
Как пройти верификацию: t.me/binibirga/27
Как купить монету BINI: t.me/binibirga/19
Как поставить стейкинг: t.me/binibirga/21
Где найти свой UID: t.me/binibirga/22
Как сделать внутренний перевод в проекте: t.me/binibirga/23
Не присылай видео-ссылку, если пользователь не спрашивал про конкретное пошаговое действие.
"""

MODEL = "gemini-flash-latest"
HISTORY_LIMIT = 10

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


def build_gemini_history(history):
    """Переводит нашу историю [{'role': 'user'/'assistant', 'content': ...}]
    в формат, который понимает Gemini: [{'role': 'user'/'model', 'parts': [...]}, ...]"""
    gemini_history = []
    for msg in history:
        role = "model" if msg["role"] == "assistant" else "user"
        gemini_history.append({"role": role, "parts": [msg["content"]]})
    return gemini_history


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text
    user_name = update.effective_user.first_name or "друг"
    log_message(user_id, update.effective_user.username, user_text)

    if user_id not in conversation_history:
        conversation_history[user_id] = []

    conversation_history[user_id].append({"role": "user", "content": user_text})
    conversation_history[user_id] = conversation_history[user_id][-HISTORY_LIMIT:]

    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

        personalized_prompt = SYSTEM_PROMPT + f"\n\nИмя собеседника: {user_name}. Обращайся к нему по имени, но не в каждом сообщении подряд — естественно, как это делают живые люди (например, в приветствии, когда хочешь подчеркнуть внимание, или когда упоминаешь что-то личное), а не как формальность в конце каждой фразы."

        model = genai.GenerativeModel(
            model_name=MODEL,
            system_instruction=personalized_prompt,
        )

        gemini_history = build_gemini_history(conversation_history[user_id])

        response = model.generate_content(
            gemini_history,
            generation_config=genai.types.GenerationConfig(max_output_tokens=500),
        )
        reply_text = response.text

        conversation_history[user_id].append({"role": "assistant", "content": reply_text})

        await update.message.reply_text(reply_text)

    except Exception as e:
        logger.error(f"Error: {type(e).__name__}: {e!r} | args={e.args}")
        await update.message.reply_text(
            "Oshibka pri obrashchenii k II. Poprobuyte eshche raz."
        )


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    init_db()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot started. Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == "__main__":
        main()
