import os
import asyncio
import logging
import time
from typing import Dict, List, Tuple
import sympy as sp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
TOKEN = os.getenv("")
if not TOKEN:
    raise SystemExit("")
bot = Bot(token=TOKEN)
dp = Dispatcher()
USER_HISTORY: Dict[int, List[Tuple[str, str]]] = {}
PENDING_INPUT: Dict[int, str] = {}       
LAST_CALL: Dict[int, float] = {}        
HISTORY_SIZE = 8
RATE_LIMIT_SECONDS = 0.8
def rate_limited(user_id: int) -> bool:
    now = time.time()
    last = LAST_CALL.get(user_id, 0.0)
    if now - last < RATE_LIMIT_SECONDS:
        return True
    LAST_CALL[user_id] = now
    return False
def safe_sympify(expr: str):
    expr = expr.strip().replace("^", "**")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+-*/^()[]{},.= _**<>")
    if not set(expr) <= allowed:
        raise ValueError("Expression contains forbidden characters.")
    return sp.sympify(expr)
def push_history(user_id: int, request: str, result: str):
    hist = USER_HISTORY.setdefault(user_id, [])
    hist.insert(0, (request, result))
    if len(hist) > HISTORY_SIZE:
        hist.pop()
def make_action_kb(user_id: int, idx: int = 0) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(" Reuse", callback_data=f"reuse:{user_id}:{idx}"),
         InlineKeyboardButton(" Solve for x", callback_data=f"solve:{user_id}:{idx}")],
        [InlineKeyboardButton(" History", callback_data=f"hist:{user_id}:0")]
    ])
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Small+SmartMath Bot\n"
        "Commands:\n"
        "/calc — calculate or simplify an expression\n"
        "/history — show recent calculations\n"
        "/help — short help\n\n"
        "After /calc send an expression like: 2+2, sin(pi/4), x^2-2=0"
    )
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.reply("Usage:\n/calc → then send expression\n/history → view recent entries\nYou can reuse results with inline buttons.")
@dp.message(Command("calc"))
async def cmd_calc(message: types.Message):
    user_id = message.from_user.id
    PENDING_INPUT[user_id] = "calc"
    await message.reply("Send the expression to evaluate or solve (use ^ or ** for powers).")
@dp.message(Command("history"))
async def cmd_history(message: types.Message):
    user_id = message.from_user.id
    hist = USER_HISTORY.get(user_id, [])
    if not hist:
        await message.reply("History is empty.")
        return
    lines = []
    for i, (req, res) in enumerate(hist[:HISTORY_SIZE]):
        lines.append(f"{i+1}. {req} → {res}")
    await message.reply("\n".join(lines))
@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    text = (message.text or "").strip()
    if rate_limited(user_id):
        await message.reply("Too fast — slow down a bit.")
        return
    if PENDING_INPUT.get(user_id) == "calc":
        PENDING_INPUT.pop(user_id, None)
        try:
            if "=" in text:
                left, right = text.split("=", 1)
                eq = sp.Eq(safe_sympify(left), safe_sympify(right))
                vars = sorted(list(eq.free_symbols), key=lambda s: str(s))
                if not vars:
                    raise ValueError("No variables found to solve for.")
                sol = sp.solve(eq, vars[0])
                sol_str = sp.pretty(sol)
                push_history(user_id, text, str(sol))
                kb = make_action_kb(user_id, 0)
                await message.reply(f"Solved for {vars[0]}:\n{sol_str}", reply_markup=kb)
            else:
                expr = safe_sympify(text)
                if not expr.free_symbols:
                    val = float(sp.N(expr))
                    res = str(val)
                else:
                    simplified = sp.simplify(expr)
                    res = str(simplified)
                push_history(user_id, text, res)
                kb = make_action_kb(user_id, 0)
                await message.reply(f"{text} → {res}", reply_markup=kb)
        except Exception as e:
            await message.reply(f"Error: {e}")
        return
    if any(ch in text for ch in "+-*/^()") and len(text) < 200:
        try:
            expr = safe_sympify(text)
            if not expr.free_symbols:
                val = float(sp.N(expr))
                res = str(val)
                push_history(user_id, text, res)
                kb = make_action_kb(user_id, 0)
                await message.reply(f"Quick: {text} → {res}", reply_markup=kb)
                return
        except Exception:
            pass
    await message.reply("I didn't understand. Use /calc to evaluate or /help.")
@dp.callback_query()
async def callbacks(query: CallbackQuery):
    data = (query.data or "")
    user_id = query.from_user.id
    parts = data.split(":")
    try:
        if parts[0] == "reuse":
            target_user = int(parts[1]); idx = int(parts[2])
            hist = USER_HISTORY.get(target_user, [])
            if idx < len(hist):
                req, res = hist[idx]
                await query.message.answer(f"Reusing: {req}\nResult: {res}")
            else:
                await query.message.answer("Entry not found.")
        elif parts[0] == "solve":
            target_user = int(parts[1]); idx = int(parts[2])
            hist = USER_HISTORY.get(target_user, [])
            if idx < len(hist):
                req, _ = hist[idx]
                if "=" in req:
                    left, right = req.split("=", 1)
                    eq = sp.Eq(safe_sympify(left), safe_sympify(right))
                    vars = sorted(list(eq.free_symbols), key=lambda s: str(s))
                    sol = sp.solve(eq, vars[0])
                    await query.message.answer(f"Solve for {vars[0]}: {sp.pretty(sol)}")
                else:
                    expr = safe_sympify(req)
                    vars = sorted(list(expr.free_symbols), key=lambda s: str(s))
                    if not vars:
                        await query.message.answer("No variable to solve for.")
                    else:
                        sol = sp.solve(sp.Eq(expr, 0), vars[0])
                        await query.message.answer(f"Solve {req}=0 for {vars[0]}: {sp.pretty(sol)}")
            else:
                await query.message.answer("Entry not found.")
        elif parts[0] == "hist":
            target_user = int(parts[1])
            hist = USER_HISTORY.get(target_user, [])
            if not hist:
                await query.message.answer("History empty.")
            else:
                lines = [f"{i+1}. {r} → {s}" for i, (r, s) in enumerate(hist[:HISTORY_SIZE])]
                await query.message.answer("\n".join(lines))
    except Exception as e:
        await query.message.answer(f"Callback error: {e}")
    finally:
        await query.answer()
async def on_startup():
    cmds = [
        types.BotCommand("start", "Start the bot"),
        types.BotCommand("calc", "Evaluate or solve an expression"),
        types.BotCommand("history", "Show recent calculations"),
        types.BotCommand("help", "Help")
    ]
    try:
        await bot.set_my_commands(cmds)
    except Exception:
        logging.exception("Failed to set commands")
async def main():
    await on_startup()
    try:
        logging.info("Bot running")
        await dp.start_polling(bot)
    finally:
        logging.info("Shutting down, closing session")
        try:
            await bot.session.close()
        except Exception:
            pass
        try:
            await bot.close()
        except Exception:
            pass
if __name__ == "__main__":
    asyncio.run(main())