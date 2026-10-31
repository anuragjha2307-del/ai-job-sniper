import json
import urllib.request
import urllib.error
import logging
from datetime import datetime

logger = logging.getLogger("JobSniper")

def send_job_alert(bot_token: str, chat_id: str, job: dict, match_score: int, matched_skills: list, cold_pitch: str) -> bool:
    """Sends a rich Telegram message with the job details and pre-written pitch."""
    if not bot_token or not chat_id:
        logger.error("Missing Telegram bot_token or chat_id!")
        return False

    score_badge = "🟢" if match_score >= 80 else ("🟡" if match_score >= 65 else "⚪")
    skills_formatted = ", ".join([f"`{s}`" for s in matched_skills[:5]]) if matched_skills else "`General SDE Skills`"
    
    # Escape Markdown characters in title and company
    title = job.get("title", "").replace("*", "").replace("_", "")
    company = job.get("company", "").replace("*", "").replace("_", "")
    location = job.get("location", "Remote").replace("*", "").replace("_", "")
    apply_url = job.get("url", "")
    source = job.get("source", "Web")

    message = (
        f"🎯 *24x7 JOB SNIPER: HIGH MATCH!* 🚀\n\n"
        f"💼 *Role:* {title}\n"
        f"🏢 *Company:* {company}\n"
        f"📍 *Location:* {location}\n"
        f"📊 *Match Score:* {score_badge} *{match_score}%*\n"
        f"🏷️ *Matched Skills:* {skills_formatted}\n"
        f"🌐 *Source:* {source}\n\n"
        f"🔗 *Apply Link:* [Click Here to Open & Apply]({apply_url})\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"✍️ *Pre-Written Cold Email Pitch:*\n"
        f"```\n{cold_pitch}\n```\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏰ _Detected: {datetime.now().strftime('%d %b %Y, %I:%M %p')}_"
    )

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            if res.get("ok"):
                logger.info(f"✅ Alert sent for: {title} @ {company}")
                return True
    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {e}")
    return False

