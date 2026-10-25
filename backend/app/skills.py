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
    ".net", "asp.net", "laravel", "rails", "graphql", "rest api",
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
    # Marketing / analytics
    "sem", "google ads", "meta ads", "google analytics", "content marketing",
    "email marketing", "social media marketing", "social media", "copywriting",
    "a/b testing", "data cleaning", "crm", "hubspot", "salesforce",
}

# Other ways people write the same skill. Keys must be in SKILLS; a resume that
# uses any alias gets credit for the key. Keep aliases unambiguous: "go" or
# "ts" would match ordinary words.
SYNONYMS = {
    "javascript": ["js", "ecmascript", "es6"],
    "node.js": ["nodejs", "node js"],
    "react": ["react.js", "reactjs"],
    "next.js": ["nextjs"],
    "vue": ["vue.js", "vuejs"],
    "c++": ["cpp"],
    "c#": ["csharp", "c sharp"],
    "golang": ["go lang"],
    "postgresql": ["postgres", "psql"],
    "mongodb": ["mongo"],
    "kubernetes": ["k8s"],
    "aws": ["amazon web services"],
    "gcp": ["google cloud", "google cloud platform"],
    "azure": ["microsoft azure"],
    "ci/cd": ["cicd", "ci cd", "continuous integration", "continuous delivery", "continuous deployment"],
    "rest api": ["restful", "restful api", "restful services", "rest services"],
    "unit testing": ["unit tests", "unit test", "unit-tested", "unit-testing"],
    "machine learning": ["ml"],
    "nlp": ["natural language processing"],
    "scikit-learn": ["sklearn", "scikit learn"],
    "power bi": ["powerbi"],
    "excel": ["ms excel", "microsoft excel"],
    "seo": ["search engine optimization", "search engine optimisation"],
    "sem": ["search engine marketing"],
    "google ads": ["adwords", "google adwords"],
    "meta ads": ["facebook ads", "instagram ads"],
    "ui/ux": ["ui ux", "ux/ui", "user experience"],
    "generative ai": ["genai", "gen ai"],
    "llm": ["large language model", "large language models"],
    "oop": ["object oriented programming", "object-oriented programming"],
    "data structures": ["dsa"],
    "github actions": ["gh actions"],
    "data visualization": ["data visualisation", "data viz"],
    "social media marketing": ["smm", "social media"],
    "a/b testing": ["a/b tests", "ab testing", "split testing"],
}

# Phrases that mark a job-description requirement as optional.
NICE_TO_HAVE = [
    "nice to have", "nice-to-have", "good to have", "is a plus", "a plus", "plus:",
    "bonus", "preferred", "preferably", "optional", "advantage", "desirable", "ideally",
]

# Filler words that make a bullet point vague even when it has a verb and a number.
VAGUE_WORDS = {"things", "stuff", "various", "etc", "miscellaneous"}

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
