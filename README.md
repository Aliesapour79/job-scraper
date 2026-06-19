# 🎯 Job Matcher Engine v6.3 (Personal AI System)

A personal intelligent job matching system that scrapes job listings, analyzes them using hybrid scoring (TF-IDF + Semantic Embeddings), and ranks them based on relevance to a personal resume.

This project is built as a **personal decision-support tool**, not a production SaaS product.

---

# ⚙️ Core Idea

Automatically:

- Scrape job listings from a job portal
- Extract structured job data (title, company, description, requirements)
- Match jobs against a personal resume profile
- Rank jobs based on relevance
- Provide explainable scoring + visualization

---

# 🧠 System Architecture

## 1. Data Collection Layer
- Selenium-based web scraping
- Extract job postings from target site

---

## 2. Feature Engineering Layer

### 🔤 Keyword Matching
- Domain-specific keyword detection
- Weighted keyword scoring

### 📊 TF-IDF Similarity
- Text similarity between resume and job descriptions

### 🧠 Semantic Embedding
- SentenceTransformer model:
  - `paraphrase-multilingual-MiniLM-L12-v2`
- Computes semantic similarity between resume and job postings

---

## 3. Dual-Track Scoring System

### 🔧 Technical Track
Covers:
- Programming
- AI / ML
- Electronics
- IoT
- Networking
- Data analysis

### 🧾 General Track
Covers:
- Office work
- Communication
- Reporting
- Excel / Word / administrative tasks

---

## 4. Hybrid Classification

Jobs are categorized into:

- Technical
- Administrative
- Hybrid

Used for ranking + visualization.

---

## 5. Scoring Engine

Final score includes:

- TF-IDF similarity
- Embedding similarity
- Boost factors (skill reinforcement)
- Penalty system (generic/noisy jobs)
- Category adjustments

---

## 6. Outlier Detection

Used to detect:

- Unusual job matches
- Distribution anomalies

(Not used for ranking decisions)

---

# 📦 Configuration (`config.py`)

- `SCORE_WEIGHTS` → TF-IDF vs Embedding balance
- `TECH_KEYWORDS_MAP` → technical domains
- `ADMIN_KEYWORDS_WEIGHTED` → office/general skills
- `FILTERS` → thresholds & filtering rules
- `EMBEDDING_MODEL` → model selection

---

# 📊 Outputs

## JSON Output
Includes:
- final score
- category
- skill matches
- boosts / penalties

## HTML Report
Includes:
- ranked job cards
- category separation
- skill visualization
- score breakdown
- outlier indicators
- group analysis bars

---

# 🧪 Scoring Breakdown

Each job has:

- Technical Score
- General Score
- Embedding Score
- TF-IDF Score
- Boost Score
- Penalty Score
- Final Score

---

# 🧩 Key Features

- Dual-track scoring (Technical / General)
- Hybrid job detection
- Multilingual semantic matching
- Explainable ranking system
- Outlier analytics
- Rich HTML reporting
- Fully modular pipeline

---

# 📁 Project Structure
main.py → Orchestration pipeline
semantic_matcher.py → Embedding + similarity engine
html_generator.py → HTML report generator
config.py → System configuration
job_matcher_core.py → Scraping + scoring logic



---

# 🚀 Workflow

1. Scrape job listings
2. Extract structured data
3. Compute:
   - TF-IDF similarity
   - Embedding similarity
4. Apply dual-track scoring
5. Classify jobs
6. Apply boosts & penalties
7. Rank results
8. Export JSON + HTML

---

# 🎯 Design Philosophy

This system is:

- Personal AI assistant for job discovery
- Hybrid NLP ranking engine
- Explainable scoring system

Not optimized for scale — optimized for **accuracy + interpretability**.

---

# ⚠️ Notes

- Embedding model is optional (fallback supported)
- Outlier score is analytical only
- Heavily configurable via `config.py`
- Tuned for a single resume context

---

# 👤 Author

Personal AI system for intelligent job matching and analysis.

Version: v6.3 (Dual Track + Hybrid Scoring)
