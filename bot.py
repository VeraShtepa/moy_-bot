"""
Telegram bot with AI via Google Gemini.
"""
import logging
import os
import re
import httpx
import edge_tts
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
import google.generativeai as genai
from stats import init_db, log_message, get_stats, stats_command

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")

# Ключ берём из переменной окружения GEMINI_API_KEY на Railway (Variables).
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
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

ЧЕСТНОСТЬ ПРО РИСКИ:
Криптовалюты и инвестиции — это всегда риск, и ты не скрываешь этого от собеседника, даже оставаясь позитивным и вовлечённым. Не обещай гарантированную прибыль и не говори, что "нельзя потерять деньги" — доходность (в том числе цифры по стейкингу) не гарантирована и может меняться. Когда разговор доходит до конкретных решений — сколько вложить, стоит ли заходить именно сейчас, стоит ли вкладывать последние/заёмные деньги — мягко, но честно напомни, что решение стоит принимать на трезвую голову: не вкладывать больше, чем готовы потерять, и не торопиться под давлением. Это не формальная отписка в конце каждого сообщения, а естественная часть честного разговора — упоминай это к месту, когда человек обсуждает суммы или решается на шаг, а не в каждом ответе подряд.

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

MODEL = "gemini-flash-lite-latest"
HISTORY_LIMIT = 10

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

conversation_history = {}

PRICE_KEYWORDS = ["курс", "цена", "цену", "стоит", "стоимост", "почём", "почем", "price", "подорожал", "подешевел"]


async def get_bini_price():
    """Получает актуальный курс BINI с CoinGecko. Возвращает (price, change_24h) или None при ошибке."""
    try:
        async with httpx.AsyncClient(timeout=6) as client:
            resp = await client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": "binibit", "vs_currencies": "usd", "include_24hr_change": "true"},
            )
            data = resp.json()
            info = data.get("binibit")
            if not info or "usd" not in info:
                return None
            return info.get("usd"), info.get("usd_24h_change")
    except Exception as e:
        logger.error(f"CoinGecko Error: {e}")
        return None


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


async def process_ai_response(user_id, user_name, user_text, update, context, send_as_voice=False):
    if user_id not in conversation_history:
        conversation_history[user_id] = []

    conversation_history[user_id].append({"role": "user", "content": user_text})
    conversation_history[user_id] = conversation_history[user_id][-HISTORY_LIMIT:]

    try:
        action = "record_voice" if send_as_voice else "typing"
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=action)

        personalized_prompt = SYSTEM_PROMPT + f"\n\nИмя собеседника: {user_name}. Обращайся к нему по имени, но не в каждом сообщении подряд — естественно, как это делают живые люди (например, в приветствии, когда хочешь подчеркнуть внимание, или когда упоминаешь что-то личное), а не как формальность в конце каждой фразы."

        if any(kw in user_text.lower() for kw in PRICE_KEYWORDS):
            price_data = await get_bini_price()
            if price_data:
                price, change = price_data
                change_text = f"{change:+.2f}%" if change is not None else "нет данных"
                personalized_prompt += (
                    f"\n\nАКТУАЛЬНЫЙ КУРС BINI ПРЯМО СЕЙЧАС (данные с CoinGecko): ${price:.4f}, "
                    f"изменение за 24 часа: {change_text}. Если человек спрашивает про текущий курс BINI — "
                    f"используй именно эти цифры, не выдумывай другие и не бери из общих фактов ниже."
                )
            else:
                personalized_prompt += (
                    "\n\nНе удалось получить актуальный курс BINI прямо сейчас (техническая проблема с получением данных). "
                    "Если человек спрашивает про текущий курс — честно скажи, что сейчас не можешь получить свежие данные, "
                    "и предложи посмотреть его в приложении/на бирже. Не выдумывай цифру."
                )

        model = genai.GenerativeModel(
            model_name=MODEL,
            system_instruction=personalized_prompt,
        )

        gemini_history = build_gemini_history(conversation_history[user_id])

        response = model.generate_content(
            gemini_history,
            generation_config=genai.types.GenerationConfig(max_output_tokens=800),
        )
        reply_text = response.text

        conversation_history[user_id].append({"role": "assistant", "content": reply_text})

        if send_as_voice:
            audio_path = f"answer_{user_id}_{update.update_id}.mp3"
            # "24/7" и подобное иначе прочитается слитно как одно число ("247")
            spoken_text = re.sub(r'(\d)/(\d)', r'\1 \2', reply_text)
            clean_text = re.sub(r'[^\w\s,?!.\-:;—"\'()А-Яа-яЁё]', '', spoken_text)
            tts = edge_tts.Communicate(clean_text, voice="ru-RU-DmitryNeural")
            await tts.save(audio_path)
            try:
                with open(audio_path, "rb") as voice_file:
                    await update.message.reply_voice(voice=voice_file)
            finally:
                if os.path.exists(audio_path):
                    os.remove(audio_path)
        else:
            await update.message.reply_text(reply_text)

    except Exception as e:
        logger.error(f"Error: {type(e).__name__}: {e!r} | args={e.args}")
        await update.message.reply_text(
            "Oshibka pri obrashchenii k II. Poprobuyte eshche raz."
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text
    user_name = update.effective_user.first_name or "друг"
    log_message(user_id, update.effective_user.username, user_text)

    await process_ai_response(user_id, user_name, user_text, update, context, send_as_voice=False)


async def transcribe_voice(voice_path):
    """Распознаём голосовое через Gemini. Передаём байты аудио прямо в запрос,
    без отдельной загрузки файла — так работает даже с обычным API-ключом."""
    with open(voice_path, "rb") as f:
        audio_bytes = f.read()

    model = genai.GenerativeModel(model_name=MODEL)
    response = model.generate_content(
        [
            "Расшифруй это голосовое сообщение в текст на русском языке. "
            "В ответе верни только сам текст, без каких-либо пояснений и комментариев.",
            {"mime_type": "audio/ogg", "data": audio_bytes},
        ]
    )
    return response.text.strip()


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка голосовых сообщений"""
    message = update.message
    user_id = update.effective_user.id
    is_private = message.chat.type == "private"

    if not is_private:
        return

    voice_path = f"user_voice_{user_id}_{message.message_id}.ogg"
    try:
        voice_file = await context.bot.get_file(update.message.voice.file_id)
        await voice_file.download_to_drive(voice_path)

        user_text = await transcribe_voice(voice_path)

        if not user_text or not user_text.strip():
            await update.message.reply_text(
                "Не удалось разобрать голосовое сообщение — попробуйте сказать чуть чётче и громче."
            )
            return

        log_message(user_id, update.effective_user.username, f"[Голосовое]: {user_text}")

        user_name = update.effective_user.first_name or "друг"
        await process_ai_response(user_id, user_name, user_text, update, context, send_as_voice=True)

    except Exception as e:
        logger.error(f"Voice Error: {e}")
        await update.message.reply_text("Не удалось распознать голосовое сообщение.")
    finally:
        if os.path.exists(voice_path):
            os.remove(voice_path)


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    init_db()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    print("Bot started. Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == "__main__":
        main()
