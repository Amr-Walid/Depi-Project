<div align="center">

# 💻 Crypto-Pulse Frontend Dashboard

### Premium Real-Time Analytics Web Application Built on Next.js, Zustand & Shadcn UI

[![Next.js](https://img.shields.io/badge/Next.js_15-000000?style=for-the-badge&logo=nextdotjs)](https://nextjs.org)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS_v4-06B6D4?style=for-the-badge&logo=tailwindcss)](https://tailwindcss.com)
[![ShadcnUI](https://img.shields.io/badge/Shadcn_UI-000000?style=for-the-badge&logo=shadcnui)](https://ui.shadcn.com)
[![Zustand](https://img.shields.io/badge/Zustand-443e38?style=for-the-badge)](https://zustand-demo.pmnd.rs)

</div>

---

## 📋 Table of Contents
1. [Overview](#-overview)
2. [Key Features](#-key-features)
3. [Technology Stack](#-technology-stack)
4. [Folder Architecture](#-folder-architecture)
5. [User Interface Modules](#-user-interface-modules)
6. [API & AI Chat Integration](#-api--ai-chat-integration)
7. [Installation & Development Setup](#-installation--development-setup)
8. [Docker Production Build](#-docker-production-build)

---

## 🔍 Overview

The frontend of **Crypto-Pulse** is an interactive, fully responsive analytical dashboard built using the **Next.js App Router** architecture. It displays real-time price updates (connected to the FastAPI backend), charts historical trends, manages user watchlists/portfolios, and features an integrated AI Assistant powered by **Google Gemini** via the Vercel AI SDK.

---

## ✨ Key Features

- 📊 **Real-time Price Grid**: Updates dynamically as live data aggregates in the Supabase PostgreSQL database.
- 📈 **Advanced Analytics Engine**: High-fidelity charts showing historical open, high, low, close, and volume (OHLCV) metrics with custom range selections.
- 🤖 **Interactive AI Assistant**: Real-time market analysis chatbot powered by Gemini models for instant market research and advisory logs.
- ⭐ **Custom Watchlists**: Add or remove monitored cryptocurrency pairs on the fly.
- 💼 **Portfolio Accounting**: Input purchases (shares, entry price) to track profit margins and live valuation.
- 🔔 **Threshold Price Alerts**: Add above/below value monitors that trigger updates once crossed.
- 🌓 **Adaptive Theming**: Beautiful dark/light mode toggle utilizing Tailwind CSS.

---

## 🛠️ Technology Stack

| Library / Tool | Role | Version |
| :--- | :--- | :---: |
| **Next.js** | Core React Framework (App Router & Server Actions) | `^15` |
| **Tailwind CSS** | Premium component layouts and style compilation | `^4` |
| **Shadcn UI + Radix** | Accessible, custom-themed interactive elements | Latest |
| **Zustand** | Lightweight, high-performance global state engine | `^4.5` |
| **Recharts** | Interactive SVG-based data line and bar charting | `^2.12` |
| **Vercel AI SDK** | Hook integrations connecting stream responses to Gemini | `^3.0` |

---

## 🏗️ Folder Architecture

```
frontend/
├── app/                        # Next.js App Router (pages and server logic)
│   ├── layout.tsx              # Root HTML wrapper, global font loads, and theme providers
│   ├── page.tsx                # Main Dashboard entry point
│   ├── login/                  # Login page & authentication forms
│   └── register/               # Signup page & validation handlers
├── components/                 # Shared UI elements
│   ├── ui/                     # Shadcn components (Button, Input, Dialog, etc.)
│   ├── navbar.tsx              # Navigation header containing theme toggle & auth indicators
│   ├── market-table.tsx        # Dashboard prices grid
│   └── crypto-chart.tsx        # Recharts historical visualization component
├── contexts/                   # React context providers (AuthContext, ThemeContext)
├── hooks/                      # Custom hooks (e.g. useAuth, useMarketData)
├── lib/                        # Utility clients (axios custom instance, Gemini config)
├── utils/                      # Formatting helpers (currency formatting, date formatters)
├── public/                     # Static media files and assets (icons, brand logos)
├── package.json                # Project dependencies and script files
├── tailwind.config.ts          # Styling tokens
└── tsconfig.json               # TypeScript compiler config
```

---

## 📊 User Interface Modules

### 1. Market Tickers Grid
Displays a clean table listing the 20 tracked cryptocurrencies with real-time updates. Highlights 24h percent changes in red or green.

### 2. Historical Candle Charts
Integrates Recharts with interactive tooltips. Users can toggle time horizons (e.g., 24 Hours, 7 Days, 30 Days, 1 Year) to pull historical OHLCV data from the backend APIs.

### 3. AI Advisory Panel
A floating sidebar component housing a conversational chatbot UI. It provides market analysis reports and cryptocurrency insights using the Gemini model APIs.

---

## 🔌 API & AI Chat Integration

The frontend links to the backend REST API endpoints via a centralized Axios client.

```
┌─────────────────────────────────┐
│       Next.js Frontend          │
├─────────────────────────────────┤
│                                 │
│   ─── JWT Auth Token ─────────► │    ┌────────────────────────┐
│   ─── Fetch Chart History ────► │───►│  FastAPI Backend API   │
│                                 │    └────────────────────────┘
│   ─── Prompt Stream ──────────► │    ┌────────────────────────┐
│                                 │───►│    Gemini API Model    │
└─────────────────────────────────┘    └────────────────────────┘
```

The system secures standard HTTP queries and routes prompts to Gemini to provide text responses directly in the UI.

---

## 🚀 Installation & Development Setup

### ⚙️ Prerequisites
*   Node.js 22+
*   npm or pnpm package manager

### 📦 Steps
1.  Navigate to the frontend folder:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Configure your environment file (`frontend/.env`):
    ```env
    NEXT_PUBLIC_API_URL=http://localhost:8000
    GOOGLE_GENERATIVE_AI_API_KEY=your_google_gemini_api_key
    ```
4.  Launch the development server:
    ```bash
    npm run dev
    ```
5.  Access the web application at: `http://localhost:3000`

---

## 🐳 Docker Production Build

To containerize and run the frontend inside a Docker network:

1.  Build the image:
    ```bash
    docker build -t cryptopulse-frontend .
    ```
2.  Run the container:
    ```bash
    docker run -d -p 3000:3000 --name frontend-app --env-file .env cryptopulse-frontend
    ```
