# 👑 عمرو وليد — Team Lead & Lead Data Engineer

> **الدور:** قائد الفريق + مهندس البيانات الرئيسي  
> **المسؤولية الجوهرية:** الرؤية المعمارية، البنية التحتية على Azure، وضمان تكامل المشروع

---

## 🏁 Milestone 1 — تأسيس البنية التحتية وتأمين المشروع

**الهدف:** بناء "الهيكل العظمي" للمشروع بأكمله، من GitHub إلى Azure، وتوفير الأدوات اللازمة للفريق للبدء في العمل.

---

### ✅ Task 1.1 — إنشاء وتنظيم مستودع GitHub

**الملفات المتأثرة:**
- `📁 crypto-pulse/` ← الهيكل الكامل للمشروع

**ما تم إنجازه:**
- [x] إنشاء المستودع على GitHub
- [x] إنشاء الهيكل الكامل للمجلدات (ingestion, processing, dags, backend, ml, notebooks...)
- [x] إعادة هيكلة المشروع ليتبع معمارية Medallion (Bronze → Silver → Gold)
- [x] رفع الملفات الأساسية على الـ main/dev branch

---

### ✅ Task 1.2 — إعداد ملفات الجذر (Root Configuration Files)

**الملفات المتأثرة:**
- `.gitignore`
- `.env.example`
- `requirements.txt`

**ما تم إنجازه:**
- [x] إنشاء `.gitignore` يشمل: `.env`, `__pycache__`, `*.pyc`, `data/historical/`, ملفات النماذج الكبيرة
- [x] إنشاء `.env.example` كقالب واضح لجميع أعضاء الفريق يحتوي على:
  - `AZURE_CLIENT_ID`
  - `AZURE_CLIENT_SECRET`
  - `AZURE_TENANT_ID`
  - `AZURE_STORAGE_ACCOUNT_NAME`
  - `AZURE_STORAGE_CONTAINER_NAME`
  - `KAFKA_BOOTSTRAP_SERVERS`
  - `KAFKA_TOPIC_REALTIME_PRICES`
- [x] إنشاء `requirements.txt` الأولي

---

### ✅ Task 1.3 — بناء البنية التحتية على Azure

**ما تم إنجازه:**
- [x] إنشاء **Resource Group**: `rg-cryptopulse-dev`
- [x] إنشاء **Storage Account (ADLS Gen2)**: `stcryptopulsedev`
- [x] إنشاء **Container**: `datalake`
- [x] إنشاء **Service Principal**: `sp-cryptopulse` بصلاحيات `Storage Blob Data Contributor`
- [x] مشاركة بيانات الاعتماد بشكل آمن مع الفريق

> **ملاحظة مستمرة:** أنت نقطة الاتصال لأي مشكلة في Azure. إذا احتاج أي شخص صلاحيات إضافية أو واجه خطأ في الاتصال، يرجع إليك مباشرة.

---

### ✅ Task 1.4 — سكريبتات جلب البيانات الأساسية (Ingestion)

**الملفات المتأثرة:**
- `ingestion/producers/producer_binance.py`
- `ingestion/producers/producer_coingecko.py`
- `ingestion/historical/historical_fetcher.py`

**ما تم إنجازه:**
- [x] كتابة `producer_binance.py`: يجلب بيانات الأسعار اللحظية من Binance WebSocket ويرسلها إلى Kafka topic: `crypto.realtime.prices`
- [x] كتابة `producer_coingecko.py`: يجلب بيانات السوق من CoinGecko API ويرسلها إلى Kafka
- [x] كتابة `historical_fetcher.py`: يجلب بيانات OHLCV التاريخية من يناير 2021 لـ 20 عملة ويحفظها كـ JSON خام في `data/historical/`
  - يدعم Retry عند فشل الطلب
  - يستخدم `ThreadPoolExecutor` لتسريع الجلب
  - يتعامل مع Rate Limiting بشكل صحيح

---

### ⚠️ Task 1.5 — مراجعة Pull Requests (مستمر)

