"""Private single-owner Telegram transport. Never logs bodies, tokens or URLs."""
import json
import urllib.request


class Telegram:
    def __init__(self, token):
        self.token = token

    def call(self, method, **payload):
        request = urllib.request.Request(
            f"https://api.telegram.org/bot{self.token}/{method}",
            data=json.dumps(payload).encode(), headers={"Content-Type":"application/json"})
        with urllib.request.urlopen(request, timeout=40) as response:
            result = json.load(response)
        if not result.get("ok"):
            raise RuntimeError("Telegram rejected request")
        return result["result"]

    def send(self, owner, text):
        return self.call("sendMessage", chat_id=owner, text=text)


HELP = """پارس تریدر ۰.۱ — نسخه پژوهشی؛ معامله واقعی غیرفعال است.
/plan انتخاب نوع حساب
/balance 10000 ثبت سرمایه آزمایشی
/signals فعال‌کردن پایش سیگنال
/pause توقف سیگنال جدید
/status وضعیت
/recent آخرین ستاپ‌ها
/live وضعیت اجرای واقعی
رمز متاتریدر را در پیام ارسال نکنید."""


def handle(message, owner, store):
    if message.get("from",{}).get("id") != owner or message.get("chat",{}).get("id") != owner or message.get("chat",{}).get("type") != "private":
        return None
    text = message.get("text", "").strip()
    pieces = text.split()
    cmd = pieces[0].split("@")[0] if pieces else ""
    if cmd in ("/start","/help"):
        return HELP
    if cmd == "/plan":
        return "نوع حساب را انتخاب کن:\n/one تک‌مرحله‌ای\n/two دومرحله‌ای\n/pro پروتریدر\nانتخاب پلن به معنی تأیید قوانین یا مجوز EA نیست."
    if cmd in ("/one","/two","/pro"):
        store.put("plan", cmd[1:])
        return "پلن ثبت شد. سرمایه آزمایشی را با /balance 10000 ثبت کن."
    if cmd == "/balance":
        try:
            amount = float(pieces[1])
            if not 0 < amount <= 1e9:
                raise ValueError()
        except (IndexError,ValueError):
            return "نمونه صحیح: /balance 10000"
        store.put("paper_balance", amount)
        return "سرمایه آزمایشی ثبت شد؛ موجودی واقعی حساب تغییر نکرد."
    if cmd == "/signals":
        store.put("paused", False)
        return "پایش سیگنال فعال شد؛ نیازمند قیمت تازه و تقویم خبر معتبر است."
    if cmd == "/pause":
        store.put("paused", True)
        return "سیگنال جدید متوقف شد. این دستور معامله‌ای را نمی‌بندد."
    if cmd == "/live":
        return "معامله واقعی در نسخه ۰.۱ پیاده‌سازی نشده است. فرم دریافت رمز نیز هنوز وجود ندارد."
    if cmd == "/status":
        return f"نسخه پژوهشی ۰.۱\nپلن: {store.get('plan','انتخاب نشده')}\nسرمایه آزمایشی: {store.get('paper_balance','ثبت نشده')}\nتوقف: {store.get('paused',True)}\nآخرین پایش: {store.get('scan_status','انجام نشده')}\nاجرای واقعی: غیرفعال\nاخبار خودکار و AI: هنوز متصل نیستند"
    if cmd == "/recent":
        rows = store.recent()
        return "\n\n".join(r["text"] for r in rows) if rows else "هنوز ستاپی ثبت نشده."
    return "دستور ناشناخته. /help\nرمز یا توکن را در چت ارسال نکن."
