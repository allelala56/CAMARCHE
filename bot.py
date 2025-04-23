import telebot
from flask import Flask, request
import json
import os
from datetime import datetime

API_TOKEN = "7115175533:AAHcFYSUzqagDMuxOttx4jLUNCDdlVyvtZo"
WEBHOOK_URL = "https://blackdjlog.onrender.com/webhook"

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# Load services, wallets, and admin_wallet
def load_json(name):
    with open(name, "r") as f:
        return json.load(f) if os.path.exists(name) else {}

def save_json(name, data):
    with open(name, "w") as f:
        json.dump(data, f)

wallets = load_json("wallet.json")
admin_wallet = load_json("admin_wallet.json")
services = load_json("services.json")
SUPPORT_USERNAME = "blackdjdj"
ADMIN_PASSWORD = "jamais007"

@app.route('/')
def index():
    return "BLACKDJLOG Webhook is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    wallets.setdefault(user_id, 0)
    save_json("wallet.json", wallets)

    with open("logo.jpg", "rb") as photo:
        bot.send_photo(message.chat.id, photo, caption="📌 Bienvenue sur le canal de BLACKDJLOG\n\nPour toute demande, passez en privé avec le support : @" + SUPPORT_USERNAME)

    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    cats = list(set(s["category"] for s in services if s["enabled"]))
    for cat in cats:
        markup.add(telebot.types.InlineKeyboardButton(cat, callback_data="CAT_" + cat))
    markup.add(telebot.types.InlineKeyboardButton("💼 Mon solde", callback_data="SOLDE"))
    markup.add(telebot.types.InlineKeyboardButton("📞 Support", url=f"https://t.me/{SUPPORT_USERNAME}"))

    bot.send_message(message.chat.id, "⬇️ Choisissez une catégorie :", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("CAT_"))
def show_category(call):
    category = call.data.replace("CAT_", "")
    markup = telebot.types.InlineKeyboardMarkup()
    for s in services:
        if s["category"] == category and s["enabled"]:
            label = f'{s["name"]} - {s["price"]}€'
            markup.add(telebot.types.InlineKeyboardButton(label, callback_data=f"BUY_{s['id']}"))
    markup.add(telebot.types.InlineKeyboardButton("🔙 Retour", callback_data="BACK"))
    bot.edit_message_text(f"📦 {category} :", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "SOLDE")
def solde_display(call):
    user_id = str(call.from_user.id)
    bot.answer_callback_query(call.id, text=f"💰 Solde : {wallets.get(user_id, 0)}€")

@bot.callback_query_handler(func=lambda call: call.data.startswith("BUY_"))
def buy_service(call):
    sid = call.data.replace("BUY_", "")
    user_id = str(call.from_user.id)
    service = next((s for s in services if s["id"] == sid), None)
    if not service:
        bot.answer_callback_query(call.id, "Service introuvable.")
        return
    if service.get("restricted_time") is not None and datetime.now().hour != service["restricted_time"]:
        bot.answer_callback_query(call.id, "⏰ Disponible uniquement à 00h.")
        return
    if wallets.get(user_id, 0) < service["price"]:
        bot.answer_callback_query(call.id, "❌ Solde insuffisant.")
        return

    wallets[user_id] -= service["price"]
    admin_wallet["admin"] = admin_wallet.get("admin", 0) + service["price"]
    save_json("wallet.json", wallets)
    save_json("admin_wallet.json", admin_wallet)
    bot.answer_callback_query(call.id, f"✅ {service['name']} acheté !")

@bot.callback_query_handler(func=lambda call: call.data == "BACK")
def back(call):
    start(call.message)

# Config webhook lors du lancement du serveur
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
