import os
from boxbotapi import NewBotAPI, NewMessage, NewUpdate, ModeRichText
from boxbotapi import configs as cfg

os.environ["DEBOX_BOT_API_KEY"] = os.getenv("DEBOX_BOT_API_KEY")
os.environ["DEBOX_BOT_API_SECRET"] = os.getenv("DEBOX_BOT_API_SECRET")

TARGET_GROUP_CHAT_ID = "c8wm9ddj"

bot = NewBotAPI(
    os.getenv("DEBOX_BOT_API_KEY"),
    os.getenv("DEBOX_BOT_API_SECRET")
)

cfg.Debug = False
cfg.MessageListener = True

print("🚀 预售小助手机器人已启动（美化卡片模式）")

def send_rich_alert():
    msg_text = (
        "🚀 **CheesePad New Pool Alert**\n\n"
        "**Pool:** #Goats - Presale\n"
        "**Presale:** Goats (Goats)\n"
        "💰 **Soft Cap:** 10 BNB\n"
        "🏦 **Hard Cap:** 40 BNB\n"
        "🕒 **Timeline:** 06/03 12:00 PM - 06/03 12:10 PM\n"
        "📥 **Contribution:** 0.05 - 0.2 BNB\n"
        "📈 **Sale Rate:** 1 BNB = 3,000,000 Goats\n"
        "📈 **Listing Rate:** 1 BNB = 3,000,000 Goats\n"
        "💧 **Liquidity:** 51%\n"
        "🔒 **Lockup:** 210 days, 23 hours, 50 minutes, 25 seconds\n\n"
        "🌐 **Website** | **X(Twitter)** | **Telegram**\n\n"
        "@everyone **Join the Presale on CheesePad**\n"
        "🔗 https://www.cheesepad.ai/sale"
    )

    msg = NewMessage(TARGET_GROUP_CHAT_ID, "group", msg_text)
    msg.ParseMode = ModeRichText
    bot.Send(msg)

# 消息监听
update_config = NewUpdate(0)
update_config.Timeout = 60

for update in bot.GetUpdatesChan(update_config):
    if update.Message:
        chat_id = update.Message.Chat.ID
        chat_type = update.Message.Chat.Type
        text = (update.Message.Text or "").strip().lower()

        if text == "/check" or text == "check":
            reply = NewMessage(chat_id, chat_type, "🔍 正在查询当前预售项目，请稍等...")
            reply.ParseMode = ModeRichText
            bot.Send(reply)
            send_rich_alert()
            continue

        reply = NewMessage(chat_id, chat_type, "🤖 收到！输入 /check 可查看当前预售卡片效果～")
        reply.ParseMode = ModeRichText
        bot.Send(reply)
