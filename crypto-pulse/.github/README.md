# 🛠️ GitHub Actions CI/CD Pipeline

Welcome to the GitHub configurations directory. This directory holds the continuous integration (CI) and continuous deployment (CD) workflows for the **Crypto-Pulse** project.

---

## 📂 Directory Structure

```
.github/
└── workflows/
    └── ci-cd.yml      # Main CI/CD pipeline definition
```

---

## 🚀 Workflow Overview

The CI/CD pipeline is defined in `.github/workflows/ci-cd.yml`. It is designed to ensure code quality and system integrity by running automated suites whenever a developer pushes code or submits a pull request.

### ⏱️ Triggers

| Event | Branches | Description |
| :--- | :--- | :--- |
| `push` | `main`, `dev` | Triggers on code push to main or development branch. |
| `pull_request` | `main`, `dev` | Triggers when a pull request is opened or updated targeting main/dev. |

---

## 🧱 Job Details

The workflow is divided into two parallel, independent jobs:

### 1. 🐍 Backend Test Suite (`backend-test`)
Spins up a temporary database service and runs the complete FastAPI test suite.
*   **Operating System**: `ubuntu-latest`
*   **Database Container**: PostgreSQL 15 (`postgres:15`)
*   **Python Version**: `3.10`
*   **Tasks**:
    1. Check out repository code.
    2. Install python dependencies from `backend/requirements.txt` along with testing utilities (`pytest`, `httpx`).
    3. Run pytest inside the `backend` directory.

### 2. ⚛️ Frontend Lint & Build (`frontend-build`)
Ensures Next.js frontend code is clean, linted, and builds successfully.
*   **Operating System**: `ubuntu-latest`
*   **Node.js Version**: `22` (cached npm)
*   **Tasks**:
    1. Check out repository code.
    2. Install dependencies using `npm ci`.
    3. Run ESLint static analysis tool (`npm run lint`).
    4. Compile the production Next.js static asset build (`npm run build`).

---

## 🔒 Required Secret Keys

The frontend build job references the following secret, which should be configured in GitHub Repository Secrets (`Settings > Secrets and variables > Actions`):

*   `GOOGLE_GENERATIVE_AI_API_KEY`: Required by the Next.js app to interact with Gemini API models for generating user-oriented reports or market insights.
