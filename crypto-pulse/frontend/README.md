# 🚀 CryptoPulse Frontend

Welcome to the **CryptoPulse** frontend, a high-performance, real-time cryptocurrency analytics dashboard built with **Next.js 16**, **Tailwind CSS v4**, and **Shadcn UI**.

This dashboard provides a premium experience for monitoring crypto markets, managing portfolios, and analyzing market sentiment using AI.

## ✨ Features

- 📊 **Real-time Market Dashboard**: Live price updates and market overview.
- 📈 **Advanced Analytics**: Interactive OHLCV charts and technical indicators.
- 🤖 **AI Assistant**: Intelligent chat for market analysis and crypto queries.
- ⭐ **Watchlist**: Track your favorite coins in one place.
- 💼 **Portfolio Tracker**: Manage your holdings and track profits/losses.
- 🔔 **Price Alerts**: Get notified when coins hit your target price.
- 🌗 **Dark Mode**: Beautiful, modern UI with theme customization.

## 🛠️ Tech Stack

- **Framework**: Next.js 16 (App Router)
- **Styling**: Tailwind CSS v4
- **UI Components**: Shadcn UI + Radix UI
- **State Management**: Zustand
- **AI Integration**: Vercel AI SDK + Google Gemini
- **Charts**: Recharts
- **Icons**: Lucide React + Tabler Icons

## 🚀 Getting Started

### 1. Prerequisites

- Node.js 22+
- npm or pnpm

### 2. Environment Setup

Create a `.env` file in this directory and add the following:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
GOOGLE_GENERATIVE_AI_API_KEY=your_gemini_api_key
```

### 3. Install Dependencies

```bash
npm install
```

### 4. Run Development Server

```bash
npm run dev
```

The app will be available at [http://localhost:3000](http://localhost:3000).

## 🐳 Docker Support

Build and run the frontend using Docker:

```bash
docker build -t cryptopulse-frontend .
docker run -p 3000:3000 --env-file .env cryptopulse-frontend
```

---

*Part of the CryptoPulse Data Engineering Project.*
