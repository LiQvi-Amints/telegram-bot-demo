This is telegram bot made with Python 3, Aiogram 3, and Sympy.  
It can calculate, simplify, and even solve equations — right inside Telegram.
What this bot can do
Calculate and simplify expressions like `2+2`, `sin(pi/4)`  
Solve equations (for example: `x^2 - 2 = 0`)  
Remember your recent calculations (history command)  
Has inline buttons to reuse results  
Limits spam with a built-in cooldown  
Clean and async Python code — easy to expand

Quick start

Install dependencies:

  bash
  pip install -r requirements.txt
   


| Command | What it does |
|----------|---------------|
| `/start` | Shows welcome message and short help |
| `/help` | Quick guide |
| `/calc` | Enter calculation mode — just type expressions |
| `/history` | Shows your recent calculations |

You can also just send something like `2+2` and the bot will calculate it instantly.

Example


User: /calc
Bot: Send an expression to evaluate or solve.

User: x^2 - 2 = 0
Bot: Solved for x:
[-√2, √2]

---

used

Python 3.10+
Aiogram 3 (Telegram bot framework)
Sympy (math library)
AsyncIO
Inline buttons & callback handling


About

This bot was made as a demo project to show real coding skills in Python + Aiogram.  
It’s clean, safe, and fully working, you can use it as a base for more advanced bots  
Don’t share your real bot token in public repositories!

License

MIT License — feel free to use, modify, or learn from it.  
Just don’t forget to give credit
