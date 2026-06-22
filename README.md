## 📝 **نسخه جدید `README.md` (انگلیسی)**

```markdown
# 🎯 AI Job Matcher - Reverse ATS

[![GitHub Actions](https://github.com/Aliesapour79/job-scraper/actions/workflows/job-matcher.yml/badge.svg)](https://github.com/Aliesapour79/job-scraper/actions)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**An intelligent automated system for matching job listings with your resume.**

---

## 🎯 **What is it?**

**AI Job Matcher** is a personal tool that:
- 🔍 Scrapes job listings from **multiple job portals**
- 🧠 Matches them with your resume using **AI & NLP**
- 📊 Ranks the best opportunities
- 📧 Sends **automated reports** to you

This is built as a **personal decision-support tool**, not a commercial SaaS product.

---

## ✨ **Features**

| Feature | Description |
|---------|-------------|
| 🔄 **Multi-Site Scraping** | Supports e-estekhdam & Jobvision (extensible) |
| 🧠 **Smart Matching** | Hybrid TF-IDF + Embedding + Semantic Matching |
| 🎯 **Dual-Track Scoring** | Separate scoring for Technical & Administrative jobs |
| 🏷️ **Auto Categorization** | Detects Technical / Administrative / Hybrid |
| 📊 **Professional Reporting** | HTML + JSON output with full analysis |
| 🤖 **Outlier Detection** | Identifies outstanding and unusual job matches |
| ⏰ **Automated Execution** | Runs every 6 hours on GitHub Actions |
| 📱 **Telegram Notifications** | Auto-sends results to your Telegram |

---

## 🧠 **System Architecture**

### 1. **Data Collection Layer**
- Uses **Selenium** for dynamic site scraping
- Supports: `e-estekhdam` and `Jobvision`
- Scrapes **all pages** within a job category

### 2. **NLP Processing Layer**
- **TF-IDF Similarity**: Text similarity between resume and job
- **Semantic Embedding**: Uses `paraphrase-multilingual-MiniLM-L12-v2`
- **Keyword Matching**: Domain-specific keyword detection

### 3. **Dual-Track Scoring System**

#### 🔧 **Technical Track**
- Programming (Python, C++, ...)
- AI & Machine Learning
- IoT & Electronics
- Networking & DevOps
- Data Analysis

#### 🧾 **General Track**
- Office Skills (Word, Excel, ...)
- Management & Coordination
- Reporting & Documentation
- Communication & Support

### 4. **Final Scoring Engine**

```
Final Score = (Technical Score × 0.7) + (General Score × 0.3)
             + Boost - Penalty
```

### 5. **Advanced Outlier Detection**
- Hybrid **Z-Score + Percentile** method
- Auto-detects **Skewness** in data distribution
- Intelligently chooses calculation method based on data

---

## 📂 **Project Structure**

```
job-scraper/
├── config/                         # Settings & Resume
│   ├── __init__.py
│   ├── resume.py                   # Your resume (separate from code)
│   └── settings.py                 # Weights & filters
│
├── matcher/                        # Core matching engine
│   ├── __init__.py
│   ├── score_calculator.py         # Score calculation
│   ├── semantic_matcher.py         # Embedding model
│   └── skill_groups.py             # Skill groups
│
├── report/                         # Report generation
│   ├── __init__.py
│   └── html_generator.py           # HTML output
│
├── scrapers/                       # Site-specific scrapers
│   ├── __init__.py
│   ├── e_estekhdam_scraper.py      # e-estekhdam scraper
│   └── jobvision_scraper.py        # Jobvision scraper
│
├── utils/                          # Shared utilities
│   ├── __init__.py
│   └── driver.py                   # Browser management
│
├── main.py                         # Main entry point
├── requirements.txt                # Dependencies
├── .github/
│   └── workflows/
│       └── job-matcher.yml         # Auto-run on GitHub Actions
└── README.md
```

---

## ⚙️ **Configuration**

### `config/settings.py`

```python
# Hybrid weights
SCORE_WEIGHTS = {
    'tfidf': 0.30,      # 30% TF-IDF
    'embedding': 0.70   # 70% Embedding
}

# Domain weights
INTENT_WEIGHTS = {
    'technical': 0.70,
    'general': 0.30
}

# Filters
FILTERS = {
    'min_score': 20,
    'top_n_results': 25
}
```

### `config/resume.py`

Your resume is stored as plain text, easy to edit and update.

---

## 📊 **Outputs**

### 1. **JSON Output**
Complete data for each job:
- Final score with breakdown
- Job category
- Matched skills
- Outlier score

### 2. **HTML Report**
A clean, interactive report with:
- Ranked job cards
- Separate sections (Technical / Admin / Hybrid)
- Skill visualization
- Outlier indicators
- Group analysis bars

---

## 🚀 **How to Run**

### 1. **Install Dependencies**

```bash
pip install -r requirements.txt
```

### 2. **Run Manually**

```bash
python main.py
```

### 3. **Automated Run (GitHub Actions)**

The system is configured to run **every 6 hours** and send results to Telegram.

---

## 🔧 **Requirements**

- Python 3.11+
- Chrome Browser (for Selenium)
- Internet connection

---

## 🧪 **Tech Stack**

| Technology | Purpose |
|------------|---------|
| **Python** | Core language |
| **Selenium** | Web scraping |
| **Sentence Transformers** | Embedding models |
| **Scikit-learn** | TF-IDF & statistics |
| **NumPy** | Numerical computation |
| **GitHub Actions** | Automation |
| **Telegram API** | Notifications |

---

## 📈 **Version History**

| Version | Changes |
|---------|---------|
| **v6.3** | Dual-Track + Hybrid Scoring System |
| **v6.2** | Improved Outlier Detection (Hybrid Z-Score + Percentile) |
| **v6.1** | Added Multi-Intent Scoring |
| **v6.0** | Complete modular architecture refactor |

---

## 👤 **Author**

**Ali Eisapour Sharabiani**  
Software Engineer | Python Developer | AI / Computer Vision | IoT & Embedded Systems

---
