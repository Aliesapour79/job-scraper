````markdown
# 🎯 AI Job Matcher - Reverse ATS

[![GitHub Actions](https://github.com/Aliesapour79/job-scraper/actions/workflows/job-matcher.yml/badge.svg)](https://github.com/Aliesapour79/job-scraper/actions)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> **An intelligent AI-powered system that matches job listings with your resume and ranks the best opportunities automatically.**

---

## 🎯 What is this?

AI Job Matcher is a personal automation tool that:

- 🔍 Scrapes job listings from multiple job portals
- 🧠 Matches jobs with your resume using AI & NLP
- 📊 Ranks opportunities based on relevance and fit
- 📧 Sends automated reports via Telegram

👉 This project is a **personal decision-support system**, not a SaaS product.

---

## ✨ Features

| Feature | Description |
|--------|-------------|
| 🔄 Multi-site scraping | Supports e-estekhdam & Jobvision (extensible) |
| 🧠 Smart matching | TF-IDF + Sentence Embeddings + Semantic scoring |
| 🎯 Dual-track scoring | Separate scoring for Technical & General roles |
| 🏷️ Auto categorization | Detects Technical / Administrative / Hybrid jobs |
| 📊 Advanced reporting | HTML + JSON structured output |
| 🚨 Outlier detection | Highlights unusually strong job matches |
| ⏰ Automation | Runs every 6 hours via GitHub Actions |
| 📱 Telegram alerts | Sends results directly to Telegram |

---

## 🧠 System Architecture

### 1. Data Collection Layer
- Selenium-based dynamic scraping
- Supports multiple job portals
- Full pagination crawling per category

### 2. NLP Processing Layer
- TF-IDF similarity scoring
- Sentence Transformers embeddings
  - `paraphrase-multilingual-MiniLM-L12-v2`
- Keyword-based skill detection

### 3. Dual-Track Scoring System

#### 🔧 Technical Track
- Programming (Python, C++, etc.)
- AI / Machine Learning
- IoT / Embedded Systems
- DevOps / Networking
- Data Analysis

#### 🧾 General Track
- Office tools (Excel, Word, etc.)
- Management & coordination
- Communication & support
- Documentation & reporting

---

### 4. Final Scoring Engine

```text
Final Score =
(Technical Score × 0.7) +
(General Score × 0.3) +
Boost - Penalty
````

---

### 5. Outlier Detection System

* Adaptive **Z-Score + Percentile hybrid method**
* Automatic skewness detection
* Smart fallback for non-normal distributions

---

## 📂 Project Structure

```
job-scraper/
├── config/                 # Configuration & resume
│   ├── resume.py
│   └── settings.py
│
├── matcher/                # Core engine
│   ├── score_calculator.py
│   ├── semantic_matcher.py
│   └── skill_groups.py
│
├── scrapers/              # Job scrapers
│   ├── e_estekhdam_scraper.py
│   └── jobvision_scraper.py
│
├── report/                # Report generator
│   └── html_generator.py
│
├── utils/                 # Utilities
│   └── driver.py
│
├── main.py
├── requirements.txt
└── .github/workflows/
    └── job-matcher.yml
```

---

## ⚙️ Configuration

### `config/settings.py`

```python
SCORE_WEIGHTS = {
    "tfidf": 0.30,
    "embedding": 0.70
}

INTENT_WEIGHTS = {
    "technical": 0.70,
    "general": 0.30
}

FILTERS = {
    "min_score": 20,
    "top_n_results": 25
}
```

---

### `config/resume.py`

Your resume is stored as plain text for easy modification.

---

## 📊 Outputs

### JSON Output

Includes:

* Final score breakdown
* Job category
* Matched skills
* Outlier score

### HTML Report

* Ranked job cards
* Technical / General separation
* Skill highlights
* Outlier indicators
* Visual grouping

---

## 🚀 How to Run

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run manually

```bash
python main.py
```

### Automation

Runs every 6 hours via GitHub Actions and sends results to Telegram.

---

## 🔧 Requirements

* Python 3.11+
* Chrome (Selenium)
* Internet connection

---

## 🧪 Tech Stack

| Technology            | Purpose              |
| --------------------- | -------------------- |
| Python                | Core logic           |
| Selenium              | Web scraping         |
| Sentence Transformers | NLP embeddings       |
| Scikit-learn          | TF-IDF + stats       |
| NumPy                 | Numerical operations |
| GitHub Actions        | Automation           |
| Telegram API          | Notifications        |

---

## 📈 Version History

| Version | Changes                                         |
| ------- | ----------------------------------------------- |
| v6.3    | Dual-track + improved scoring system            |
| v6.2    | Hybrid outlier detection (Z-Score + Percentile) |
| v6.1    | Multi-intent scoring                            |
| v6.0    | Full modular refactor                           |

---

## 👤 Author

**Ali Eisapour Sharabiani**
Software Engineer | Python | AI / Computer Vision | Embedded Systems

```