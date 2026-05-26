import os
import json
import time
import threading
from boxbotapi import NewBotAPI, NewMessage, NewUpdate, ModeRichText
from boxbotapi import configs as cfg
from playwright.sync_api import sync_playwright

os.environ["DEBOX_BOT_API_KEY"] = os.getenv("DEBOX_BOT_API_KEY")
os.environ["DEBOX_BOT_API_SECRET"] = os.getenv("DEBOX_BOT_API_SECRET")

TARGET_GROUP_CHAT_ID = "c8wm9ddj"
CHECK_INTERVAL = 300   # 自动检查间隔（秒），5分钟

bot = NewBotAPI(
    os.getenv("DEBOX_BOT_API_KEY"),
    os.getenv("DEBOX_BOT_API_SECRET")
)

cfg.Debug = False
cfg.MessageListener = True

print("🚀 预售小助手机器人已启动（自动+手动查询当前预售）")

# ================== 检查函数 ==================
def check_new_presales(manual=False):
    print("🔍 正在检查 CheesePad 当前预售...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
            )
            page = browser.new_page()
            page.goto("https://www.cheesepad.ai/sale", wait_until="networkidle", timeout=60000)
            page.wait_for_selector("div[class*='card'], div[class*='launchpad']", timeout=30000)
            
            cards = page.query_selector_all("div[class*='card'], div[class*='launchpad'], div[class*='project']")
            
            active_projects = []
            for card in cards:
                try:
                    name = card.query_selector("h3, .name, [class*='title']").inner_text().strip()
                    status = card.query_selector("span[class*='status'], .badge").inner_text().strip()
                    link = "https://www.cheesepad.ai/sale"
                    
                    if any(kw in (status or "").lower() for kw in ["presale", "upcoming", "live", "sale", "launch"]):
                        active_projects.append({"name": name, "status": status, "link": link})
                except:
                    continue
            browser.close()

        if active_projects:
            print(f"发现 {len(active_projects)} 个当前活跃预售项目")
            if manual:   # 手动查询时列出所有
                msg_text = "@everyone 🔍 **当前 CheesePad 活跃预售项目：**\n\n"
                for item in active_projects:
                    msg_text += f"📌 **{item['name']}**\n🔥 状态：{item['status']}\n🔗 {item['link']}\n\n"
                msg_text += "快去看看有没有想参与的吧！🍀"
            else:   # 自动模式只提醒新项目（保持原逻辑）
                # 这里保留你原来的新项目提醒逻辑，如果想简化也可以改
                msg_text = "@everyone 🚨 **发现新预售！**\n\n"
                for item in active_projects:
                    msg_text += f"📌 **{item['name']}** - {item['status']}\n🔗 {item['link']}\n\n"
                msg_text += "快去参与吧！🍀"
            
            msg = NewMessage(TARGET_GROUP_CHAT_ID, "group", msg_text)
            msg.ParseMode = ModeRichText
            bot.Send(msg)
        else:
            print("✅ 暂无活跃预售")
            if manual:
                msg = NewMessage(TARGET_GROUP_CHAT_ID, "group", "@everyone ✅ 当前暂无活跃预售项目")
                msg.ParseMode = ModeRichText
                bot.Send(msg)
    except Exception as e:
        print("检查出错（可忽略）:", str(e)[:100])

# ================== 自动线程 ==================
def monitor_thread():
    while True:
        check_new_presales(manual=False)
        time.sleep(CHECK_INTERVAL)

threading.Thread(target=monitor_thread, daemon=True).start()

# ================== 消息监听 ==================
update_config = NewUpdate(0)
update_config.Timeout = 60

for update in bot.GetUpdatesChan(update_config):
    if update.Message:
        chat_id = update.Message.Chat.ID
        chat_type = update.Message.Chat.Type
        text = (update.Message.Text or "").strip()

        print(f"收到消息: {text}")

        if text.lower() == "/check":
            reply = NewMessage(chat_id, chat_type, "🔍 正在查询当前所有活跃预售项目，请稍等...")
            reply.ParseMode = ModeRichText
            bot.Send(reply)
            check_new_presales(manual=True)
            continue

        # 普通回复
        reply = NewMessage(chat_id, chat_type, f"🤖 收到：{text}\n\n输入 /check 可查询当前所有活跃预售项目！")
        reply.ParseMode = ModeRichText
        bot.Send(reply)
