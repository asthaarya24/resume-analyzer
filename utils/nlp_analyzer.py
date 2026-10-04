"""
spaCy-based NLP analysis.
Tries en_core_web_md first (better), falls back to en_core_web_sm,
then falls back to a pure-regex approach if no model is installed.
"""
import re
from collections import Counter

try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_md")
        print("spaCy: en_core_web_md loaded")
    except OSError:
        try:
            nlp = spacy.load("en_core_web_sm")
            print("spaCy: en_core_web_sm loaded")
        except OSError:
            nlp = None
            print("WARNING: No spaCy model found. Run:  python -m spacy download en_core_web_sm")
except ImportError:
    nlp = None
    print("WARNING: spaCy not installed. Run:  pip install spacy")

STOP = {
    "the","a","an","and","or","but","in","on","at","to","for","of","with",
    "by","from","is","are","was","were","be","been","have","has","had","do",
    "does","did","will","would","could","should","may","might","shall","can",
    "we","you","they","he","she","it","this","that","these","those","our",
    "your","their","its","as","if","then","than","so","up","out","about",
    "into","through","during","including","experience","work","working",
    "ability","strong","good","excellent","required","preferred","using",
    "skills","skill","must","also","well","high","years","year","team",
}


# ── keyword extraction ──────────────────────────────────────────────────────

def _keywords_spacy(text: str, n: int) -> list:
    doc = nlp(text[:12000])
    words = []
    for tok in doc:
        if (not tok.is_stop and not tok.is_punct and not tok.is_space
                and tok.pos_ in {"NOUN","PROPN","ADJ","VERB"}
                and len(tok.lemma_) > 2
                and tok.lemma_.lower() not in STOP):
            words.append(tok.lemma_.lower())
    for chunk in doc.noun_chunks:
        clean = chunk.text.lower().strip()
        if 2 < len(clean) < 40 and clean not in STOP:
            words.append(clean)
    return [w for w, _ in Counter(words).most_common(n)]


def _keywords_regex(text: str, n: int) -> list:
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    filtered = [w for w in words if w not in STOP]
    return [w for w, _ in Counter(filtered).most_common(n)]


def extract_keywords(text: str, n: int = 20) -> list:
    return _keywords_spacy(text, n) if nlp else _keywords_regex(text, n)


# ── named entity extraction ─────────────────────────────────────────────────

def extract_entities(text: str) -> list:
    if not nlp:
        return []
    doc = nlp(text[:6000])
    buckets: dict = {}
    for ent in doc.ents:
        if ent.label_ in {"ORG","PRODUCT","GPE","DATE","WORK_OF_ART"}:
            val = ent.text.strip()
            if val:
                buckets.setdefault(ent.label_, [])
                if val not in buckets[ent.label_]:
                    buckets[ent.label_].append(val)
    return [{"label": k, "values": v[:6]} for k, v in buckets.items()]


def extract_education(text: str) -> list:
    """Extracts degree, university, and GPA from education lines."""
    keywords = [
        "bachelor", "master", r"b\.sc", r"m\.sc", r"b\.tech", r"m\.tech",
        r"b\.e", "mba", "phd", "doctor", "ba", "bs", "ms", "bba", "degree"
    ]
    found = []
    for line in re.split(r'\r?\n', text or ""):
        low = line.lower()
        for kw in keywords:
            if kw in low:
                # Extract degree
                degree_match = None
                for deg in ["bachelor of science", "bachelor of arts", "bachelor of engineering", "bachelor of technology",
                           "master of science", "master of arts", "master of engineering", "master of technology",
                           "master of business administration", "b.sc", "m.sc", "b.tech", "m.tech", "b.e", "mba", "phd"]:
                    if deg in low:
                        degree_match = deg.replace('.', '').upper()
                        break
                
                # Extract university/institution (words after common institution keywords)
                uni_match = None
                uni_patterns = [r'(?:university|college|institute|school)\s+([A-Z][a-zA-Z\s]+)',
                               r'at\s+([A-Z][a-zA-Z\s]+)(?:,|\s|$)']
                for pattern in uni_patterns:
                    match = re.search(pattern, line, re.I)
                    if match:
                        uni_match = match.group(1).strip()
                        # Remove location if present
                        uni_match = re.sub(r',.*$', '', uni_match).strip()
                        break
                
                # Extract GPA
                gpa_match = None
                gpa_patterns = [r'gpa[:\s]*([0-9]\.[0-9]|[0-9]/[0-9]|[0-9]+%|\d+\.\d+)',
                               r'cgpa[:\s]*([0-9]\.[0-9]|[0-9]/[0-9]|[0-9]+%|\d+\.\d+)']
                for pattern in gpa_patterns:
                    match = re.search(pattern, line, re.I)
                    if match:
                        gpa_match = match.group(1).strip()
                        break
                
                # Combine all info
                parts = []
                if degree_match:
                    parts.append(degree_match)
                if uni_match:
                    parts.append(f"@ {uni_match}")
                if gpa_match:
                    parts.append(f"(GPA: {gpa_match})")
                
                if parts:
                    clean = " ".join(parts)
                    if clean and clean not in found:
                        found.append(clean)
                break
    return found[:6]


