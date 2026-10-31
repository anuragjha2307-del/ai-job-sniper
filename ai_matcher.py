import re
import json
import logging
import urllib.request
from typing import Dict, Tuple

logger = logging.getLogger("JobSniper")

# Keywords that indicate Fresher / Entry Level / Internship (Gives high boost)
FRESHER_KEYWORDS = [
    "intern", "internship", "fresher", "freshers", "entry level", "entry-level",
    "junior", "jr.", "jr ", "trainee", "associate", "graduate", "0-1", "0-2",
    "0 years", "college", "student", "early career", "campus", "fellowship"
]

# Senior / High experience roles to penalize or skip
SENIOR_KEYWORDS = [
    "senior", "sr.", "sr ", "lead", "principal", "staff engineer", "architect",
    "director", "vp", "manager", "5+ years", "6+ years", "7+ years", "8+ years", "10+ years"
]

def clean_html(text: str) -> str:
    """Removes HTML tags and entities."""
    clean = re.sub(r'<[^>]+>', ' ', text)
    clean = re.sub(r'&[a-z]+;', ' ', clean)
    return " ".join(clean.split())

def calculate_match_score(job: Dict, target_roles: list, candidate_skills: list) -> Tuple[int, list]:
    """
    Calculates match percentage (0-100) prioritizing Freshers, 0 Years, and Internships.
    """
    title_raw = job.get("title", "")
    title_lower = title_raw.lower()
    desc_clean = clean_html(job.get("description", "")).lower()
    tags_str = " ".join([str(t).lower() for t in job.get("tags", [])])
    full_text = f"{title_lower} {tags_str} {desc_clean}"

    # 1. Seniority Check (Skip senior/lead jobs for 0-year candidate)
    if any(re.search(r'\b' + re.escape(sr) + r'\b', title_lower) for sr in ["senior", "lead", "principal", "staff", "architect", "director", "head"]):
        return 0, []

    # 2. Check Fresher / Entry / Internship Status
    is_fresher_friendly = False
    for fk in FRESHER_KEYWORDS:
        if fk in title_lower or fk in full_text:
            is_fresher_friendly = True
            break

    # 3. Role / Title Match (up to 40 points)
    title_score = 0
    for role in target_roles:
        r_clean = role.strip().lower()
        if not r_clean:
            continue
        if r_clean in title_lower:
            title_score = 40
            break
        
        # Check domain words (data analyst, analytics, python, machine learning, deep learning, nlp, computer vision, full stack, sde, intern)
        key_terms = [
            "data analyst", "analytics", "bi analyst", "business intelligence",
            "python", "machine learning", "deep learning", "nlp", "computer vision",
            "full stack", "fullstack", "sde", "intern", "developer", "engineer"
        ]
        matching_terms = [t for t in key_terms if t in title_lower and t in r_clean]
        if matching_terms:
            title_score = max(title_score, 25 + len(matching_terms) * 5)

    if title_score == 0:
        return 0, []

    # 4. Skill Overlap (up to 40 points)
    matched_skills = []
    # Map synonyms/acronyms for comprehensive tech & data analyst matching
    synonyms = {
        "sql": ["sql", "mysql", "postgresql", "sqlite", "tsql", "sql queries"],
        "data analyst": ["data analyst", "data analysis", "analytics", "bi", "reporting"],
        "data visualization": ["data visualization", "power bi", "tableau", "matplotlib", "seaborn", "dashboard", "dashboards", "data viz"],
        "pandas": ["pandas", "numpy", "data manipulation", "data wrangling", "data cleaning"],
        "excel": ["excel", "advanced excel", "spreadsheets", "vlookup"],
        "power bi": ["power bi", "powerbi", "dax"],
        "tableau": ["tableau"],
        "nlp": ["nlp", "npl", "natural language processing", "llm", "transformers"],
        "computer vision": ["computer vision", "cv", "opencv", "image processing", "vision"],
        "deep learning": ["deep learning", "pytorch", "tensorflow", "neural networks"],
        "machine learning": ["machine learning", "ml", "scikit-learn", "data science"],
        "full stack": ["full stack", "fullstack", "frontend", "backend", "web development"]
    }

    for skill in candidate_skills:
        s_clean = skill.strip().lower()
        if not s_clean:
            continue

        matched = False
        if s_clean in synonyms:
            if any(re.search(r'\b' + re.escape(syn) + r'\b', full_text) for syn in synonyms[s_clean]):
                matched = True
        else:
            if re.search(r'\b' + re.escape(s_clean) + r'\b', full_text):
                matched = True

        if matched:
            matched_skills.append(skill.strip())

    skill_score = min(40, len(matched_skills) * 8)

    # 5. Fresher / Internship Bonus (+20 points)
    fresher_bonus = 20 if is_fresher_friendly else 0

    total_score = min(100, title_score + skill_score + fresher_bonus)

    return total_score, matched_skills


def generate_cold_pitch(job: Dict, candidate_name: str, github_url: str, matched_skills: list, gemini_api_key: str = "") -> str:
    """Generates tailored cold pitch for Data Analyst / SDE / ML Fresher roles."""
    role = job.get("title", "Developer")
    company = job.get("company", "Team")
    role_lower = role.lower()

    # Dynamic skill selection based on role
    if "analyst" in role_lower or "analytics" in role_lower or "bi" in role_lower:
        top_skills = ", ".join(matched_skills[:4]) if matched_skills else "SQL, Python (Pandas/NumPy), Power BI, Tableau, and Excel data modeling"
        pitch_body = (
            f"As an analytical and detail-oriented early-career professional skilled in {top_skills}, "
            f"I specialize in transforming raw datasets into actionable dashboards, performing exploratory data analysis, and building clean SQL queries."
        )
    else:
        top_skills = ", ".join(matched_skills[:4]) if matched_skills else "Python, Machine Learning, Computer Vision, and Full Stack development"
        pitch_body = (
            f"As an early-career engineer proficient in {top_skills}, "
            f"I focus on writing clean, scalable code and building functional AI/ML & full-stack applications."
        )

    if gemini_api_key and len(gemini_api_key.strip()) > 10:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_api_key.strip()}"
            prompt = f"""
            Write a high-converting, 3-sentence cold application email from Fresher/Entry-Level candidate '{candidate_name}' to '{company}' for '{role}'.
            Candidate strengths: {top_skills}.
            Include GitHub/Portfolio: {github_url}.
            Tone: Enthusiastic, skilled, project-driven fresher with 0-year professional exp but strong hands-on building experience.
            Output ONLY the email text with Subject line.
            """
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:
            pass

    pitch = (
        f"Subject: Application: {role} (Entry-Level / Fresher) - {candidate_name}\n\n"
        f"Hi {company} Hiring Team,\n"
        f"I am writing to express my strong interest in the {role} role at {company}. "
        f"{pitch_body}\n\n"
        f"Projects & GitHub: {github_url}\n\n"
        f"I am excited to bring dedication, fresh perspective, and strong problem-solving skills to your team. I look forward to hearing from you.\n\n"
        f"Best regards,\n"
        f"{candidate_name}"
    )
    return pitch
