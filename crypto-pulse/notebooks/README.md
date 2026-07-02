# notebooks/ - Jupyter Notebooks

This directory contains Jupyter notebooks used for exploratory data analysis (EDA), model verification, and proof-of-concept (PoC) dashboard mockups.

---

## 📂 Notebook Index

The directory contains four structured notebooks designed to trace the development and verification phases of the project:

| File Name | Phase | Key Libraries | Description |
| :--- | :--- | :--- | :--- |
| **`01-data-exploration.ipynb`** | EDA | `pandas`, `matplotlib`, `seaborn` | Analyzes historical OHLCV data, calculates price correlations, standardizes dates, and plots rolling volume trends. |
| **`02-model-training.ipynb`** | ML Verification | `transformers`, `torch` | Sets up a local test environment for the `ProsusAI/finbert` classifier model. Tokenizes headlines, evaluates classifications, and inspects output vectors. |
| **`03-poc-dashboard.ipynb`** | Prototyping | `plotly`, `pandas` | Initial proof-of-concept visual renderings. Tests candlestick charting, price changes, and layout proportions. |
| **`03-sentiment-dashboard.ipynb`**| Dashboard | `plotly`, `dash` | An interactive sentiment timeline dashboard. Links article timestamps with sentiment values, compiling rolling sentiment metrics and bull/bear labels. |

---

## 🚀 How to Run the Notebooks

### ⚙️ Prerequisites
Ensure you have Jupyter installed alongside the required analysis libraries:
```bash
pip install jupyter pandas matplotlib seaborn plotly dash transformers torch
```

### 🏃‍♂️ Running
Start the Jupyter Notebook server from this directory:
```bash
cd notebooks
jupyter notebook
```
Select any notebook from the browser list to review the data workflows and execution logs.
