import os
from typing import Dict, Any

import bentoml
from bentoml.io import JSON


svc = bentoml.Service("resume_ml_service")


@svc.api(input=JSON(), output=JSON())
def parse_resume(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Lightweight placeholder that splits sections heuristically.
    Replace with ONNX-backed NER/section tagger when available.
    """
    text: str = (payload or {}).get("text", "")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    sections: Dict[str, list[str]] = {"experience": [], "education": [], "skills": [], "other": []}
    current = "other"
    for line in lines:
        low = line.lower()
        if "experience" in low:
            current = "experience"
        elif "education" in low:
            current = "education"
        elif "skill" in low:
            current = "skills"
        sections.setdefault(current, []).append(line)
    return {"sections": sections, "model": "placeholder", "version": "v0"}


@svc.api(input=JSON(), output=JSON())
def extract_skills(payload: Dict[str, Any]) -> Dict[str, Any]:
    text: str = (payload or {}).get("text", "")
    # naive keyword scan placeholder
    catalog = ["python", "fastapi", "azure", "aws", "docker", "kubernetes", "sql", "pandas", "onnx", "bentoml"]
    found = sorted({w for w in catalog if w.lower() in text.lower()})
    return {"skills": found, "model": "placeholder", "version": "v0"}


@svc.api(input=JSON(), output=JSON())
def score_match(payload: Dict[str, Any]) -> Dict[str, Any]:
    resume_text: str = (payload or {}).get("resume_text", "")
    job_text: str = (payload or {}).get("job_description", "")
    rset = set(w.strip(".,;:!?").lower() for w in resume_text.split())
    jset = set(w.strip(".,;:!?").lower() for w in job_text.split())
    if not rset or not jset:
        return {"score": 0.0, "overlap": [], "model": "placeholder", "version": "v0"}
    overlap = rset.intersection(jset)
    score = len(overlap) / max(1, len(jset))
    return {"score": round(float(score), 4), "overlap": sorted(list(overlap)), "model": "placeholder", "version": "v0"}


