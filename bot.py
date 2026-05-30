import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types
import telebot

load_dotenv()

GEMINI_API_KEY = os.environ.get("API_KEY")
TELEGRAM_TOKEN = os.environ.get("BOT_TOKEN")
ALLOWED_ID = os.environ.get("ALLOWED_ID")
TODO_FILE = "todos.json"

gemini = genai.Client(api_key=GEMINI_API_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN)


# ── Storage helpers ────────────────────────────────────────────────────────────

def load_todos() -> list:
    if not os.path.exists(TODO_FILE):
        return []
    with open(TODO_FILE, "r") as f:
        content = f.read().strip()
        if not content:
            return []
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Corrupted file — back it up and start fresh
            os.rename(TODO_FILE, TODO_FILE + ".bak")
            return []

def save_todos(todos: list):
    with open(TODO_FILE, "w") as f:
        json.dump(todos, f, indent=2)

def next_id(todos: list) -> int:
    return max((t["id"] for t in todos), default=0) + 1


# ── Gemini: parse natural language into a structured action ───────────────────

SYSTEM_PROMPT = """
You are a to-do list assistant. The user will send natural language messages.
Your job is to understand what they want and return ONLY a valid JSON object.

Current todos will be provided in each request so you can reference them by
id or title when the user says things like "done with task 2" or "remove buy milk".

Respond ONLY with a JSON object in one of these formats:

ADD a task:
{"action": "add", "title": "<task title>"}

COMPLETE a task:
{"action": "complete", "id": <task id>}

DELETE a task:
{"action": "delete", "id": <task id>}

LIST all tasks:
{"action": "list"}

CLEAR all completed tasks:
{"action": "clear_completed"}

UNKNOWN (not a todo request):
{"action": "unknown", "reply": "<friendly reply>"}

Rules:
- Never include extra text, only the JSON object.
- If the user mentions a task by name instead of id, find the matching id from
  the current todos list and use that id.
- If you cannot confidently match a task, return unknown with a helpful message.
- For ADD, clean up the title (remove filler like "add", "remind me to", etc).
"""

def ask_gemini(user_message: str, todos: list) -> dict:
    todos_context = json.dumps(todos, indent=2) if todos else "[]"
    prompt = f"Current todos:\n{todos_context}\n\nUser message: {user_message}"

    for attempt in range(3):
        try:
            response = gemini.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT
                )
            )
            raw = response.text.strip()
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            return json.loads(raw.strip())
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                time.sleep(2 ** attempt)
            else:
                return {"action": "unknown", "reply": f"Gemini error: {e}"}
    return {"action": "unknown", "reply": "Gemini is busy. Try again in a moment."}


# ── Format todo list for Telegram ─────────────────────────────────────────────

def format_todos(todos: list) -> str:
    if not todos:
        return "📭 Your to-do list is empty!"

    pending   = [t for t in todos if not t["done"]]
    completed = [t for t in todos if t["done"]]

    lines = []
    if pending:
        lines.append("📋 *Pending*")
        for t in pending:
            lines.append(f"  `{t['id']}.` ☐ {t['title']}")
    if completed:
        lines.append("\n✅ *Completed*")
        for t in completed:
            lines.append(f"  `{t['id']}.` ☑ ~{t['title']}~")

    return "\n".join(lines)


# ── Execute the action Gemini decided on ──────────────────────────────────────

def execute_action(action: dict) -> str:
    todos = load_todos()
    act = action.get("action")

    if act == "add":
        title = action.get("title", "").strip()
        if not title:
            return "❌ Couldn't figure out what to add. Try again!"
        task = {
            "id": next_id(todos),
            "title": title,
            "done": False,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        todos.append(task)
        save_todos(todos)
        return f"✅ Added: *{title}*"

    elif act == "complete":
        tid = action.get("id")
        for t in todos:
            if t["id"] == tid:
                t["done"] = True
                save_todos(todos)
                return f"☑ Marked done: *{t['title']}*"
        return f"❌ Couldn't find task with id `{tid}`."

    elif act == "delete":
        tid = action.get("id")
        before = len(todos)
        todos = [t for t in todos if t["id"] != tid]
        if len(todos) < before:
            save_todos(todos)
            return f"🗑 Deleted task `{tid}`."
        return f"❌ Couldn't find task with id `{tid}`."

    elif act == "list":
        return format_todos(todos)

    elif act == "clear_completed":
        before = len(todos)
        todos = [t for t in todos if not t["done"]]
        removed = before - len(todos)
        save_todos(todos)
        return f"🧹 Cleared {removed} completed task(s).\n\n" + format_todos(todos)

    elif act == "unknown":
        return action.get("reply", "I didn't understand that. Try: 'add buy milk', 'done with task 1', 'show my list'.")

    return "❓ Something went wrong. Please try again."


def is_authorised(id):
    return int(ALLOWED_ID) == id

# ── Telegram handlers ──────────────────────────────────────────────────────────

@bot.message_handler(commands=["start"])
def handle_start(message):
    if is_authorised(message.from_user.id):
        bot.reply_to(message, (
            "👋 Hey! I'm your *AI To-Do assistant* powered by Gemini.\n\n"
            "Just talk to me naturally:\n"
            "• _add buy groceries_\n"
            "• _mark task 1 as done_\n"
            "• _delete task 2_\n"
            "• _show my list_\n"
            "• _clear completed tasks_\n\n"
            "No need for special commands — just type!"
        ), parse_mode="Markdown")
    else: 
        bot.reply_to(message, "Unauthorised")

@bot.message_handler(commands=["list"])
def handle_list(message):
    if is_authorised(message.from_user.id):
        todos = load_todos()
        bot.reply_to(message, format_todos(todos), parse_mode="Markdown")
    else: 
        bot.reply_to(message, "Unauthorised")

@bot.message_handler(commands=["clear"])
def handle_clear(message):
    if is_authorised(message.from_user.id):
        todos = load_todos()
        todos = [t for t in todos if not t["done"]]
        save_todos(todos)
        bot.reply_to(message, "🧹 Cleared all completed tasks.\n\n" + format_todos(todos), parse_mode="Markdown")
    else: 
        bot.reply_to(message, "Unauthorised")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    if is_authorised(message.from_user.id):
        user_text = message.text
        todos = load_todos()

        bot.send_chat_action(message.chat.id, "typing")

        action = ask_gemini(user_text, todos)
        reply  = execute_action(action)

        bot.reply_to(message, reply, parse_mode="Markdown")
    else: 
        bot.reply_to(message, f"Unauthorised")

# ── Run ────────────────────────────────────────────────────────────────────────

print("✅ Todo bot is running...")
bot.infinity_polling()
