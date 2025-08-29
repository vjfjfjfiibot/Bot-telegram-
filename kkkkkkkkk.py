#!/usr/bin/env python3
"""
forwarder_multi.py
- يدعم أكثر من (قناة مصدر -> قناة هدف) في نفس الوقت
- لكل زوج بروتوكول فلترة خاص به
- بدون "Forwarded from"
- يدعم النصوص + الميديا + الألبومات
"""

import asyncio
import logging
import re
from telethon import TelegramClient, events, errors

# ---------- إعدادات المستخدم ----------
API_ID = 20291391
API_HASH = "c6f7cc55b7c4ec329b2d3cf543c6e004"
SESSION_NAME = "forwarder_session"

# تعريف القنوات والبروتوكولات
CHANNEL_PAIRS = [
    {
        "source": -1001012483012,   # القناة الأولى (مصدر)
        "target": -1002888724896,   # القناة الأولى (هدف)
        "banned_patterns": {
            r"https://t.me/iraqedu": "https://t.me/SAYE44G",
            r"داعش": "",
        }
    },
    {
        "source": -1001926324129,   # القناة الثانية (مصدر)
        "target": -1002281224169,   # القناة الثانية (هدف)
        "banned_patterns": {}
    },
    {
        "source": -1001234567890,   # القناة الثالثة (مصدر)
        "target": -1001132278525,   # القناة الثالثة (هدف)
        "banned_patterns": {}
    },
    {
        "source": -1001000151090,   # القناة الرابعة (مصدر)
        "target": -1002539531983,   # القناة الرابعة (هدف)
        "banned_patterns": {
            r"Https://t.me/edu2iq": "https://t.me/VDV2V"
        }
    },
    {
        "source": -1001573409984,   # القناة الخامسة (مصدر)
        "target": -1002555086506,   # القناة الخامسة (هدف)
        "banned_patterns": {
            r"http://t.me/iRAQm": "https://t.me/derfftv"
        }
    },
    {
        "source": -1002927804963,   # 🚀 القناة السادسة (مصدر)
        "target": -1002549347039,   # 🚀 القناة السادسة (هدف)
        "banned_patterns": {
            r"اعلان": "[مخفي إعلان]",
            r"link": "[رابط محجوب]"
        }
    }
]
# --------------------------------------

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("forwarder_multi")

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# لتجميع رسائل الألبومات حسب كل قناة
albums_buffer = {}

def filter_text(text: str, patterns: dict) -> str:
    """استبدال الكلمات/الأنماط المحظورة في النص حسب بروتوكول كل قناة"""
    if not text:
        return text
    result = text
    for pattern, replacement in patterns.items():
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result


async def main():
    await client.start()
    me = await client.get_me()
    logger.info(f"✅ سجل الدخول: {me.first_name} (id={me.id})")

    # نولّد handler لكل زوج مصدر-هدف
    for pair in CHANNEL_PAIRS:
        source = pair["source"]
        target = pair["target"]
        patterns = pair["banned_patterns"]

        @client.on(events.NewMessage(chats=source))
        async def handler(event, src=source, tgt=target, proto=patterns):
            msg = event.message
            gid = msg.grouped_id

            try:
                if gid:  # ألبوم
                    key = (src, gid)
                    if key not in albums_buffer:
                        albums_buffer[key] = []
                    
                    albums_buffer[key].append(msg)
                    await asyncio.sleep(2)

                    if key in albums_buffer:
                        group = albums_buffer.pop(key)
                        media_list = [m for m in group if m.media]
                        caption = filter_text(group[0].text or "", proto)

                        await client.send_file(
                            tgt,
                            [m.media for m in media_list],
                            caption=caption,
                            parse_mode="html"
                        )
                        logger.info(f"✅ أُرسل ألبوم ({len(media_list)} عناصر) من {src} -> {tgt}")

                else:
                    if msg.media:
                        await client.send_file(
                            tgt,
                            msg.media,
                            caption=filter_text(msg.text or "", proto),
                            parse_mode="html"
                        )
                    else:
                        await client.send_message(
                            tgt,
                            filter_text(msg.text, proto),
                            parse_mode="html"
                        )

                    logger.info(f"✅ نُسخت رسالة id={msg.id} من {src} -> {tgt}")

            except errors.FloodWaitError as fw:
                wait = fw.seconds + 1
                logger.warning(f"⏳ FloodWait: الانتظار {wait} ثانية...")
                await asyncio.sleep(wait)
            except Exception as e:
                logger.error(f"❌ فشل: {e}")

    logger.info("🚀 مستعد للاستماع لكل القنوات...")
    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 تم الإنهاء من طرفك.")