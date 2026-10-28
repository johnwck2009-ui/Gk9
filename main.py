import os
import random
import sqlite3
import threading
from datetime import date
from flask import Flask
from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler, ContextTypes,
    MessageHandler, filters,
)

TOKEN = os.getenv("BOT_TOKEN")
DB_PATH = os.getenv("DB_PATH", "gk9_scores.db")
DB_LOCK = threading.Lock()

QUESTIONS = [
    {"player":"Cristiano Ronaldo","clues":"I am Portuguese. I have played for Manchester United, Real Madrid and Juventus.","level":"Easy","options":["Cristiano Ronaldo","Bruno Fernandes","Luis Figo","Bernardo Silva"]},
    {"player":"Lionel Messi","clues":"I am Argentine. I became famous at Barcelona and later played for PSG and Inter Miami.","level":"Easy","options":["Ángel Di María","Lionel Messi","Sergio Agüero","Lautaro Martínez"]},
    {"player":"Kylian Mbappé","clues":"I am French. I starred for PSG and helped France win the 2018 World Cup.","level":"Easy","options":["Antoine Griezmann","Ousmane Dembélé","Kylian Mbappé","Olivier Giroud"]},
    {"player":"Mohamed Salah","clues":"I am an Egyptian forward known for my time at Liverpool.","level":"Easy","options":["Sadio Mané","Riyad Mahrez","Mohamed Salah","Victor Osimhen"]},
    {"player":"Erling Haaland","clues":"I am a Norwegian striker who has scored many goals for Manchester City.","level":"Easy","options":["Harry Kane","Erling Haaland","Alexander Isak","Darwin Núñez"]},
    {"player":"Neymar Jr","clues":"I am Brazilian and have played for Barcelona, PSG and Al-Hilal.","level":"Easy","options":["Vinícius Júnior","Ronaldinho","Neymar Jr","Rivaldo"]},
    {"player":"Luka Modrić","clues":"I am a Croatian midfielder who won the 2018 Ballon d'Or after reaching the World Cup final.","level":"Medium","options":["Ivan Rakitić","Luka Modrić","Toni Kroos","Mateo Kovačić"]},
    {"player":"Zinedine Zidane","clues":"I am a French football legend who won the 1998 World Cup and coached Real Madrid.","level":"Medium","options":["Thierry Henry","Patrick Vieira","Zinedine Zidane","Didier Deschamps"]},
    {"player":"Andrés Iniesta","clues":"I am a Spanish midfielder who scored the winning goal in the 2010 World Cup final.","level":"Medium","options":["Xavi","Andrés Iniesta","Sergio Busquets","Cesc Fàbregas"]},
    {"player":"Didier Drogba","clues":"I am an Ivorian striker remembered for my success at Chelsea.","level":"Medium","options":["Samuel Eto'o","Yaya Touré","Didier Drogba","George Weah"]},
    {"player":"Ronaldinho","clues":"I am a Brazilian playmaker famous for my skills and smile. I won the 2005 Ballon d'Or.","level":"Medium","options":["Kaká","Ronaldo Nazário","Ronaldinho","Romário"]},
    {"player":"Thierry Henry","clues":"I am a French striker and Arsenal legend who also played for Barcelona.","level":"Medium","options":["Thierry Henry","David Trezeguet","Eric Cantona","Robert Pirès"]},
    {"player":"George Weah","clues":"I am a Liberian football legend who won the 1995 Ballon d'Or.","level":"Hard","options":["Jay-Jay Okocha","George Weah","Abedi Pele","Nwankwo Kanu"]},
    {"player":"Franz Beckenbauer","clues":"I was a German defender nicknamed Der Kaiser and won the World Cup as player and coach.","level":"Hard","options":["Gerd Müller","Lothar Matthäus","Franz Beckenbauer","Karl-Heinz Rummenigge"]},
    {"player":"Lev Yashin","clues":"I was a Soviet goalkeeper, nicknamed the Black Spider, and won the 1963 Ballon d'Or.","level":"Hard","options":["Gianluigi Buffon","Dino Zoff","Lev Yashin","Gordon Banks"]},
    {"player":"Roberto Carlos","clues":"I am a Brazilian left-back famous for powerful free kicks and playing for Real Madrid.","level":"Medium","options":["Cafu","Marcelo","Roberto Carlos","Dani Alves"]},
    {"player":"Mia Hamm","clues":"I am an American football icon who helped the US win two Women's World Cups.","level":"Hard","options":["Abby Wambach","Mia Hamm","Megan Rapinoe","Alex Morgan"]},
    {"player":"Sadio Mané","clues":"I am a Senegalese forward who played for Liverpool and helped my country win AFCON in 2021.","level":"Medium","options":["Sadio Mané","Mohamed Salah","Pierre-Emerick Aubameyang","Victor Moses"]},
    {"player":"Didier Deschamps","clues":"I captained France to the 1998 World Cup and later coached France to the 2018 title.","level":"Hard","options":["Laurent Blanc","Didier Deschamps","Zinedine Zidane","Aimé Jacquet"]},
    {"player":"Jude Bellingham","clues":"I am an English midfielder who played for Borussia Dortmund before joining Real Madrid in 2023.","level":"Easy","options":["Phil Foden","Declan Rice","Jude Bellingham","Cole Palmer"]},
    {"player":"Yaya Touré","clues":"I am an Ivorian midfielder who starred for Manchester City and Barcelona.","level":"Medium","options":["Kolo Touré","Yaya Touré","Michael Essien","John Obi Mikel"]},
    {"player":"Gianluigi Buffon","clues":"I am an Italian goalkeeper and 2006 World Cup winner, best known for my long spell at Juventus.","level":"Hard","options":["Iker Casillas","Gianluigi Buffon","Petr Čech","Manuel Neuer"]},
    {"player":"Marta","clues":"I am a Brazilian footballer often regarded as one of the greatest women's players ever.","level":"Hard","options":["Marta","Birgit Prinz","Christine Sinclair","Sam Kerr"]},
    {"player":"Wayne Rooney","clues":"I am an English forward and Manchester United's all-time leading scorer.","level":"Medium","options":["Alan Shearer","Wayne Rooney","Frank Lampard","Steven Gerrard"]},
]