def extract_experience(text: str) -> list:
    """Extracts all work experience entries with job title, organization, and years."""
    # Broader set of role terms to catch more experience entries
    role_terms = ["engineer", "developer", "manager", "analyst", "consultant", "director",
                  "designer", "architect", "coordinator", "specialist", "associate", "intern",
                  "experience", "worked", "working", "role", "position", "employed", "job"]
    duration_re = re.compile(r"\d+\+?\s*(?:years|yrs|year)", re.I)
    date_re = re.compile(r"\d{4}[-–]\d{4}|\d{4}\s*[-–]\s*Present|\d{4}", re.I)
    found = []
    for line in re.split(r'\r?\n', text or ""):
        low = line.lower()
        # Include lines with role terms, durations, or dates
        if any(term in low for term in role_terms) or duration_re.search(line) or date_re.search(line):
            # Extract job title (first capitalized phrase that looks like a title)
            title_match = None
            # Try to extract title from common patterns
            title_patterns = [
                r"(?:senior|junior|lead|principal|staff)?\s*(?:software|frontend|backend|full.?stack|data|machine\s+learning|product|project)?\s*(?:engineer|developer|scientist|analyst|manager|consultant|advisor|director|designer|architect|coordinator|specialist|associate|intern|trainee)",
                r"([A-Z][a-zA-Z\s]+(?:engineer|developer|manager|analyst|consultant|director|designer|architect|coordinator|specialist|associate|intern))"
            ]
            for pattern in title_patterns:
                match = re.search(pattern, line, re.I)
                if match:
                    title_match = match.group(0).strip().title()
                    break
            
            # If no title pattern matched, try to extract the first meaningful phrase
            if not title_match:
                # Extract first 2-3 capitalized words as potential title
                words = line.split()
                title_words = []
                for word in words:
                    if word[0].isupper() and len(word) > 2:
                        title_words.append(word)
                    if len(title_words) >= 3:
                        break
                if title_words:
                    title_match = " ".join(title_words)
            
            # Extract organization/company
            org_match = None
            org_patterns = [r'(?:at|@|with|for)\s+([A-Z][a-zA-Z0-9\s&]+)(?:,|\s|$)',
                           r'(?:company|corporation|inc|ltd|llc|pvt|ltd\.|pvt\.)\s+([A-Z][a-zA-Z0-9\s&]+)']
            for pattern in org_patterns:
                match = re.search(pattern, line, re.I)
                if match:
                    org_match = match.group(1).strip()
                    # Remove location if present
                    org_match = re.sub(r',.*$', '', org_match).strip()
                    # Remove common filler words
                    org_match = re.sub(r'\b(?:the|a|an)\b', '', org_match, flags=re.I).strip()
                    break
            
            # Extract working years/duration
            years_match = None
            years_patterns = [r'(\d{4}[-–]\d{4}|\d{4}\s*[-–]\s*Present|\d{4})',
                             r'(\d+\+?\s*(?:years|yrs|year|months|month))']
            for pattern in years_patterns:
                match = re.search(pattern, line, re.I)
                if match:
                    years_match = match.group(1).strip()
                    break
            
            # Combine all info
            parts = []
            if title_match:
                parts.append(title_match)
            if org_match:
                parts.append(f"@ {org_match}")
            if years_match:
                parts.append(f"({years_match})")
            
            # If we have at least some info, add it
            if parts:
                clean = " ".join(parts)
                if clean and len(clean) > 5 and clean not in found:
                    found.append(clean)
    return found[:10]


# ── overlap score ────────────────────────────────────────────────────────────

def keyword_overlap_score(resume_kw: list, job_kw: list) -> float:
    if not job_kw:
        return 0.0
    overlap = set(resume_kw) & set(job_kw)
    return round(len(overlap) / len(job_kw) * 100, 2)


# ── main entry ───────────────────────────────────────────────────────────────

def analyze_with_nlp(resume_text: str, job_desc: str) -> dict:
    resume_kw = extract_keywords(resume_text, n=30)
    job_kw    = extract_keywords(job_desc,    n=30)
    entities  = extract_entities(resume_text)
    education = extract_education(resume_text)
    experience = extract_experience(resume_text)
    score     = keyword_overlap_score(resume_kw, job_kw)

    return {
        "resume_keywords":       resume_kw[:20],
        "job_keywords":          job_kw[:20],
        "entities":              entities,
        "education":             education,
        "experience":            experience,
        "keyword_overlap_score": score,
    }
