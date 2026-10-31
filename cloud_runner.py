import os
import sys
import json
import logging
from datetime import datetime

# UTF-8 stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from job_sources import get_all_live_jobs
from ai_matcher import calculate_match_score, generate_cold_pitch
from telegram_alert import send_job_alert
from agent import load_env, load_seen_jobs, save_seen_jobs

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s"
)
logger = logging.getLogger("GitHubActionSniper")

def main():
    print("""
===================================================================
     ☁️ GITHUB ACTIONS 24x7 CLOUD AI JOB SNIPER RUNNER
===================================================================
    """)
    config = load_env()

    # Cloud environment variables take top priority
    for key in [
        "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "CANDIDATE_NAME", 
        "CANDIDATE_GITHUB", "CANDIDATE_SKILLS", "TARGET_ROLES", 
        "MIN_MATCH_SCORE", "GEMINI_API_KEY"
    ]:
        if os.environ.get(key):
            config[key] = os.environ.get(key)

    bot_token = config.get("TELEGRAM_BOT_TOKEN")
    chat_id = config.get("TELEGRAM_CHAT_ID")
    min_score = int(config.get("MIN_MATCH_SCORE", 55))
    name = config.get("CANDIDATE_NAME", "Anurag Jha")
    github = config.get("CANDIDATE_GITHUB", "")
    gemini_key = config.get("GEMINI_API_KEY", "")

    raw_roles = config.get("TARGET_ROLES", "Data Analyst, Python Developer, Machine Learning Intern, AI Engineer, Full Stack, SDE")
    target_roles = [r.strip() for r in raw_roles.split(",") if r.strip()]

    raw_skills = config.get("CANDIDATE_SKILLS", "SQL, Python, Pandas, NumPy, Power BI, Tableau, Excel, Machine Learning, Deep Learning, NLP, Computer Vision, SDE, Full Stack")
    candidate_skills = [s.strip() for s in raw_skills.split(",") if s.strip()]

    logger.info(f"Candidate: {name}")
    logger.info(f"Target Roles count: {len(target_roles)}")
    logger.info(f"Target Skills count: {len(candidate_skills)}")

    seen_jobs = load_seen_jobs()
    logger.info(f"Previously seen jobs in database: {len(seen_jobs)}")

    logger.info("📡 Scanning live tech job boards from GitHub Cloud...")
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

    new_matches.sort(key=lambda x: x[0], reverse=True)
    logger.info(f"New high-match fresher/entry roles found: {len(new_matches)}")

    # Send alerts for top new matches (max 3 per cron run to avoid spam)
    alerts_to_send = new_matches[:3]
    for score, skills, job in alerts_to_send:
        logger.info(f"🚀 Dispatching alert: {job['title']} @ {job['company']} (Score: {score}%)")
        pitch = generate_cold_pitch(job, name, github, skills, gemini_key)
        send_job_alert(bot_token, chat_id, job, score, skills, pitch)

    save_seen_jobs(seen_jobs)
    logger.info("✅ GitHub Actions Cloud cycle completed successfully.")

if __name__ == "__main__":
    main()
