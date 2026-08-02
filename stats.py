"""
Модуль статистики для Telegram-бота.
Использует SQLite (файл stats.db), ничего дополнительно ставить не нужно —
sqlite3 встроен в Python.
"""

import sqlite3
from datetime import datetime, timedelta

DB_PATH = "stats.db"


def init_db():
    """Создаёт таблицу для логов, если её ещё нет. Вызывать один раз при старте бота."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            text TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()


def log_message(user_id: int, username: str, text: str):
    """Записывает одно сообщение в базу. Вызывать при каждом входящем сообщении."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO messages (user_id, username, text, timestamp) VALUES (?, ?, ?, ?)",
        (user_id, username or "нет username", text, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_stats():
    """Считает статистику: всего сообщений, уникальных пользователей, за сегодня, топ-5 активных."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM messages")
    total_messages = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT user_id) FROM messages")
    unique_users = cur.fetchone()[0]

    today = datetime.now().date().isoformat()
    cur.execute("SELECT COUNT(*) FROM messages WHERE timestamp LIKE ?", (f"{today}%",))
    today_count = cur.fetchone()[0]

    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    cur.execute("SELECT COUNT(*) FROM messages WHERE timestamp >= ?", (week_ago,))
    week_count = cur.fetchone()[0]

    cur.execute("""
        SELECT username, COUNT(*) as cnt FROM messages
        GROUP BY user_id
        ORDER BY cnt DESC
        LIMIT 5
    """)
    top_users = cur.fetchall()

    conn.close()

    return {
        "total_messages": total_messages,
        "unique_users": unique_users,
        "today_count": today_count,
        "week_count": week_count,
        "top_users": top_users,
    }


async def stats_command(update, context):
    """Обработчик команды /stats — присылает сводку прямо в чат."""
    stats = get_stats()

    top_lines = "\n".join(
        f"  {i+1}. @{username} — {count} сообщений"
        for i, (username, count) in enumerate(stats["top_users"])
    ) or "  пока нет данных"

    text = (
        "📊 Статистика бота\n\n"
        f"Всего сообщений: {stats['total_messages']}\n"
        f"Уникальных пользователей: {stats['unique_users']}\n"
        f"Сообщений сегодня: {stats['today_count']}\n"
        f"Сообщений за 7 дней: {stats['week_count']}\n\n"
        f"Топ активных:\n{top_lines}"
    )

    await update.message.reply_text(text)
