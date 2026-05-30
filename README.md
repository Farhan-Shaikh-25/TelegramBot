# 📋 Telegram AI To-Do Bot

A personal Telegram bot that manages your to-do list using natural language, powered by Google Gemini. Just talk to it like a human — no special syntax needed.

---

## Features

- Add, complete, and delete tasks using plain English
- Gemini understands context — refer to tasks by name or ID
- Tasks stored locally in a `todos.json` file
- Rate limit protection with automatic retries
- Authorized access — only you can use it

---

## Project Structure

```
TelegramBot/
├── bot.py            # Main bot code
├── requirements.txt  # Python dependencies
├── .env              # Secret keys (never commit this)
└── todos.json        # Auto-created on first task
```

---

## Prerequisites

- Python 3.10+
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)
- Your Telegram user ID from [@userinfobot](https://t.me/userinfobot)

---

## Setup

**1. Clone the repo**
```bash
git clone https://github.com/Farhan-Shaikh-25/TelegramBot.git
cd TelegramBot
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Create your `.env` file**
```
API_KEY=your_gemini_api_key
BOT_TOKEN=your_telegram_bot_token
ALLOWED_ID=your_telegram_user_id
```

**4. Run the bot**
```bash
python bot.py
```

---

## Usage

Just send any natural language message to your bot on Telegram:

| What you type | What happens |
|---|---|
| `add buy groceries` | Adds a new task |
| `I finished task 2` | Marks task 2 as done |
| `remove the milk task` | Finds and deletes by name |
| `show my list` | Lists all tasks |
| `clear completed` | Removes all done tasks |

### Slash Commands

| Command | Description |
|---|---|
| `/start` | Welcome message and usage guide |
| `/list` | Show all tasks |
| `/clear` | Remove all completed tasks |

---

## Data Storage

Tasks are saved in `todos.json` in the project folder:

```json
[
  {"id": 1, "title": "buy groceries", "done": false, "created": "2026-05-28 10:00"},
  {"id": 2, "title": "call doctor",   "done": true,  "created": "2026-05-28 09:00"}
]
```

---

## Rate Limits

Uses `gemini-2.5-flash-lite` which gives the most generous free tier:

| Limit | Value |
|---|---|
| Requests per minute | 15 RPM |
| Requests per day | 1,000 RPD |

The bot handles `429` rate limit errors automatically with exponential backoff retries.

---

## Security

- Only your Telegram user ID (set in `ALLOWED_ID`) can interact with the bot
- All secrets are stored in `.env` and never hardcoded

---

## Dependencies

| Package | Purpose |
|---|---|
| `google-genai` | Gemini API client |
| `pyTelegramBotAPI` | Telegram bot framework |
| `python-dotenv` | Load `.env` file |

---

## License

MIT
