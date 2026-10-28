# GK9 Who's That Player?

A Telegram football guessing game. Players identify footballers from clues, earn points, take a daily challenge, view personal stats, and compete on a leaderboard.

## Features

- Telegram button-based main menu
- Multiple-choice player guessing questions
- Easy, Medium, and Hard questions worth 10, 20, and 30 points
- Daily challenge limited to one scored attempt per user per day
- Leaderboard and personal statistics
- Built-in question bank; no external sports API required
- SQLite score storage
- Flask health-check endpoint for Render

## Run locally

1. Install Python 3.10 or newer.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a Telegram bot with [@BotFather](https://t.me/BotFather) and copy its token.
4. Set the token as an environment variable named `BOT_TOKEN`.
5. Run the bot:

   ```bash
   python main.py
   ```

The bot uses long polling. Do not commit the bot token to this repository.

## Deploy on Render

1. Create a **Web Service** from this repository.
2. Render can use `render.yaml`; otherwise set the build command to `pip install -r requirements.txt` and the start command to `python main.py`.
3. Add `BOT_TOKEN` in the service's Environment settings. Paste the token from BotFather as its value; do not add it to GitHub.
4. Deploy, then open the bot in Telegram and press **Start**.

The Flask `/` endpoint is a health check. SQLite stores scores in `gk9_scores.db` by default. For scores to survive service restarts and redeploys, configure a persistent disk on Render and set `DB_PATH` to a file path on that disk.

## Notes

- The question bank is included in `main.py` and can be expanded by adding question entries to `QUESTIONS`.
- This bot provides football trivia and entertainment only. It does not provide live match scores or betting services.
