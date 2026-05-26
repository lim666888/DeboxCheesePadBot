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

print("🚀 预售小助手机器人已启动（手动+自动查询当前预售）")

# ================== 检查当前所有活跃预售 ==================
def check_current_presales(manual=False):
    print("🔍 正在查询 CheesePad 当前活跃预售...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
            )
            page = browser.new_page()
            page.goto("https://www.cheesepad.ai/sale", wait_until="networkidle", timeout=60000)
            
            # 更宽松的选择器，适配当前页面
            cards = page.query_selector_all("div[class*='card'], div[class*='launchpad'], div[class*='project'], div[role='button']")
            
            active_projects = []
            for card in cards:
                try:
                    # 尝试多种可能的选择器
                    name_selectors = ["h3", ".name", "[class*='title']", "[class*='project-name']", "strong", "span"]
                    name = None
                    for sel in name_selectors:
                        elem = card.query_selector(sel)
                        if elem:
                            name = elem.inner_text().strip()
                            break
                    
                    status_selectors = ["span[class*='status']", ".badge", "[class*='tag']", "div[class*='status']"]
                    status = None
                    for sel in status_selectors:
                        elem = card.query_selector(sel)
                        if elem:
                            status = elem.inner_text().strip()
                            break
                    
                    if name and status and any(kw in status.lower() for kw in ["presale", "upcoming", "live", "sale", "launch"]):
                        link = "https://www.cheesepad.ai/sale"
                        active_projects.append({"name": name, "status": status, "link": link})
                except:
                    continue
            browser.close()

        if active_projects:
            print(f"✅ 发现 {len(active_projects)} 个活跃预售项目")
            msg_text = "@everyone 🔍 **CheesePad 当前活跃预售项目：**\n\n"
            for item in active_projects:
                msg_text += f"📌 **{item['name']}**\n🔥 状态：{item['status']}\n🔗 {item['link']}\n\n"
            msg_text += "快去看看有没有想参与的吧！🍀"
        else:
            print("✅ 当前暂无活跃预售项目")
            msg_text = "@everyone ✅ 当前暂无活跃预售项目（没有找到准备开始或正在预售的项目）"

        msg = NewMessage(TARGET_GROUP_CHAT_ID, "group", msg_text)
        msg.ParseMode = ModeRichText
        bot.Send(msg)

    except Exception as e:
        print("检查出错:", str(e)[:100])
        if manual:
            msg = NewMessage(TARGET_GROUP_CHAT_ID, "group", "@everyone ❌ 查询失败，请稍后再试")
            msg.ParseMode = ModeRichText
            bot.Send(msg)

# 自动检查线程
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
        text = (update.Message.Text or "").strip()

        print(f"收到消息: {text}")

        if text.lower() == "/check":
            reply = NewMessage(chat_id, chat_type, "🔍 正在查询当前所有活跃预售项目，请稍等...")
            reply.ParseMode = ModeRichText
            bot.Send(reply)
            check_current_presales(manual=True)
            continue

        # 普通回复
        reply = NewMessage(chat_id, chat_type, f"🤖 收到：{text}\n\n输入 /check 可查询当前所有活跃预售项目！")
        reply.ParseMode = ModeRichText
        bot.Send(reply)
