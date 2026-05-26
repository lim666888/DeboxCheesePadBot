import os
import time
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

print("🚀 预售小助手机器人已启动（稳定版）")

# ================== 手动查询 ==================
def manual_check():
    msg = NewMessage(
        TARGET_GROUP_CHAT_ID, "group",
        "@everyone 🔍 **CheesePad 当前预售查询**\n\n"
        "目前抓取还有点问题，我正在优化中...\n\n"
        "你可以直接点击下面链接查看最新项目：\n"
        "🔗 https://www.cheesepad.ai/sale\n\n"
        "输入 /check 可让我再尝试一次！🍀"
    )
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

        print(f"收到消息: {text}")

        if text == "/check" or text == "check":
            reply = NewMessage(chat_id, chat_type, "🔍 正在查询当前预售项目，请稍等...")
            reply.ParseMode = ModeRichText
            bot.Send(reply)
            manual_check()
            continue

        # 普通回复
        reply = NewMessage(chat_id, chat_type, f"🤖 收到：{text}\n\n输入 /check 可查询 CheesePad 当前预售项目！")
        reply.ParseMode = ModeRichText
        bot.Send(reply)
