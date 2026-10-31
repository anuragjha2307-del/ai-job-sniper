import os
import sys
import time
import json
import logging
from datetime import datetime

# UTF-8 stdout on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from job_sources import get_all_live_jobs
from ai_matcher import calculate_match_score, generate_cold_pitch
from telegram_alert import send_job_alert

base_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(base_dir, "job_sniper.log")
seen_file = os.path.join(base_dir, "seen_jobs.json")

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding="utf-8")
    ]
)
logger = logging.getLogger("JobSniper")

def load_env(env_path: str = None) -> dict:
    if env_path is None:
        env_path = os.path.join(base_dir, ".env")
    config = {}
    if not os.path.exists(env_path):
        return config
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            config[k.strip()] = v.strip().strip('"').strip("'")
    return config

def load_seen_jobs() -> set:
    if os.path.exists(seen_file):
        try:
            with open(seen_file, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_seen_jobs(seen_set: set):
    try:
        # Keep maximum last 1000 IDs to avoid huge file size
        recent_ids = list(seen_set)[-1000:]
        with open(seen_file, "w", encoding="utf-8") as f:
            json.dump(recent_ids, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save seen jobs: {e}")

def run_scan_cycle(config: dict, seen_jobs: set, is_initial: bool = False, max_alerts_per_cycle: int = 3):
    bot_token = config.get("TELEGRAM_BOT_TOKEN")
    chat_id = config.get("TELEGRAM_CHAT_ID")
    min_score = int(config.get("MIN_MATCH_SCORE", 65))
    name = config.get("CANDIDATE_NAME", "Anurag Jha")
    github = config.get("CANDIDATE_GITHUB", "")
    gemini_key = config.get("GEMINI_API_KEY", "")

    raw_roles = config.get("TARGET_ROLES", "Android Developer, SDE, Python Developer")
    target_roles = [r.strip() for r in raw_roles.split(",") if r.strip()]

    raw_skills = config.get("CANDIDATE_SKILLS", "Android, Kotlin, Jetpack Compose, Python, SDE")
    candidate_skills = [s.strip() for s in raw_skills.split(",") if s.strip()]

    logger.info("📡 Scanning live tech job boards (Remotive, Jobicy, Arbeitnow)...")
    live_jobs = get_all_live_jobs()
    logger.info(f"Total live jobs fetched: {len(live_jobs)}")

    new_matches = []

    for job in live_jobs:
        job_id = job["id"]
        if job_id in seen_jobs:
            continue

        score, matched_skills = calculate_match_score(job, target_roles, candidate_skills)
        seen_jobs.add(job_id)

        if score >= min_score:
            new_matches.append((score, matched_skills, job))

    # Sort matches by highest score first
    new_matches.sort(key=lambda x: x[0], reverse=True)

    logger.info(f"High-match roles found: {len(new_matches)}")

    # Send alerts (limit to top matches per cycle so user isn't spammed with 50 messages at once)
    alerts_to_send = new_matches[:max_alerts_per_cycle]
    for score, skills, job in alerts_to_send:
        logger.info(f"🚀 Sending alert for: {job['title']} @ {job['company']} (Score: {score}%)")
        pitch = generate_cold_pitch(job, name, github, skills, gemini_key)
        send_job_alert(bot_token, chat_id, job, score, skills, pitch)
        time.sleep(2)  # Short pause between Telegram messages

    save_seen_jobs(seen_jobs)


def main():
    print("""
===================================================================
      🎯 24x7 AI JOB & INTERNSHIP SNIPER INITIALIZED
===================================================================
    """)
    config = load_env()
    bot_token = config.get("TELEGRAM_BOT_TOKEN")
    chat_id = config.get("TELEGRAM_CHAT_ID")
    interval = int(config.get("SCAN_INTERVAL_SECONDS", 600))

    if not bot_token or not chat_id:
        logger.error("Please configure TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env!")
        return

    logger.info(f"Candidate: {config.get('CANDIDATE_NAME')}")
    logger.info(f"Target Roles: {config.get('TARGET_ROLES')}")
    logger.info(f"Scan Interval: {interval} seconds")
    logger.info("AI Sniper is now standing guard. Press Ctrl+C to terminate.\n")

    seen_jobs = load_seen_jobs()

    # Initial scan
    run_scan_cycle(config, seen_jobs, is_initial=(len(seen_jobs) == 0))

    while True:
        try:
            logger.info(f"Sleeping for {interval}s until next scan cycle...")
            time.sleep(interval)
            run_scan_cycle(config, seen_jobs)
        except KeyboardInterrupt:
            logger.info("Shutting down AI Job Sniper gracefully...")
            break
        except Exception as e:
            logger.error(f"Unexpected error in sniper loop: {e}", exc_info=True)
            time.sleep(30)

if __name__ == "__main__":
    main()

