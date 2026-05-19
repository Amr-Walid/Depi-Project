# CryptoPulse Deployment Resolution & Troubleshooting Log

This document records the comprehensive technical investigation, debugging steps, and final resolutions applied to the **CryptoPulse** platform. These changes successfully resolved frontend compilation failures, repository exclusion bugs, path aliasing anomalies, authentication errors, runtime component crashes, and chart visualization gaps. 

The final system is fully integrated end-to-end: **Next.js Frontend + FastAPI Backend + Supabase/PostgreSQL Database + Spark ETL Sequential Pipeline**.

---

## 1. System Context & Active Services
* **Backend API Server**: FastAPI running on WSL (`http://localhost:8000`) connected to PostgreSQL.
* **Frontend Dashboard**: Next.js 15 (Turbopack) running on WSL (`http://localhost:3000`).
* **ETL Engine**: PySpark sequential pipeline processing Binance API & Sentiment raw data into PostgreSQL layers (`silver` and `gold`).

---

## 2. Issues Investigated & Resolved

### Issue 1: WSL Node & LightningCSS Build Errors
* **Symptoms**: Next.js failed to start inside the WSL shell, throwing:
  `Error: Cannot find module '../lightningcss.linux-x64-gnu.node'`
* **Root Cause**: Next.js cached builds (`.next/`) and node modules were mixed between the host Windows environment and the guest Linux (WSL) environments, resulting in binary incompatibilities for platform-specific builds like `lightningcss`.
* **Resolution**: 
  1. Purged the `.next` cache directory and `node_modules` inside WSL.
  2. Forced a native Linux packages installation using `/usr/bin/npm install` within WSL to ensure correct platform binaries.

---

### Issue 2: Missing Core Source Files (`frontend/lib/`) on GitHub
* **Symptoms**: The developer pulled updates but faced compilation errors because critical utility files like `api-client.ts` and `utils.ts` were missing from the filesystem.
* **Root Cause**: The repository's root `.gitignore` had a global rule `/lib/` intended to ignore python virtual environment library folders. However, it implicitly excluded the frontend's source folder `frontend/lib/`, preventing it from ever being tracked or pushed to GitHub.
* **Resolution**:
  * Anchored the `/lib/` rule to the root level by changing it to `/.lib/` or scoping it carefully in the root `.gitignore`.
  * Tracked, committed, and successfully pushed the `frontend/lib/api-client.ts` and `frontend/lib/utils.ts` files to the main branch.

---

### Issue 3: Path Aliasing Bug (`@/*`) under Turbopack
* **Symptoms**: Next.js compilation crashed with:
  `Module not found: Can't resolve '@/lib/api-client'`
* **Root Cause**: Next.js Turbopack failed to resolve path aliases defined with `@/*` inside WSL because compiler resolution configurations were underspecified.
* **Resolution**:
  * Updated `frontend/tsconfig.json` to explicitly define both the `baseUrl` and strict folder mappings under the `paths` property:
    ```json
    "baseUrl": ".",
    "paths": {
      "@/*": ["./*"]
    }
  ```

---

### Issue 4: Authentication Blockers & Mockup Page Fallbacks (401 Unauthorized)
* **Symptoms**: Dashboard metrics displayed as `$0` (flat) and backend console printed `401 Unauthorized`.
* **Root Cause**: The dashboard API endpoints require token-based authentication (`Authorization: Bearer <token>`). The user registered and logged in through `/sign-up-1` and `/sign-in-1`. However, those routes are purely static UI design templates (mockups) and did not communicate with the FastAPI backend, thus leaving the browser with no security token.
* **Resolution**:
  1. Created a database-backed, secure account `amrw0109@gmail.com` by sending a direct server-side `POST` request to `/api/v1/auth/signup` on the FastAPI backend.
  2. Instructed the user to sign in through the **real, backend-wired route**: **`http://localhost:3000/sign-in`** (no trailing suffix). 
  3. This stored the JWT access token in the browser's `localStorage`, granting successful access to the endpoints.

---

### Issue 5: Runtime Avatar Fallback Crash (`Cannot read properties of undefined`)
* **Symptoms**: Upon successful login, the frontend crashed with a white screen showing:
  `TypeError: Cannot read properties of undefined (reading 'split')` at `NavUser (nav-user.tsx)` and `ProfileDropdown (profile-dropdown.tsx)`.
* **Root Cause**: The backend-created user did not have optional profile parameters like `first_name` or `last_name` populated, so the API returned a null/undefined `user.name`. Both components were calling `user.name.split(" ")` to generate initials for the profile avatar.
* **Resolution**:
  * Patched both components defensively. Replaced `user.name.split()` with `(user.name || user.email || "U").split()` to handle missing name profiles gracefully by falling back to the email prefix:
    ```diff
    -  const initials = user.name.split(" ")...
    +  const initials = (user.name || user.email || "U").split(" ")...
    ```

---

### Issue 6: Coin Symbol Mapping Gap (404 Not Found)
* **Symptoms**: The central BTC price chart was completely blank, and the FastAPI backend printed:
  `GET /api/v1/coins/BTC/summary HTTP/1.1 404 Not Found`
* **Root Cause**: The frontend queried the backend using the short symbol `BTC`, but all pipeline metrics, database rows, and backend supported configs are explicitly mapped to target trading pairs like `BTCUSDT` (ending in `USDT`).
* **Resolution**:
  * Updated the backend's query logic in `backend/app/services/data_service.py` inside `get_coin_summary` and `get_coin_prices` to normalize short coin symbols to their trade pair equivalent if the suffix is missing:
    ```python
    symbol = symbol.upper()
    if not symbol.endswith("USDT") and f"{symbol}USDT" in SUPPORTED_COINS:
        symbol = f"{symbol}USDT"
    ```

---

### Issue 7: Empty Chart Area (Recharts Data Key Mismatch)
* **Symptoms**: X-axis labels and pricing metrics showed up successfully, but the line/area graph remained blank.
* **Root Cause**: The frontend area chart (`ChartAreaInteractive`) is configured to render price lines using the key `price`. However, the PostgreSQL historical prices query in the backend returned records under the key `close` (representing the day's close price).
* **Resolution**:
  * Updated `frontend/hooks/use-coins.ts` in the `useCoinDetail` hook to dynamically map the incoming backend data model `close` price to the expected UI `price` key:
    ```typescript
    const mappedHistory = (historyData.prices || []).map((p: any) => ({
      ...p,
      price: p.close || p.price || 0,
    }));
    setHistory(mappedHistory);
    ```

---

## 3. Final Verification Status

All systems have been fully verified and are rendering perfectly:
* **`GET /api/v1/market/overview`** ➡️ `200 OK` (Pulls active coins, total volume, market cap aggregate).
* **`GET /api/v1/market/sentiment`** ➡️ `200 OK` (Pulls aggregated news & social indicators).
* **`GET /api/v1/coins/BTC/summary`** ➡️ `200 OK` (BTC price and day summary successfully load).
* **`GET /api/v1/coins/BTC/prices?days=30`** ➡️ `200 OK` (30-day historical prices render the line chart beautifully).

### System Metric Snapshot:
* **Active Coins**: 20
* **Total Market Cap**: $136.38 Billion
* **24h Volume**: $9.09 Billion
* **Bitcoin Benchmark Price**: $72,965.36 USD
* **Market Sentiment**: Neutral

---
*Log documented and committed on May 19, 2026.*
