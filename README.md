
---

# 🎯 AI Job Matcher - Reverse ATS

[![GitHub Actions](https://github.com/Aliesapour79/job-scraper/actions/workflows/job-matcher.yml/badge.svg)](https://github.com/Aliesapour79/job-scraper/actions)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 🧠 Overview

**AI Job Matcher** is an intelligent automation system that analyzes job listings and matches them with your resume using AI, NLP, and scoring algorithms.

It helps you:

* 🔍 Find relevant job opportunities automatically
* 🧠 Match jobs with your resume using semantic similarity
* 📊 Rank jobs based on relevance and fit
* 📩 Send automated reports via Telegram
* ⏰ Run continuously via GitHub Actions

> ⚠️ This is a personal decision-support system, not a commercial SaaS.

---

## ✨ Key Features

* 🔄 Multi-site job scraping (e-estekhdam, Jobvision)
* 🧠 Hybrid NLP matching (TF-IDF + Sentence Embeddings)
* 🎯 Dual scoring system (Technical + General tracks)
* 🏷️ Automatic job categorization
* 📊 Structured JSON + HTML reports
* 🚨 Outlier detection for exceptional matches
* ⏰ Fully automated execution (every 6 hours)
* 📱 Telegram notifications

---

## 🏗️ System Architecture

### 1. Data Collection

* Selenium-based web scraping
* Multi-page crawling support
* Extensible job portal design

### 2. NLP Engine

* TF-IDF similarity scoring
* Sentence Transformers:

  * `paraphrase-multilingual-MiniLM-L12-v2`
* Keyword-based skill detection

---

### 3. Scoring System

#### 🔧 Technical Score

* Programming (Python, C++, etc.)
* AI / Machine Learning
* IoT / Embedded Systems
* DevOps / Networking
* Data Analysis

#### 🧾 General Score

* Office tools (Excel, Word)
* Communication skills
* Management & coordination
* Documentation & reporting

---

## 📌 Final Score Formula

```text
Final Score =
(Technical × 0.7) +
(General × 0.3) +
Boost - Penalty
```

---

## 🚨 Outlier Detection Engine

Adaptive hybrid model:

* Z-Score (distribution-aware)
* Percentile ranking (robust fallback)
* Automatic skewness detection
* Smart switching between statistical methods

---

## 📁 Project Structure

```
job-scraper/
│
├── config/
│   ├── resume.py
│   └── settings.py
│
├── matcher/
│   ├── score_calculator.py
│   ├── semantic_matcher.py
│   └── skill_groups.py
│
├── scrapers/
│   ├── e_estekhdam_scraper.py
│   └── jobvision_scraper.py
│
├── report/
│   └── html_generator.py
│
├── utils/
│   └── driver.py
│
├── main.py
├── requirements.txt
└── .github/workflows/job-matcher.yml
```

---

## ⚙️ Configuration

### Scoring Weights

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

## 📊 Outputs

### 📦 JSON Output

Each job contains:

* Final score
* Category (Technical / General / Hybrid)
* Matched skills
* Outlier score
* Full metadata

---

### 🌐 HTML Report

* Ranked job cards
* Category separation
* Skill highlights
* Outlier indicators
* Clean dashboard-style UI

---

## 🚀 Getting Started

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run manually

```bash
python main.py
```

### 3. Automation (GitHub Actions)

* Runs every 6 hours
* Sends results via Telegram
* Fully hands-free pipeline

---

## 🧰 Tech Stack

| Layer      | Technology            |
| ---------- | --------------------- |
| Language   | Python 3.11           |
| Scraping   | Selenium              |
| NLP        | Sentence Transformers |
| ML / Stats | Scikit-learn          |
| Math       | NumPy                 |
| CI/CD      | GitHub Actions        |
| Messaging  | Telegram API          |

---

## 📈 Version History

| Version | Description                   |
| ------- | ----------------------------- |
| v7      | Multi-site resilient scraping ||
| v6.3    | Dual-track scoring system     |
| v6.2    | Hybrid outlier detection      |
| v6.1    | Multi-intent scoring          |
| v6.0    | Modular architecture refactor |

---

## 👤 Author

**Ali Eisapour Sharabiani**

Software Engineer
Python | AI | Computer Vision | Embedded Systems

---
