"""A small, extendable vocabulary of skills that ATS systems commonly look for.

Contributions welcome: add terms in lowercase. Multi-word terms are fine.
"""

SKILLS = {
    # Languages
    "python", "java", "javascript", "typescript", "c", "c++", "c#", "golang",
    "rust", "kotlin", "swift", "php", "ruby", "scala", "matlab", "sql", "bash",
    "html", "css", "dart",
    # Frontend
    "react", "react native", "next.js", "vue", "angular", "svelte", "redux",
    "tailwind", "bootstrap", "jquery", "webpack", "vite", "flutter",
    # Backend
    "node.js", "express", "django", "flask", "fastapi", "spring", "spring boot",
    ".net", "asp.net", "laravel", "rails", "graphql", "rest api", "restful",
    "microservices", "grpc",
    # Data / AI
    "machine learning", "deep learning", "nlp", "computer vision", "pandas",
    "numpy", "scikit-learn", "tensorflow", "pytorch", "keras", "opencv",
    "data analysis", "data visualization", "power bi", "tableau", "excel",
    "statistics", "llm", "generative ai", "hugging face", "langchain", "spark",
    "hadoop", "airflow", "etl",
    # Databases
    "mysql", "postgresql", "mongodb", "redis", "sqlite", "oracle", "firebase",
    "dynamodb", "elasticsearch", "cassandra",
    # Cloud / DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
    "jenkins", "ci/cd", "github actions", "linux", "nginx", "git", "github",
    "gitlab",
    # Testing / practices
    "unit testing", "jest", "pytest", "selenium", "cypress", "tdd", "agile",
    "scrum", "jira", "oop", "data structures", "algorithms", "system design",
    # Security / networking
    "cybersecurity", "networking", "oauth", "jwt",
    # Soft / business skills
    "communication", "leadership", "teamwork", "problem solving",
    "project management", "stakeholder management", "time management",
    "critical thinking", "customer service", "sales", "marketing", "seo",
    "content writing", "figma", "ui/ux",
}

ACTION_VERBS = {
    "achieved", "analyzed", "architected", "automated", "built", "collaborated",
    "conducted", "created", "delivered", "deployed", "designed", "developed",
    "drove", "enhanced", "established", "executed", "generated", "implemented",
    "improved", "increased", "integrated", "launched", "led", "managed",
    "mentored", "migrated", "optimized", "organized", "orchestrated", "planned",
    "presented", "reduced", "refactored", "resolved", "researched", "scaled",
    "shipped", "simplified", "spearheaded", "streamlined", "supported",
    "tested", "trained", "transformed", "upgraded", "wrote",
}

# Words common in job descriptions that are not useful as keywords.
JD_NOISE = {
    "experience", "work", "working", "team", "ability", "strong", "years",
    "year", "skills", "knowledge", "role", "candidate", "candidates", "job",
    "company", "including", "required", "requirements", "preferred", "plus",
    "good", "excellent", "responsibilities", "understanding", "looking",
    "opportunity", "join", "using", "use", "well", "new", "related", "etc",
    "must", "will", "able", "help", "across", "within", "based", "degree",
    "bachelor", "field", "equivalent", "familiarity", "familiar", "great",
    "environment", "best", "practices", "time", "level", "day", "high",
    "make", "need", "want", "like", "also", "per", "us", "we", "you", "our",
    "ideal", "seeking", "hands", "solid", "proven", "minimum", "least",
}
