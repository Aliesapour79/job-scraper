## 📘 MatchFlow Pipeline

---

## 🧠 Overview

**MatchFlow Pipeline** is a job intelligence and ranking system that scrapes job listings, processes them using NLP techniques, and ranks them based on semantic relevance to a target resume with **level-based skill matching**.

Unlike a simple scraper, this system is a **full data pipeline + recommendation engine + observability layer**.

---

## 🌐 Live Demo
👉 **Streamlit Dashboard:**
[https://jobvision-analyzer.streamlit.app/](https://jobvision-analyzer.streamlit.app/)

---

## 🚀 System Evolution

| Version | Description |
|---------|-------------|
| v1 | Simple scraping script |
| v2 | Basic NLP matching (TF-IDF) |
| v3 | Multi-site scraping pipeline |
| v4 | Hybrid scoring (embedding + keyword) |
| v5 | SQLite persistence + deduplication |
| v6 | Advanced scoring engine |
| v7 | Observability + caching + dashboard |
| **v8** | **Level-based matching + dynamic weights + unified database** |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      MATCHFLOW PIPELINE                         │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        🕷️ SCRAPING LAYER                        │
│  ────────────────────────────────────────────────────────────── │
│  • Jobvision scraper with location & is_urgent extraction      │
│  • Selenium-based crawling with retry handling                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         🧹 ETL LAYER                           │
│  ────────────────────────────────────────────────────────────── │
│  • Extract skills from JSON (source database)                  │
│  • Normalize skills to "Skill (Level)" format                  │
│  • Clean requirements and extract metadata                     │
│  • Store in unified database schema                            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         💾 DATA LAYER                          │
│  ────────────────────────────────────────────────────────────── │
│  • SQLite with unified schema (17 columns)                     │
│
│  • Foreign key relationship with scores table                  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        🧠 MATCHER LAYER                        │
│  ────────────────────────────────────────────────────────────── │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ HARD SCORE (Level-Based)                               │    │
│  │ • Skill matching with levels (Beginner/Intermediate/Advanced) │
│  │ • Dynamic skill groups with weighted keywords          │    │
│  │ • Ratio-based scoring: resume_level / job_level        │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ FUNCTIONAL SCORE                                       │    │
│  │ • Extracted from job description                       │    │
│  │ • Matches functional verbs (design, develop, etc.)     │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ SOFT SCORE                                             │    │
│  │ • Extracted from job description                       │    │
│  │ • Matches soft skills (teamwork, communication, etc.)  │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ SEMANTIC SCORE                                         │    │
│  │ • Sentence Transformers (MiniLM)                       │    │
│  │ • Resume-to-job semantic similarity                    │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ ELIGIBILITY (Penalty System)                           │    │
│  │ • Age range validation                                 │    │
│  │ • Gender requirements                                  │    │
│  │ • Military service status                              │    │
│  │ • Education level matching                             │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        📊 OUTPUT LAYER                         │
│  ────────────────────────────────────────────────────────────── │
│  • JSON report with full details                              │
│  • HTML report with visual cards                              │
│  • Score storage in database                                  │
│  • Top 30 jobs to Telegram (optional)                         │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        📡 OBSERVABILITY LAYER                  │
│  ────────────────────────────────────────────────────────────── │
│  • Streamlit Dashboard with real-time analytics                │
│  • Score attribution analysis                                  │
│  • Category distribution charts                                │
│  • Job search interface                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Key Features

### 🔄 Multi-Source Scraping

- Jobvision with multiple categories (developer, data-science, secretary, hr)
- Selenium-based crawling with retry handling
- **location** and **is_urgent** extraction
- Cache system for fast duplicate detection

---

### 🧠 Level-Based Skill Matching (v8)

**Hard Score** is now computed using **skill levels**:

```
Level Weights:
- Beginner   → 1.0
- Intermediate → 2.0
- Advanced   → 3.0

Match Score = min(resume_level / job_level, 1.0)
```

**Example:**
| Resume Level | Job Level | Score |
|--------------|-----------|-------|
| Advanced (3) | Advanced (3) | 100% |
| Advanced (3) | Intermediate (2) | 100% |
| Intermediate (2) | Advanced (3) | 66.7% |

---

### 🎯 Dynamic Weights

Weights are automatically adjusted based on job category:

| Category | Hard | Functional | Soft | Semantic |
|----------|------|------------|------|----------|
| **Technical** | 0.50 | 0.20 | 0.10 | 0.20 |
| **Administrative** | 0.15 | 0.25 | 0.40 | 0.20 |
| **Hybrid** | 0.35 | 0.25 | 0.25 | 0.15 |

---

### 🗄️ Unified Database Schema

**17 columns** with proper relationships:

- `location`, `is_urgent` fields added
- Skills stored as `"Skill (Level)"` format
- Foreign key to scores table
- Indexed for performance

---

### 📊 Scoring Formula (v8)

```
Hard Score = Σ(skill_match_score × weight) × normalization
Functional Score = Σ(functional_verb_matches)
Soft Score = Σ(soft_keyword_matches)
Semantic Score = embedding_similarity × 100

Raw Score = (Hard × W_hard) + (Functional × W_func) + (Soft × W_soft) + (Semantic × W_semantic)

Final Score = Raw Score × (1 - Penalty/100)
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.11+ |
| Scraping | Selenium |
| NLP | sentence-transformers (MiniLM) |
| ML/Stats | scikit-learn, numpy, scipy |
| Storage | SQLite |
| Dashboard | Streamlit + Plotly |
| Visualization | HTML + CSS |
| CI/CD | GitHub Actions |

---

## 📁 Project Structure

```
matchflow-pipeline/
├── config/              # Settings + resume
├── core/                # Pipeline engine (scorer, reporter)
├── matcher/             # Matching engine
│   ├── eligibility.py   # Penalty system
│   ├── explainability.py # Score explanations
│   ├── score_calculator.py # v8 scoring
│   ├── skill_parser.py  # Level-based parsing
│   ├── skill_groups.py  # Skill categories
│   └── weights.py       # Dynamic weights
├── scrapers/            # Web scraping
├── utils/               # Helpers, DB, drivers
├── report/              # HTML generator
├── analysis/            # Score attribution analysis
├── scripts/             # ETL and scoring scripts
├── data/                # SQLite database
├── cache/               # Cache layer
├── output/              # Reports (JSON/HTML)
├── tmp/                 # Test files (ignored)
│
├── main.py              # Entry point
├── dashboard.py         # Streamlit dashboard
├── README.md
└── requirements.txt
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Aliesapour79/job-scraper.git
cd job-scraper
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```


### 3. Run the system

```bash
python main.py
```

### 4. Optional components

```bash
# Dashboard
streamlit run dashboard.py

# Score attribution analysis
python analysis/run_final_score_attribution.py

# Database ETL
python scripts/database_cleaner.py
```

---

## 📈 Performance Notes

- **Jobs processed:** 3,587 jobs per run
- **Scoring speed:** ~5-6 jobs/second
- **Best match score:** 82.01%

---

## 📊 Outputs

### 📦 JSON Report
- Full job details with scores
- Matched skills list
- Category classification
- Penalty reasons

### 🌐 HTML Report
- Visual job cards
- Score breakdown
- Category filtering
- Top matches highlighted

### 📈 Dashboard
- Real-time analytics
- Category distribution charts
- Top companies ranking
- Job search interface

---

## 📌 Current System State

This system is a:

> **Complete Job Intelligence & Ranking Pipeline with Level-Based Matching, Dynamic Weights, and Unified Database**

---

## 👤 Author

**Ali Eisapour Sharabiani**

Software Engineer | Python Developer | AI/Computer Vision | IoT & Embedded Systems

---