app_web = Flask(__name__)

@app_web.get("/")
def home():
    return "GK9 Who's That Player? bot is running."

def connect_db():
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, name TEXT NOT NULL DEFAULT 'Player',
        points INTEGER NOT NULL DEFAULT 0, games INTEGER NOT NULL DEFAULT 0,
        correct INTEGER NOT NULL DEFAULT 0
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS daily_attempts (
        user_id INTEGER NOT NULL, day TEXT NOT NULL,
        PRIMARY KEY(user_id, day)
    )""")
    conn.commit()
    return conn

def ensure_user(user_id, name):
    with DB_LOCK, connect_db() as conn:
        conn.execute("INSERT OR IGNORE INTO users(user_id, name) VALUES(?, ?)", (user_id, name))
        conn.execute("UPDATE users SET name=? WHERE user_id=?", (name, user_id))

def record_answer(user_id, name, points, correct, daily=False):
    today = date.today().isoformat()
    with DB_LOCK, connect_db() as conn:
        conn.execute("INSERT OR IGNORE INTO users(user_id, name) VALUES(?, ?)", (user_id, name))
        if daily:
            cur = conn.execute("INSERT OR IGNORE INTO daily_attempts(user_id, day) VALUES(?, ?)", (user_id, today))
            if cur.rowcount == 0:
                return False
        conn.execute("""UPDATE users SET name=?, points=points+?, games=games+1,
                     correct=correct+? WHERE user_id=?""",
                     (name, points, int(correct), user_id))
    return True

def get_question(level=None, daily=False):
    pool = [q for q in QUESTIONS if level is None or q["level"] == level]
    if daily:
        return pool[date.today().toordinal() % len(pool)]
    return random.choice(pool)

def menu_keyboard():
    return ReplyKeyboardMarkup(
        [["⚽ Guess the Player", "📅 Daily Challenge"],
         ["🏆 Leaderboard", "📊 My Stats"],
         ["ℹ️ How to Play"]],
        resize_keyboard=True
    )

def question_keyboard(q, daily=False):
    buttons = [[InlineKeyboardButton(option, callback_data=f"answer:{QUESTIONS.index(q)}:{i}:{int(daily)}")]
               for i, option in enumerate(q["options"])]
    buttons.append([InlineKeyboardButton("⬅️ Main Menu", callback_data="menu")])
    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id, user.full_name or user.username or "Player")
    context.user_data.pop("current_question", None)
    await update.message.reply_text(
        "⚽ Welcome to GK9 Who's That Player?\n\n"
        "Think you know football? Identify players from clues, earn points, "
        "take the Daily Challenge and climb the leaderboard.\n\nChoose an option below to get started.",
        reply_markup=menu_keyboard()
    )

async def send_question(update, context, daily=False, level=None):
    q = get_question(level=level, daily=daily)
    context.user_data["current_question"] = QUESTIONS.index(q)
    context.user_data["daily_question"] = daily
    text = ("📅 DAILY CHALLENGE\n\n" if daily else "⚽ GUESS THE PLAYER\n\n")
    text += f"Difficulty: {q['level']}\nPoints: { {'Easy':10,'Medium':20,'Hard':30}[q['level']] }\n\n{q['clues']}\n\nWho am I?"
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=question_keyboard(q, daily))
    else:
        await update.message.reply_text(text, reply_markup=question_keyboard(q, daily))

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    if msg == "⚽ Guess the Player":
        await send_question(update, context)
    elif msg == "📅 Daily Challenge":
        await send_question(update, context, daily=True)
    elif msg == "🏆 Leaderboard":
        await leaderboard(update, context)
    elif msg == "📊 My Stats":
        await stats(update, context)
    elif msg == "ℹ️ How to Play":
        await update.message.reply_text(
            "How to play GK9:\n\n"
            "1. Read the player clues.\n2. Choose one of the four answers.\n"
            "3. Earn 10 points for Easy, 20 for Medium or 30 for Hard when correct.\n"
            "4. Try the Daily Challenge once per day for points.\n"
            "5. Check My Stats and compete on the leaderboard.\n\n"
            "Questions are built into the bot; live data or external APIs are not needed.",
            reply_markup=menu_keyboard()
        )
    else:
        await update.message.reply_text("Use the buttons below to play GK9.", reply_markup=menu_keyboard())

async def answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    q_index, option_index, daily = int(parts[1]), int(parts[2]), bool(int(parts[3]))
    q = QUESTIONS[q_index]
    user = query.from_user
    is_correct = q["options"][option_index] == q["player"]
    points = {"Easy":10, "Medium":20, "Hard":30}[q["level"]] if is_correct else 0
    accepted = record_answer(user.id, user.full_name or user.username or "Player", points, is_correct, daily=daily)
    if daily and not accepted:
        result = "You have already completed today's Daily Challenge. Come back tomorrow!"
    elif is_correct:
        result = f"✅ Correct! The player is {q['player']}.\nYou earned {points} points."
    else:
        result = f"❌ Not quite. The correct answer is {q['player']}.\nNo points this time."
    context.user_data.pop("current_question", None)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Play Again", callback_data="play")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard"),
         InlineKeyboardButton("📊 My Stats", callback_data="stats")],
        [InlineKeyboardButton("⬅️ Main Menu", callback_data="menu")]
    ])
    await query.edit_message_text(result, reply_markup=keyboard)

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with DB_LOCK, connect_db() as conn:
        rows = conn.execute("SELECT name, points, correct FROM users ORDER BY points DESC, correct DESC LIMIT 10").fetchall()
    text = "🏆 GK9 LEADERBOARD\n\n"
    if not rows:
        text += "No scores yet. Be the first to play!"
    else:
        medals = ["🥇", "🥈", "🥉"]
        for i, (name, points, correct) in enumerate(rows, 1):
            marker = medals[i-1] if i <= 3 else f"{i}."
            text += f"{marker} {name[:24]} — {points} pts ({correct} correct)\n"
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Main Menu", callback_data="menu")]]))
    else:
        await update.message.reply_text(text, reply_markup=menu_keyboard())

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id, user.full_name or user.username or "Player")
    with DB_LOCK, connect_db() as conn:
        row = conn.execute("SELECT points, games, correct FROM users WHERE user_id=?", (user.id,)).fetchone()
    points, games, correct = row or (0, 0, 0)
    accuracy = round(correct * 100 / games) if games else 0
    text = (f"📊 YOUR GK9 STATS\n\nPoints: {points}\nQuestions answered: {games}"
            f"\nCorrect answers: {correct}\nAccuracy: {accuracy}%")
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Main Menu", callback_data="menu")]]))
    else:
        await update.message.reply_text(text, reply_markup=menu_keyboard())

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    if data.startswith("answer:"):
        await answer_question(update, context)
    elif data == "menu":
        await query.answer()
        await query.edit_message_text("Main menu: choose what you'd like to do using the Telegram menu buttons.")
        await query.message.reply_text("Welcome back to GK9. What would you like to play?", reply_markup=menu_keyboard())
    elif data == "play":
        await query.answer()
        await send_question(update, context)
    elif data == "leaderboard":
        await query.answer()
        await leaderboard(update, context)
    elif data == "stats":
        await query.answer()
        await stats(update, context)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f"Bot error: {context.error!r}")

def run_bot():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is missing.")
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(CallbackQueryHandler(callbacks))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_error_handler(error_handler)
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    threading.Thread(target=lambda: app_web.run(host="0.0.0.0", port=port), daemon=True).start()
    run_bot()
