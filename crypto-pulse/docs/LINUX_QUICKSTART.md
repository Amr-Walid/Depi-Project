# 🐧 CryptoPulse — دليل التشغيل السريع لبيئة لينكس (Lightweight)

تم تصميم هذا الدليل لتشغيل مشروع CryptoPulse على الأجهزة ذات الموارد المحدودة. سيتم تخطي تشغيل خدمات (Spark, Kafka, Zookeeper, Airflow) واستخدام سكربتات خفيفة ومباشرة لنقل البيانات ومعالجتها.

## 📋 المتطلبات الأساسية
- Python 3.8+
- Node.js 18+
- (اختياري) حساب Supabase للحصول على قاعدة البيانات
- (اختياري) NewsAPI Key للحصول على أخبار حقيقية

## 🚀 خطوة بخطوة للتشغيل الشامل

### 1️⃣ تثبيت المتطلبات (Requirements)
أولاً، نحتاج لتثبيت مكتبات بايثون الأساسية للسكربتات الخفيفة والـ dbt:
```bash
pip install -r req_main.txt
```

### 2️⃣ إعداد الجداول (Schema Setup)
السكربت ده هيبني كل الجداول المطلوبة في Supabase (سواء الخاصة باليوزرز أو الـ Silver Layer):
```bash
python scripts/setup_supabase_schema.py
```

### 3️⃣ حقن البيانات المباشر (Direct Seed)
بدل ما نستخدم Spark و Kafka، السكربت ده هيحقن الداتا مباشرة في Supabase:
- **Historical**: من ملفات JSON المحلية
- **Prices**: من Binance API (أو بيانات عشوائية لو فشل)
- **News**: من NewsAPI (لو الـ Key موجود في .env) أو بيانات عشوائية
- **Social**: من RSS Feeds (CoinTelegraph)
- **Sentiment**: محاكاة لنتائج FinBERT

```bash
python scripts/seed_supabase_direct.py
```

### 4️⃣ بناء طبقة Gold (dbt run)
هنبني الجداول النهائية اللي الداشبورد هيقرأ منها:
```bash
cd processing/dbt
dbt run
dbt test
cd ../..
```

### 5️⃣ تشغيل الباك إند (FastAPI)
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# هيشتغل على: http://localhost:8000
```

### 6️⃣ تشغيل الفرونت إند (Next.js)
في تيرمنال تاني:
```bash
cd frontend
npm install
npm run dev
# هيشتغل على: http://localhost:3000
```

---

## ⚡ التشغيل الأوتوماتيكي بالكامل (All-in-One)
بدل ما تشغل كل خطوة لوحدها، عملنالك سكربت بيعمل كل حاجة ورا بعض:

```bash
# تشغيل كل الخطوات (من 1 لـ 4) ثم تشغيل السيرفرات
chmod +x scripts/run_pipeline.sh
./scripts/run_pipeline.sh all
```

لو عاوز تشغل السيرفرات بس:
```bash
./scripts/run_pipeline.sh start
```

---

## 🐋 استخدام Docker Compose (نسخة خفيفة)
لو جهازك يستحمل تشغيل الباك والفرونت في Docker، ممكن تستخدم النسخة الخفيفة:
```bash
docker compose -f docker-compose.lightweight.yml up -d
```
> **ملاحظة:** تأكد إنك نفذت خطوات حقن البيانات (2, 3, 4) الأول عشان الداشبورد يشتغل صح.
