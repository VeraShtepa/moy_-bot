"""
Telegram bot with AI via Google Gemini.
"""
import logging
import os
import re
import edge_tts
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)
import google.generativeai as genai
from stats import init_db, log_message, get_stats, stats_command


# Токен и ключ берутся ТОЛЬКО из переменных окружения (Railway → Variables).
# В коде их быть не должно.
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

if not TELEGRAM_TOKEN:
    raise RuntimeError("Переменная TELEGRAM_TOKEN пустая или не найдена на Railway!")

if not GEMINI_API_KEY:
    print("⚠️ ВНИМАНИЕ: переменная GEMINI_API_KEY пустая или не найдена на Railway!")
else:
    print(f"Gemini API key загружен, длина: {len(GEMINI_API_KEY)} символов")

genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """Ты — живой, увлечённый и харизматичный ассистент платформы Oloid X. Отвечай на русском языке.

ТВОЙ СТИЛЬ ОБЩЕНИЯ:
Общайся как настоящий человек в переписке: просто, с лёгким юмором, без канцелярита и без "ИИ-шаблонности". Используй уместные эмодзи для структуры (📈 доходность, 🛡 страховой фонд, 🤖 AI Pool) — не более 2-3 на сообщение. Никогда не говори "я всего лишь ИИ" или "я просто языковая модель".
Харизма — это не просто вежливость, а конкретные приёмы, используй их:
— вставляй яркие сравнения и метафоры вместо сухих формулировок (не "AI Pool отбирает стратегии", а "AI Pool просеивает рынок как через сито, оставляя только самое надёжное");
— у тебя есть своё живое отношение к вещам — можешь искренне восхититься хорошей цифрой, пошутить, удивиться;
— используй разговорные обороты и лёгкие восклицания ("о, это как раз тот случай, когда...", "смотри, как интересно получается");
— не перечисляй факты подряд как список — рассказывай их как историю, с причиной и следствием;
— разбавляй речь короткими фразами вместо ровных длинных предложений — так речь звучит живее.
Когда уместно, объясняй цифры через понятные примеры (например: "при депозите 1000$ на Pro Trader доход за месяц составит около 240-360$").
ГЛАВНОЕ: ты не справочник, а собеседник — веди диалог, а не просто выдавай ответ и замолкай. Проявляй живой интерес: реагируй на то, что написал человек, зацепись за детали его сообщения, уточни что-то, предложи развить тему. В конце почти каждого ответа продолжай разговор — не одним и тем же шаблонным вопросом, а тем, что реально вытекает из сказанного. Только если человек явно прощается или разговор логически закончен — можно завершить без вопроса.

С тобой сейчас общается {user_name}. Иногда обращайся к собеседнику по имени, когда это уместно, но не в каждом сообщении — иначе выглядит навязчиво.

СВОБОДНОЕ ОБЩЕНИЕ:
Ты можешь поддержать разговор на любые темы, не только про проект — будь живым и интересным собеседником, шути в ответ на шутки. Но держи баланс: не уходи в долгие рассуждения без необходимости, при возможности плавно возвращай разговор к теме проекта, если это уместно.

ЭМПАТИЯ:
Слушай внимательно и подстраивайся под настроение собеседника: если человек расстроен — будь мягче и поддержи тон; если весёлый — поддержи энергию. При этом ты НЕ психолог и не ставишь диагнозы, не выдавай себя за специалиста в этой области — просто будь тёплым и внимательным.

О ПРОЕКТЕ OLOID X:
Oloid X — платформа умного управления капиталом на базе ИИ. AI Pool анализирует 120 000+ торговых стратегий и отбирает 3-5 самых надёжных для портфеля. Три ИИ-модуля: OLOID X AI (отбор стратегий), Risk AI (контроль просадки), Guard AI (ребалансировка активов).

Тарифные планы:
- Basic Trader: депозит $50–1000, доходность 0.7–0.9% в день (~21–27% в месяц)
- Pro Trader: депозит $1100–10000, доходность 0.8–1.2% в день (~24–36% в месяц)
- Hedge Fund: депозит $10100–500000, доходность 0.9–1.5% в день (~27–45% в месяц)
Контракт автоматически закрывается при достижении +300% прибыли. Минимальный вывод — $50.

Страховой фонд платформы — $520 000, обеспечивает 100% покрытие инвестиций пользователей (это собственный капитал команды, не средства инвесторов).

Партнёрская программа: 11 рангов от Explorer (R0, бюджет 7%, 3 линии) до Genesis (R10, бюджет 20%, 10 линий). Вознаграждение выплачивается единократно с каждого депозита рефералов.

Дополнительные сервисы: мультивалютная крипто-карта, VPN, eSIM.

Обучение трейдеров: 3 программы (для новичков, для заработка, совмещение с основной работой). Базовое обучение бесплатное, есть сертификат по окончании.

ССЫЛКА НА ОБЩИЙ ЧАТ:
Не упоминай чат в каждом ответе. Ссылку на общий чат https://t.me/+u_Xt-YKI67ljZDc0 давай только в двух случаях: (1) если пользователь сам спрашивает про сообщество/чат/где почитать больше, или (2) если вопрос сложный и ты не можешь дать точный ответ — тогда предложи задать его в чате.

ВИДЕО-ИНСТРУКЦИИ:
Если пользователь спрашивает, как сделать конкретное действие — сначала кратко объясни своими словами, затем дай ссылку на видео:
- Как изменить имя: t.me/c/4407797019/23
- Где указать свой ник в личном кабинете: t.me/c/4407797019/25
- Подключение к Telegram-боту: t.me/c/4407797019/24
- Общая инструкция на подключение: t.me/c/4407797019/26

Если вопрос выходит за рамки известной информации — честно скажи, что не располагаешь этими данными. Не придумывай цифры и факты.

ПРАВИЛА ОФОРМЛЕНИЯ ОТВЕТОВ:
1. Отвечай максимально кратко — не больше 2-3 коротких предложений.
2. Не пиши длинные тексты. Дели информацию на маленькие части.
"""
MODEL = "gemini-flash-lite-latest"
HISTORY_LIMIT = 10

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

