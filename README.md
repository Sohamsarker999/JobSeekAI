# 📊 JobSeekAI — Bangladesh Job Market Intelligence

A production-grade Streamlit analytics dashboard that analyses job postings in Bangladesh and delivers skill-demand insights, salary analytics, and AI-powered market intelligence.

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Features

| Module | Description |
|---|---|
| **Skill Frequency Analysis** | Parses, normalises, and ranks the top 15 in-demand skills |
| **Salary Distribution** | Histogram + KDE and box-plot breakdowns with BDT formatting |
| **Interactive Filters** | Sidebar multi-select for industry, role, and location |
| **AI Market Summary** | Groq LLM generates an executive brief from live analytics |

---

## Project Structure

```
JobSeekAI/
├── app/
│   ├── main.py              # Streamlit entry point
│   ├── utils.py              # Data loading, cleaning, metrics
│   ├── visualizations.py     # Chart rendering (matplotlib/seaborn)
│   ├── ai_summary.py         # Groq API integration
│   └── data/
│       └── job_postings.csv  # Sample dataset (100 postings)
├── .env.example              # API key template
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Clone & Install

```bash
git clone <repo-url>
cd JobSeekAI
pip install -r requirements.txt
```

### 2. Set Your Groq API Key

Get a free key at [console.groq.com/keys](https://console.groq.com/keys), then:

```bash
cp .env.example .env
# Edit .env and paste your key
```

Or export directly:

```bash
export GROQ_API_KEY="gsk_your_key_here"
```

### 3. Run the App

```bash
cd JobSeekAI
streamlit run app/main.py
```

The dashboard opens at **http://localhost:8501**.

---

## Configuration

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | For AI summary | Free tier available at console.groq.com |

The app works fully without the API key — only the AI Market Summary section requires it.

---

## Data Format

The CSV must contain these columns:

| Column | Type | Example |
|---|---|---|
| `job_title` | string | Software Engineer |
| `company` | string | Grameenphone |
| `salary_min` | numeric | 45000 |
| `salary_max` | numeric | 75000 |
| `skills` | comma-separated | Python, Django, REST API |
| `industry` | string | Telecommunications |
| `location` | string | Dhaka |

---

## Tech Stack

- **Frontend**: Streamlit
- **Data**: pandas
- **Visualisation**: matplotlib + seaborn
- **AI**: Groq API (Llama 3.3 70B)
- **Language**: Python 3.9+
