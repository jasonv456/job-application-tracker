"""Job Match: compare a candidate's skills with a job's required skills.

Pure functions with no Flask/DB dependency so they are easy to unit test.

match % = (number of required skills the candidate has) / (number of required skills) * 100
"""
import json
import re

# Common abbreviations/spellings mapped to one canonical form so that
# "JS" matches "JavaScript", "k8s" matches "Kubernetes", etc.
ALIASES = {
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "python3": "python",
    "postgres": "postgresql",
    "k8s": "kubernetes",
    "ml": "machine learning",
    "amazon web services": "aws",
    "ci cd": "ci/cd",
    "cicd": "ci/cd",
    "rest": "rest apis",
    "rest api": "rest apis",
    "html5": "html",
    "css3": "css",
    "ms excel": "excel",
    "microsoft excel": "excel",
}


def normalize_skill(skill):
    """Lower-case, trim and collapse whitespace, then apply aliases."""
    key = re.sub(r"\s+", " ", str(skill).strip().lower())
    return ALIASES.get(key, key)


def parse_skills(raw):
    """Turn user input into a clean, de-duplicated list of skills.

    Accepts a comma/semicolon/newline separated string, a list, a JSON array
    string, or None. Original capitalisation of the first occurrence is kept.
    """
    if raw is None:
        return []
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8")
    if isinstance(raw, str):
        text = raw.strip()
        if text.startswith("["):
            try:
                raw = json.loads(text)
            except ValueError:
                raw = re.split(r"[,;\n]", text.strip("[]"))
        else:
            raw = re.split(r"[,;\n]", text)
    seen, result = set(), []
    for item in raw:
        name = str(item).strip().strip('"').strip()
        if not name:
            continue
        key = normalize_skill(name)
        if key not in seen:
            seen.add(key)
            result.append(name)
    return result


def calculate_match(user_skills, required_skills):
    """Return a dict with match percentage plus matched and missing skills.

    If a job lists no requirements the percentage is None (not measurable)
    rather than 0% or 100%, so it is not misleadingly ranked.
    """
    required = parse_skills(required_skills)
    user_keys = {normalize_skill(s) for s in parse_skills(user_skills)}
    matched = [s for s in required if normalize_skill(s) in user_keys]
    missing = [s for s in required if normalize_skill(s) not in user_keys]
    percent = round(len(matched) / len(required) * 100) if required else None
    return {
        "percent": percent,
        "matched": matched,
        "missing": missing,
        "required_count": len(required),
    }


def match_level(percent):
    """Bucket a percentage into a label used for colour-coding in the UI."""
    if percent is None:
        return "none"
    if percent >= 75:
        return "high"
    if percent >= 50:
        return "medium"
    return "low"


def rank_jobs(user_skills, jobs, min_percent=0):
    """Attach match info to each job dict and sort best match first.

    Jobs with no requirements are dropped, as are jobs below min_percent.
    """
    results = []
    for job in jobs:
        info = calculate_match(user_skills, job.get("requirements"))
        if info["percent"] is None or info["percent"] < min_percent:
            continue
        results.append({**job, "match": info, "level": match_level(info["percent"])})
    results.sort(key=lambda j: (-j["match"]["percent"], -len(j["match"]["matched"]), j["job_title"]))
    return results
