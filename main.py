import os
import json
import time
import threading
from boxbotapi import NewBotAPI, NewMessage, NewUpdate, ModeRichText
from boxbotapi import configs as cfg
from playwright.sync_api import sync_playwright

# ================== 配置 ==================
os.environ["DEBOX_BOT_API_KEY"] = os.getenv("DEBOX_BOT_API_KEY")
os.environ["DEBOX_BOT_API_SECRET"] = os.getenv("DEBOX_BOT_API_SECRET")

TARGET_GROUP_CHAT_ID = "c8wm9ddj"
CHECK_INTERVAL = 300

SEEN_FILE = "seen_presales.json"

bot = NewBotAPI(
    os.getenv("DEBOX_BOT_API_KEY"),
    os.getenv("DEBOX_BOT_API_SECRET")
)

cfg.Debug = False
cfg.MessageListener = True

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

seen_presales = load_seen()

def save_seen():
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen_presales), f, ensure_ascii=False)

def check_new_presales():
    global seen_presales
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
                        key = f"{name}-{status}"
                        if key not in seen_presales:
                            seen_presales.add(key)
                            new_found.append({"name": name, "status": status, "link": link})
                except:
                    continue
            browser.close()

        if new_found:
            print(f"🚨 发现 {len(new_found)} 个新预售！")
            for item in new_found:
                msg = NewMessage(TARGET_GROUP_CHAT_ID, "group", f"🚨 **CheesePad 新预售上线！**\n\n📌 项目：**{item['name']}**\n🔥 状态：{item['status']}\n🔗 链接：{item['link']}\n\n快去参与吧！🍀")
                msg.ParseMode = ModeRichText
                bot.Send(msg)
            save_seen()
        else:
            print("✅ 暂无新预售")
    except Exception as e:
        print("检查出错（可忽略）:", str(e)[:100])

def monitor_thread():
    while True:
        check_new_presales()
        time.sleep(CHECK_INTERVAL)

print("🚀 预售小助手机器人已启动（CheesePad 监控已开启）")

threading.Thread(target=monitor_thread, daemon=True).start()

update_config = NewUpdate(0)
update_config.Timeout = 60

for update in bot.GetUpdatesChan(update_config):
    if update.Message:
        chat_id = update.Message.Chat.ID
        chat_type = update.Message.Chat.Type
        text = update.Message.Text or ""
        print(f"收到消息: {text}")
        reply = NewMessage(chat_id, chat_type, f"🤖 收到：{text}\nCheesePad监控运行中...")
        reply.ParseMode = ModeRichText
        bot.Send(reply)
