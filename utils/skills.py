SKILLS_DB = [
    # Languages
    "python", "java", "c++", "c#", "javascript", "typescript", "go", "rust",
    "kotlin", "swift", "ruby", "php", "scala", "r", "matlab", "bash", "perl",

    # Web
    "html", "css", "react", "angular", "vue", "next.js", "nuxt", "svelte",
    "node.js", "express", "django", "flask", "fastapi", "spring boot",
    "graphql", "rest api", "websocket", "webpack", "vite",

    # Data & ML
    "machine learning", "deep learning", "nlp", "computer vision",
    "data analysis", "data science", "statistics", "a/b testing",
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras",
    "hugging face", "transformers", "bert", "gpt", "llm", "rag",
    "langchain", "openai", "generative ai", "reinforcement learning",
    "xgboost", "lightgbm", "matplotlib", "seaborn", "plotly",

    # Databases
    "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
    "cassandra", "sqlite", "oracle", "firebase", "dynamodb", "neo4j",

    # Cloud & DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
    "jenkins", "github actions", "ci/cd", "linux", "git", "devops",
    "serverless", "lambda", "s3", "ec2",

    # Tools & Practices
    "agile", "scrum", "jira", "microservices", "system design", "oop",
    "data structures", "algorithms", "testing", "unit testing", "tdd",
    "selenium", "tableau", "power bi", "spark", "hadoop", "kafka",
    "excel", "figma", "photoshop",

    # Soft skills
    "communication", "leadership", "teamwork", "problem solving",
    "project management", "analytical", "critical thinking", "mentoring",
]


def extract_skills(text: str) -> list:
    text_lower = text.lower()
    return list({s for s in SKILLS_DB if s in text_lower})


def get_skill_match(resume_text: str, job_desc: str):
    resume_skills = extract_skills(resume_text)
    job_skills    = extract_skills(job_desc)

    matched = sorted(set(resume_skills) & set(job_skills))
    missing = sorted(set(job_skills)    - set(resume_skills))
    score   = (len(matched) / len(job_skills) * 100) if job_skills else 0

    return matched, missing, round(score, 2)
