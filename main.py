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
CHECK_INTERVAL = 300   # 每5分钟自动检查一次（想改成3分钟就改成180）

bot = NewBotAPI(
    os.getenv("DEBOX_BOT_API_KEY"),
    os.getenv("DEBOX_BOT_API_SECRET")
)

cfg.Debug = False
cfg.MessageListener = True

print("🚀 预售小助手机器人已启动（自动+手动混合模式）")

def check_new_presales():
    print("🔍 正在检查 CheesePad 新预售...")
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
            
            new_found = []
            for card in cards:
                try:
                    name = card.query_selector("h3, .name, [class*='title']").inner_text().strip()
                    status = card.query_selector("span[class*='status'], .badge").inner_text().strip()
                    link = "https://www.cheesepad.ai/sale"
                    
                    if any(kw in (status or "").lower() for kw in ["presale", "upcoming", "live", "sale", "launch"]):
                        new_found.append({"name": name, "status": status, "link": link})
                except:
                    continue
            browser.close()

        if new_found:
            print(f"🚨 发现 {len(new_found)} 个新预售！")
            for item in new_found:
                msg = NewMessage(TARGET_GROUP_CHAT_ID, "group",
                    f"🚨 **CheesePad 新预售上线！**\n\n"
                    f"📌 项目：**{item['name']}**\n"
                    f"🔥 状态：{item['status']}\n"
                    f"🔗 链接：{item['link']}\n\n"
                    f"快去参与吧！🍀")
                msg.ParseMode = ModeRichText
                bot.Send(msg)
        else:
            print("✅ 暂无新预售")
    except Exception as e:
        print("检查出错（可忽略）:", str(e)[:100])

# 自动检查线程
def monitor_thread():
    while True:
        check_new_presales()
        time.sleep(CHECK_INTERVAL)

threading.Thread(target=monitor_thread, daemon=True).start()

# 消息监听
update_config = NewUpdate(0)
update_config.Timeout = 60

for update in bot.GetUpdatesChan(update_config):
    if update.Message:
        chat_id = update.Message.Chat.ID
        chat_type = update.Message.Chat.Type
        text = (update.Message.Text or "").strip()

        print(f"收到消息: {text}")

        if text.lower() == "/check":
            reply = NewMessage(chat_id, chat_type, "🔍 正在手动检查 CheesePad 新预售，请稍等...")
            reply.ParseMode = ModeRichText
            bot.Send(reply)
            check_new_presales()
            continue

        # 普通回复
        reply = NewMessage(chat_id, chat_type, f"🤖 收到：{text}\n\n输入 /check 可立即检查新预售！")
        reply.ParseMode = ModeRichText
        bot.Send(reply)
