import json
import urllib.request
import urllib.error
import logging
from typing import List, Dict

logger = logging.getLogger("JobSniper")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def fetch_remotive_jobs() -> List[Dict]:
    """Fetches real-time tech jobs from Remotive API."""
    jobs = []
    url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=40"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for item in data.get("jobs", []):
                jobs.append({
                    "id": f"remotive_{item.get('id')}",
                    "title": item.get("title", ""),
                    "company": item.get("company_name", "Unknown"),
                    "location": item.get("candidate_required_location", "Remote / Anywhere"),
                    "url": item.get("url", ""),
                    "tags": item.get("tags", []),
                    "description": item.get("description", "")[:1200],
                    "source": "Remotive"
                })
        logger.info(f"Fetched {len(jobs)} jobs from Remotive.")
    except Exception as e:
        logger.warning(f"Remotive fetch error: {e}")
    return jobs


def fetch_jobicy_jobs() -> List[Dict]:
    """Fetches real-time tech jobs from Jobicy API."""
    jobs = []
    url = "https://jobicy.com/api/v2/remote-jobs?count=40&tag=software-dev"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for item in data.get("jobs", []):
                jobs.append({
                    "id": f"jobicy_{item.get('id')}",
                    "title": item.get("jobTitle", ""),
                    "company": item.get("companyName", "Unknown"),
                    "location": item.get("jobGeo", "Remote"),
                    "url": item.get("url", ""),
                    "tags": item.get("jobSkills", []),
                    "description": item.get("jobDescription", "")[:1200],
                    "source": "Jobicy"
                })
        logger.info(f"Fetched {len(jobs)} jobs from Jobicy.")
    except Exception as e:
        logger.warning(f"Jobicy fetch error: {e}")
    return jobs


def fetch_arbeitnow_jobs() -> List[Dict]:
    """Fetches tech jobs from Arbeitnow API."""
    jobs = []
    url = "https://www.arbeitnow.com/api/job-board-api"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for item in data.get("data", []):
                jobs.append({
                    "id": f"arbeit_{item.get('slug')}",
                    "title": item.get("title", ""),
                    "company": item.get("company_name", "Unknown"),
                    "location": item.get("location", "Remote"),
                    "url": item.get("url", ""),
                    "tags": item.get("tags", []),
                    "description": item.get("description", "")[:1200],
                    "source": "Arbeitnow"
                })
        logger.info(f"Fetched {len(jobs)} jobs from Arbeitnow.")
    except Exception as e:
        logger.warning(f"Arbeitnow fetch error: {e}")
    return jobs


def get_all_live_jobs() -> List[Dict]:
    """Aggregates jobs across all sources and removes duplicates."""
    all_jobs = []
    seen_urls = set()

    sources = [fetch_remotive_jobs, fetch_jobicy_jobs, fetch_arbeitnow_jobs]
    for fetcher in sources:
        try:
            results = fetcher()
            for j in results:
                if j["url"] and j["url"] not in seen_urls:
                    seen_urls.add(j["url"])
                    all_jobs.append(j)
        except Exception as e:
            logger.error(f"Error executing {fetcher.__name__}: {e}")

    return all_jobs

