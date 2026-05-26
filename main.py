import os
import time
import threading
from boxbotapi import NewBotAPI, NewMessage, NewUpdate, ModeRichText
from boxbotapi import configs as cfg
from playwright.sync_api import sync_playwright

os.environ["DEBOX_BOT_API_KEY"] = os.getenv("DEBOX_BOT_API_KEY")
os.environ["DEBOX_BOT_API_SECRET"] = os.getenv("DEBOX_BOT_API_SECRET")

TARGET_GROUP_CHAT_ID = "c8wm9ddj"
CHECK_INTERVAL = 300   # 自动检查间隔（5分钟）

bot = NewBotAPI(
    os.getenv("DEBOX_BOT_API_KEY"),
    os.getenv("DEBOX_BOT_API_SECRET")
)

cfg.Debug = False
cfg.MessageListener = True

print("🚀 预售小助手机器人已启动（加强版查询）")

def check_current_presales(manual=False):
    print("🔍 正在查询 CheesePad 当前活跃预售...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
            )
            page = browser.new_page()
            page.goto("https://www.cheesepad.ai/sale", wait_until="networkidle", timeout=90000)
            
            # 超级宽松的选择器，适配当前和未来页面变化
            cards = page.query_selector_all("div")
            
            active_projects = []
            for card in cards:
                try:
                    text = card.inner_text().strip()
                    if len(text) < 5:
                        continue
                    
                    # 提取可能的项目名称和状态
                    if any(kw in text.lower() for kw in ["presale", "upcoming", "live", "sale", "launch"]):
                        name = text.split("\n")[0].strip() if "\n" in text else text[:30]
                        status = "活跃预售"
                        link = "https://www.cheesepad.ai/sale"
                        active_projects.append({"name": name, "status": status, "link": link})
                except:
                    continue
            
            browser.close()

        print(f"找到 {len(active_projects)} 个可能活跃项目")

        if active_projects:
            msg_text = "@everyone 🔍 **CheesePad 当前活跃预售项目：**\n\n"
            for item in active_projects[:10]:   # 最多显示10个
                msg_text += f"📌 **{item['name']}**\n🔥 状态：{item['status']}\n🔗 {item['link']}\n\n"
            msg_text += "快去参与吧！🍀"
        else:
            msg_text = "@everyone ✅ 当前暂无活跃预售项目（页面上没有找到准备开始或正在预售的项目）"

        msg = NewMessage(TARGET_GROUP_CHAT_ID, "group", msg_text)
        msg.ParseMode = ModeRichText
        bot.Send(msg)

    except Exception as e:
        print("检查出错:", str(e)[:150])
        if manual:
            msg = NewMessage(TARGET_GROUP_CHAT_ID, "group", "@everyone ❌ 查询失败，请稍后再试")
            msg.ParseMode = ModeRichText
            bot.Send(msg)

# 自动检查
def monitor_thread():
    while True:
        check_current_presales(manual=False)
        time.sleep(CHECK_INTERVAL)

threading.Thread(target=monitor_thread, daemon=True).start()

# 消息监听
update_config = NewUpdate(0)
update_config.Timeout = 60

for update in bot.GetUpdatesChan(update_config):
    if update.Message:
        chat_id = update.Message.Chat.ID
        chat_type = update.Message.Chat.Type
        text = (update.Message.Text or "").strip().lower()

        if text == "/check":
            reply = NewMessage(chat_id, chat_type, "🔍 正在查询当前所有活跃预售项目，请稍等...")
            reply.ParseMode = ModeRichText
            bot.Send(reply)
            check_current_presales(manual=True)
            continue

        reply = NewMessage(chat_id, chat_type, f"🤖 收到：{text}\n\n输入 /check 可查询当前所有活跃预售项目！")
        reply.ParseMode = ModeRichText
        bot.Send(reply)