**مهمة مستمرة طوال المشروع:**
- [ ] مراجعة كل PR قبل الدمج في `dev` أو `main`
- [ ] التأكد من أن الكود يتبع المعايير المتفق عليها
- [ ] التأكد من عدم رفع ملف `.env` الفعلي أو بيانات اعتماد حقيقية

---

## 🚀 Milestone 2 — التوثيق، التكامل، والرؤية الشاملة

**الهدف:** الانتقال من دور "الباني" إلى دور "المهندس المعماري". التأكد من أن كل مكونات الفريق تتكامل معًا بشكل صحيح.

---

### ✅ Task 2.1 — رسم البنية التحتية (Architecture Diagram)

**الملفات المتأثرة:**
- `docs/architecture.png`

**ما يجب فعله:**
- [x] إنشاء رسم بياني احترافي يوضح تدفق البيانات الكامل:
  ```
  APIs → Kafka → Spark (Bronze) → Spark (Silver) → dbt (Gold) → FastAPI → Frontend
  ```
- [x] يشمل الرسم: أسماء الـ topics في Kafka، مسارات ADLS Gen2، اسم كل Service
- [x] رفعه في `docs/architecture.png`

**أدوات مقترحة:** draw.io, Lucidchart, Mermaid (في README)

---

### ⏳ Task 2.2 — تحديث README.md

**الملفات المتأثرة:**
- `README.md`

**ما تم إنجازه:**
- [x] تحديث جزئي شامل لحالة المشروع وتقدم الفريق
- [ ] إضافة قسم **Architecture** بشكل كامل مع الرسم البياني
- [ ] تحديث قسم **Getting Started** ليعكس بيئة Docker الحالية
- [ ] إضافة قسم **Team Members** يوضح دور كل شخص
- [ ] إضافة قسم **Data Pipeline** يشرح معمارية Medallion

---

### ❌ Task 2.3 — اختبار التكامل الشامل (Integration Testing)

**ما يجب فعله:**
- [ ] تشغيل خط أنابيب البيانات بأكمله والتحقق من:
  - [ ] بيانات Binance تصل إلى Kafka ✓
  - [ ] `bronze_consumer.py` يلتقطها ويكتبها في ADLS
  - [ ] `silver_processor.py` يقرأ من Bronze وينظف البيانات
  - [ ] dbt يقرأ Silver ويبني جداول Gold
  - [ ] FastAPI يجلب البيانات من Gold ويقدمها عبر API
- [ ] تحديد أي "فجوات" في التكامل بين عمل أعضاء الفريق وتوجيههم لحلها

---

### ❌ Task 2.4 — تقرير الحالة النهائي (Status Report)

**ما يجب تسليمه:**
- [ ] ملخص بالتقدم المحرز في كل milestone
- [ ] المشاكل التي تم حلها والطريقة
- [ ] الخطوات التالية للمشروع

---

## 📋 ملخص الحالة

| Task | الوصف | الحالة |
|------|--------|--------|
| 1.1 | هيكل المستودع | ✅ مكتمل |
| 1.2 | ملفات الجذر (.gitignore, .env.example) | ✅ مكتمل |
| 1.3 | البنية التحتية على Azure | ✅ مكتمل |
| 1.4 | سكريبتات Ingestion الأساسية | ✅ مكتمل |
| 1.5 | مراجعة Pull Requests | ⏳ مستمر |
| 2.1 | رسم البنية التحتية | ✅ مكتمل |
| 2.2 | تحديث README.md | ⏳ جزئي |
| 2.3 | اختبار التكامل الشامل | ❌ لم يبدأ |
| 2.4 | تقرير الحالة النهائي | ❌ لم يبدأ |

---

## 📂 ما يجب رفعه على GitHub (Deliverables)

**Milestone 1 (مكتمل):**
- `ingestion/producers/producer_binance.py` ✅
- `ingestion/producers/producer_coingecko.py` ✅
- `ingestion/historical/historical_fetcher.py` ✅
- `.gitignore`, `.env.example`, `requirements.txt` ✅

**Milestone 2 (قيد التنفيذ):**
- `docs/architecture.png` ← **الأولوية الأولى**
- `README.md` (نسخة محدثة شاملة)
- أي "Glue Code" يربط أجزاء المشروع ببعضها
