---

## 📘 AI Job Intelligence System (Reverse ATS v7)
---
## 🧠 Overview

**AI Job Intelligence System** is a multi-source job analysis and ranking engine that scrapes job listings, processes them using NLP techniques, and ranks them based on semantic relevance to a target resume.

Unlike a simple scraper, this system is a **full data pipeline + recommendation engine + observability layer**.

It is designed to:

* Collect job listings from multiple platforms
* Deduplicate and persist structured data
* Analyze job relevance using NLP (embedding + keyword scoring)
* Rank jobs using a hybrid scoring engine
* Provide real-time monitoring and analytical dashboards
* Generate structured reports for decision-making

---

## 🌐 Live Demo
👉 **Streamlit Dashboard:**
[https://jobvision-analyzer.streamlit.app/](https://jobvision-analyzer.streamlit.app/)

---

## 🚀 System Evolution

This system evolved through multiple architectural stages:

| Version | Description                                            |
| ------- | ------------------------------------------------------ |
| v1      | Simple scraping script                                 |
| v2      | Basic NLP matching (TF-IDF)                            |
| v3      | Multi-site scraping pipeline                           |
| v4      | Hybrid scoring (embedding + keyword)                   |
| v5      | SQLite persistence + deduplication                     |
| v6      | Advanced scoring engine (v63 logic)                    |
| v7      | Observability + caching + dashboard + partial recovery |

---

## 🏗️ System Architecture

```text
                ┌──────────────────────┐
                │   Job Sources        │
                │ (Jobvision, etc.)    │
                └─────────┬────────────┘
                          │
                ┌─────────▼────────────┐
                │   Scraping Layer     │
                │ (Selenium Crawlers)  │
                └─────────┬────────────┘
                          │
                ┌─────────▼────────────┐
                │   Cache Layer        │
                │ (Fast dedup lookup)  │
                └─────────┬────────────┘
                          │
                ┌─────────▼────────────┐
                │  Database Layer      │
                │   (SQLite)           │
                └─────────┬────────────┘
                          │
                ┌─────────▼────────────┐
                │ NLP Feature Engine   │
                │ - Embeddings         │
                │ - TF-IDF             │
                │ - Keyword scoring    │
                └─────────┬────────────┘
                          │
                ┌─────────▼────────────┐
                │ Scoring Engine v63   │
                │ Hybrid ranking model │
                └─────────┬────────────┘
                          │
        ┌─────────────────▼──────────────────┐
        │ Outlier Detection + Normalization │
        └─────────────────┬──────────────────┘
                          │
        ┌─────────────────▼──────────────────┐
        │ Output Layer                      │
        │ JSON + HTML Reports              │
        └─────────────────┬──────────────────┘
                          │
        ┌─────────────────▼──────────────────┐
        │ Observability Layer              │
        │ Monitor + Dashboard              │
        └───────────────────────────────────┘
```

---

## ⚙️ Key Features

### 🔄 Multi-Source Scraping

* Jobvision (multiple categories)
* Extensible scraper architecture
* Selenium-based crawling with retry handling

---

### 🧠 NLP Matching Engine

* Sentence Transformers (MiniLM)
* TF-IDF similarity scoring
* Keyword-based skill extraction
* Resume-to-job semantic matching

---

### 🎯 Scoring System (Hybrid Model)

Final score is computed using:

* Embedding similarity score
* TF-IDF similarity score
* Keyword match score
* Category weighting (technical vs general)
* Boost / penalty system
* Outlier adjustment

---

### 📊 Job Classification

Jobs are automatically categorized into:

* 🔧 Technical (Software, AI, Data, DevOps)
* 🧾 General (Office, Admin, HR, Communication)
* 🔀 Hybrid (Mixed skill requirements)

---

### 🗄️ Data Persistence Layer

* SQLite database storage
* Duplicate detection (URL-based + hash-based)
* Structured job normalization
* Historical tracking of jobs

---

### ⚡ Cache System

* Local caching of scraped job lists
* Fast duplicate detection before DB query
* Reduces scraping overhead significantly

---

### 📡 Observability Layer

* `monitor.py` → real-time database inspection
* `dashboard.py` → analytical visualization interface
* `tqdm` progress tracking for long-running jobs
* partial JSON saves for crash recovery

---

## 📊 Outputs

### 📦 JSON Output

Includes:

* Final score
* Technical score
* General score
* Embedding score
* TF-IDF score
* Matched skills
* Category classification
* Outlier score

---

### 🌐 HTML Report

* Ranked job list
* Category breakdown
* Skill highlights
* Top-K recommendations
* Clean dashboard-style UI

---

## 🔄 Data Lifecycle

1. Scrape job listings from multiple sources
2. Cache raw job batches
3. Deduplicate against database
4. Store normalized jobs in SQLite
5. Extract NLP features
6. Compute hybrid relevance score
7. Rank and classify jobs
8. Generate structured reports
9. Monitor system state in real-time

---

## 🧮 Scoring Formula (Conceptual)

```text
Final Score =
(Embedding Similarity × W1) +
(TF-IDF Similarity × W2) +
(Keyword Score × W3) +
(Category Weight) +
(Boost - Penalty)
```

Weights are dynamically adjustable depending on configuration.

---

## 🛠️ Tech Stack

| Layer      | Technology                            |
| ---------- | ------------------------------------- |
| Language   | Python 3.11                           |
| Scraping   | Selenium                              |
| NLP        | sentence-transformers                 |
| ML/Stats   | scikit-learn, numpy                   |
| Storage    | SQLite                                |
| UI         | HTML + Dashboard (Streamlit / custom) |
| Monitoring | Custom monitor module                 |
| Pipeline   | Modular Python architecture           |

---

## 📁 Project Structure

```text
job-scraper/
│
├── core/                 # Pipeline engine
├── matcher/             # NLP + scoring logic
├── scrapers/            # Web scraping layer
├── utils/               # Helpers, DB, drivers
├── config/              # Settings + resume
├── cache/               # Cache layer
├── data/                # SQLite DB
├── output/              # Reports (JSON/HTML)
├── partial/             # Crash recovery data
├── report/              # Report generator
│
├── dashboard.py         # UI dashboard
├── monitor.py           # Live DB viewer
├── main.py              # Entry point
└── README.md
```

---

## 🚀 Getting Started

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run system

```bash
python main.py
```

### 3. Optional components

* Live monitoring:

```bash
python monitor.py
```

* Dashboard:

```bash
python dashboard.py
```

---

## 📈 Performance Notes

* ~3000+ jobs processed per run
* ~4–7 jobs/sec scoring speed
* Multi-stage caching reduces redundant scraping
* DB-based dedup prevents reprocessing

---

## 📌 Current System State

This system is no longer a simple scraper.

It is a:

> **Job Intelligence & Ranking Pipeline with Observability and Persistence Layer**

---

## 👤 Author

**Ali Eisapour Sharabiani**

Software Engineer
Python | AI | Data Systems | Embedded Systems

---