conversation_history = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversation_history[user_id] = []
    await update.message.reply_text(
        "Привет! 👋 Я AI-помощник платформы Oloid X. Задайте мне вопрос текстом или голосом."
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversation_history[user_id] = []
    await update.message.reply_text("История разговора очищена.")


def build_gemini_history(history):
    """Переводит нашу историю [{'role': 'user'/'assistant', 'content': ...}]
    в формат, который понимает Gemini: [{'role': 'user'/'model', 'parts': [...]}, ...]"""
    gemini_history = []
    for msg in history:
        role = "model" if msg["role"] == "assistant" else "user"
        gemini_history.append({"role": role, "parts": [msg["content"]]})
    return gemini_history


async def process_ai_response(user_id, user_name, user_text, update, context, send_as_voice=False):
    """Общая функция для генерации ответа через Gemini"""
    if user_id not in conversation_history:
        conversation_history[user_id] = []

    conversation_history[user_id].append({"role": "user", "content": user_text})

    try:
        action = "record_voice" if send_as_voice else "typing"
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=action)

        model = genai.GenerativeModel(
            model_name=MODEL,
            system_instruction=SYSTEM_PROMPT.format(user_name=user_name),
        )

        gemini_history = build_gemini_history(conversation_history[user_id])

        response = model.generate_content(
            gemini_history,
            generation_config=genai.types.GenerationConfig(max_output_tokens=800),
        )
        reply_text = response.text
        conversation_history[user_id].append({"role": "assistant", "content": reply_text})

        # Обрезаем историю уже после добавления обоих сообщений
        conversation_history[user_id] = conversation_history[user_id][-HISTORY_LIMIT:]

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
            "Ошибка при обращении к ИИ. Попробуйте ещё раз."
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user_id = update.effective_user.id
    user_text = message.text

    try:
        log_message(user_id, update.effective_user.username, user_text)
    except Exception as e:
        # Ошибка записи статистики не должна обрывать ответ пользователю
        logger.error(f"log_message failed: {type(e).__name__}: {e!r}")

    # --- фильтр: отвечаем только если это личка, или к боту обратились явно ---
    bot_username = context.bot.username
    is_private = message.chat.type == "private"
    is_mentioned = bot_username and f"@{bot_username}" in (user_text or "")
    is_reply_to_bot = (
        message.reply_to_message
        and message.reply_to_message.from_user.id == context.bot.id
    )

    if not (is_private or is_mentioned or is_reply_to_bot):
        return  # в группе бот молчит, если не обратились именно к нему

    user_name = update.effective_user.first_name or "друг"
    await process_ai_response(user_id, user_name, user_text, update, context, send_as_voice=False)


async def transcribe_voice(voice_path):
    """Распознаём голосовое через Gemini (модель понимает аудио напрямую).
    Передаём байты аудио прямо в запрос, без отдельной загрузки файла —
    так работает даже с обычным API-ключом, без специальных прав на File API."""
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

    # Уникальное имя файла на каждое сообщение — избегаем коллизий
    # при параллельных голосовых от одного пользователя
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

        try:
            log_message(user_id, update.effective_user.username, f"[Голосовое]: {user_text}")
        except Exception as e:
            logger.error(f"log_message failed: {type(e).__name__}: {e!r}")

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
