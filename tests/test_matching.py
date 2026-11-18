"""Unit tests for the Job Match calculation (no database needed)."""
from matching import calculate_match, match_level, normalize_skill, parse_skills, rank_jobs


def test_parse_skills_from_comma_string_trims_and_dedupes():
    assert parse_skills(" Python, sql ,  ,Python, Git ") == ["Python", "sql", "Git"]


def test_parse_skills_from_json_string_and_list():
    assert parse_skills('["Python", "SQL"]') == ["Python", "SQL"]
    assert parse_skills(["A", "a", "B"]) == ["A", "B"]
    assert parse_skills(None) == []
    assert parse_skills("") == []


def test_parse_skills_accepts_semicolons_and_newlines():
    assert parse_skills("Python;SQL\nGit") == ["Python", "SQL", "Git"]


def test_normalize_skill_handles_case_whitespace_and_aliases():
    assert normalize_skill("  JavaScript ") == "javascript"
    assert normalize_skill("JS") == "javascript"
    assert normalize_skill("k8s") == "kubernetes"
    assert normalize_skill("Machine   Learning") == "machine learning"


def test_full_match_is_100_percent():
    r = calculate_match("python, sql", ["Python", "SQL"])
    assert r["percent"] == 100
    assert r["missing"] == []


def test_partial_match_percentage_and_lists():
    r = calculate_match(["Python", "Git"], ["Python", "SQL", "Git", "Docker"])
    assert r["percent"] == 50
    assert r["matched"] == ["Python", "Git"]
    assert r["missing"] == ["SQL", "Docker"]
    assert r["required_count"] == 4


def test_percentage_is_rounded():
    assert calculate_match(["a"], ["a", "b", "c"])["percent"] == 33
    assert calculate_match(["a", "b"], ["a", "b", "c"])["percent"] == 67


def test_no_overlap_is_zero():
    assert calculate_match(["Cooking"], ["Python"])["percent"] == 0


def test_alias_counts_as_match():
    assert calculate_match("JS, k8s", ["JavaScript", "Kubernetes"])["percent"] == 100


def test_extra_user_skills_do_not_lower_score():
    assert calculate_match("Python, SQL, Rust, Go, C++", ["Python", "SQL"])["percent"] == 100


def test_job_without_requirements_is_not_scored():
    r = calculate_match(["Python"], None)
    assert r["percent"] is None
    assert match_level(r["percent"]) == "none"


def test_match_levels():
    assert match_level(100) == "high"
    assert match_level(75) == "high"
    assert match_level(50) == "medium"
    assert match_level(49) == "low"
    assert match_level(0) == "low"


def test_rank_jobs_sorts_best_first_filters_and_skips_unscored():
    jobs = [
        {"job_title": "A", "requirements": '["Python", "SQL", "Git", "Docker"]'},  # 50%
        {"job_title": "B", "requirements": '["Python"]'},                          # 100%
        {"job_title": "C", "requirements": '["Java"]'},                            # 0%
        {"job_title": "D", "requirements": None},                                  # unscored
    ]
    ranked = rank_jobs("python, sql", jobs)
    assert [j["job_title"] for j in ranked] == ["B", "A", "C"]
    assert [j["match"]["percent"] for j in ranked] == [100, 50, 0]
    assert [j["job_title"] for j in rank_jobs("python, sql", jobs, min_percent=50)] == ["B", "A"]
