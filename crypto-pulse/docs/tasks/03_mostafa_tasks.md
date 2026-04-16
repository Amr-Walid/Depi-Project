# 🐳 مصطفى مطر — Backend Engineer & Docker Environment Owner

> **الدور:** مهندس الـ Backend + مالك بيئة التشغيل بالكامل  
> **المسؤولية الجوهرية:** بيئة Docker التي تجمع كل الخدمات، وبناء الـ API الذي يخدم المستخدمين

---

## 🏁 Milestone 1 — بناء وتفعيل بيئة التطوير المتكاملة

**الهدف:** تسليم بيئة تطوير محلية تعمل بكامل طاقتها — أي شخص في الفريق يعمل `make up` وكل شيء يشتغل.

---

### ✅ Task 1.1 — بناء بيئة Docker الأساسية

**الملف:** `docker-compose.yml`

**ما تم إنجازه:**
- [x] تعريف خدمة `zookeeper` (إدارة Kafka)
- [x] تعريف خدمة `kafka` مع إعداد Listeners (INTERNAL + EXTERNAL)
- [x] إنشاء خدمة `kafka-init-topics` لإنشاء topic `crypto.realtime.prices` تلقائيًا
- [x] تعريف خدمة `kafka-ui` على port `8080`
- [x] تعريف خدمة `postgres:15` لـ Airflow و Backend
- [x] تعريف خدمة `airflow-webserver` على port `8081` مع volume لـ `./dags`
- [x] تعريف خدمة `airflow-scheduler`
- [x] تعريف خدمة `spark-master` و `spark-worker`
- [x] إعداد network مشتركة `crypto-net` لكل الخدمات
- [x] إعداد volumes: `postgres_data`, `airflow_logs`

**⚠️ ما تم تحديثه في docker-compose.yml:**
- [x] إضافة خدمة `backend` لتشغيل FastAPI على port `8000`
- [x] إضافة topics جديدة في `kafka-init-topics`: `crypto.market.data`, `crypto.news`, `crypto.social`
- [x] تمرير متغيرات البيئة من `.env` إلى خدمات Spark و Backend
- [x] ربط volume لمجلد `processing/spark_jobs/` إلى خدمة Spark

---

### ✅ Task 1.2 — Makefile الأساسي

**الملف:** `Makefile`

**ما تم إنجازه:**
- [x] أمر `up`: `docker compose up -d`
- [x] أمر `down`: `docker compose down`
- [x] أمر `logs`: `docker compose logs -f`
- [x] أمر `restart`: `docker compose down && docker compose up -d`

**ما تم إضافته:**
- [x] `make rebuild-backend` — لإعادة بناء image الـ backend فقط:
- [x] `make test` — لتشغيل الاختبارات:
- [x] `make shell-backend` — للدخول إلى container الـ backend:
- [x] `make spark-submit` — لتشغيل Bronze Consumer:

---

### ✅ Task 1.3 — Dockerfile لـ Spark

**الملف:** `spark-apps/Dockerfile.spark`

**ما تم إنجازه:**
- [x] صورة Spark مخصصة جاهزة للتشغيل

---

### ✅ Task 1.4 — Dockerfile لـ Backend (FastAPI)

**الملف:** `backend/Dockerfile`

**ما تم إنجازه:**
- [x] إنشاء `backend/Dockerfile`
- [x] إنشاء `backend/requirements.txt`
- [x] إنشاء `.dockerignore` في مجلد backend

---

### ✅ Task 1.5 — بناء الهيكل الأولي للـ Backend

**الملفات:**
- `backend/app/main.py`
- `backend/app/routers/`
- `backend/app/models/`
- `backend/app/services/`

**ما تم إنجازه:**
- [x] ملء `backend/app/main.py` ووضع endpoint للصحة Health check
- [x] إنشاء `backend/app/routers/__init__.py`
- [x] إنشاء `backend/app/services/__init__.py`
- [x] إنشاء `backend/app/models/__init__.py`

---

## 🚀 Milestone 2 — بناء وتأمين الواجهة الخلفية (API)

**الهدف:** بناء API وظيفي ومؤمن يستطيع Frontend استخدامه لتسجيل الدخول والوصول للبيانات.

---

### ❌ Task 2.1 — نظام المصادقة (Authentication)

**الملفات:**
- `backend/app/routers/auth.py`
- `backend/app/services/auth_service.py`

**ما يجب فعله:**
- [ ] إنشاء endpoints:
  - `POST /api/v1/auth/signup` — تسجيل مستخدم جديد
  - `POST /api/v1/auth/login` — تسجيل دخول والحصول على JWT Token
- [ ] تطبيق JWT (JSON Web Tokens):
  ```python
  from jose import jwt
  SECRET_KEY = os.getenv("JWT_SECRET_KEY")
  ALGORITHM = "HS256"
  ```
- [ ] تشفير كلمات المرور:
  ```python
  from passlib.context import CryptContext
  pwd_context = CryptContext(schemes=["bcrypt"])
  ```
- [ ] استخدام `schema.sql` الذي أنشأه كريم للتفاعل مع PostgreSQL عبر SQLAlchemy
- [ ] إنشاء `Dependency` للتحقق من التوكن في الـ endpoints المحمية:
  ```python
  async def get_current_user(token: str = Depends(oauth2_scheme)):
      ...
  ```

---

### ❌ Task 2.2 — Endpoints للبيانات التحليلية

**الملفات:**
- `backend/app/routers/coins.py`
- `backend/app/services/data_service.py`

**ما يجب فعله:**
- [ ] إنشاء endpoints محمية بـ JWT:
  - `GET /api/v1/coins` — قائمة بكل العملات المتاحة
  - `GET /api/v1/coins/{coin_id}/summary` — ملخص تحليلي لعملة معينة
  - `GET /api/v1/coins/{coin_id}/prices` — بيانات الأسعار التاريخية
  - `GET /api/v1/market/overview` — نظرة عامة على السوق
- [ ] كتابة `data_service.py` الذي:
  - [ ] يتصل بـ Azure ADLS Gen2 باستخدام Service Principal
  - [ ] يقرأ البيانات من جداول **Gold Layer** التي أنشأها كريم
  - [ ] يعيدها كـ JSON منسق

> **ملاحظة:** هذا يعتمد على إنجاز كريم لجداول Gold Layer أولاً

---

### ❌ Task 2.3 — اختبارات الـ API (Testing)

**الملفات:**
- `backend/tests/test_auth.py`
- `backend/tests/test_coins.py`

**ما يجب فعله:**
- [ ] إعداد `conftest.py` مع TestClient:
  ```python
  from fastapi.testclient import TestClient
  from app.main import app
  client = TestClient(app)
  ```
- [ ] كتابة اختبارات لـ Authentication:
  - [ ] اختبار signup بمعطيات صحيحة → يجب أن يعود 201
  - [ ] اختبار signup بإيميل مكرر → يجب أن يعود 400
  - [ ] اختبار login بكلمة مرور خاطئة → يجب أن يعود 401
  - [ ] اختبار الوصول لـ endpoint محمي بدون توكن → يجب أن يعود 403
- [ ] كتابة اختبارات لـ Data Endpoints:
  - [ ] اختبار `/api/v1/coins` مع توكن صحيح → يجب أن يعود 200

---

## 📋 ملخص الحالة

| Task | الوصف | الحالة |
|------|--------|--------|
| 1.1 | docker-compose.yml الأساسي | ✅ مكتمل |
| 1.2 | Makefile الأساسي | ✅ مكتمل |
| 1.3 | Dockerfile.spark | ✅ مكتمل |
| 1.4 | backend/Dockerfile | ✅ مكتمل |
| 1.5 | هيكل backend/app/ الأولي | ✅ مكتمل |
| 2.1 | نظام Authentication (JWT) | ❌ لم يبدأ |
| 2.2 | Data Endpoints | ❌ لم يبدأ |
| 2.3 | اختبارات pytest | ❌ لم يبدأ |

---

## 📂 ما يجب رفعه على GitHub (Deliverables)

**Milestone 1:**
- `docker-compose.yml` ✅ (مرفوع ومحدث)
- `Makefile` ✅ (مرفوع ومحدث)
- `backend/Dockerfile` ✅ (مرفوع)
- `backend/app/main.py` ✅ (مرفوع)
- `backend/app/__init__.py`, `routers/__init__.py`, `services/__init__.py` ✅ (مرفوع)

**Milestone 2:**
- `backend/app/routers/auth.py`
- `backend/app/routers/coins.py`
- `backend/app/services/auth_service.py`
- `backend/app/services/data_service.py`
- `backend/tests/test_auth.py`
- `backend/tests/test_coins.py`

---

## 🔧 التبعيات والاعتمادات

| يعتمد على | من | لماذا |
|-----------|-----|--------|
| `schema.sql` (User model) | كريم | للتعامل مع PostgreSQL في Auth |
| Gold Layer جاهز | كريم + ياسين | لبناء Data Endpoints |
| Azure credentials | عمرو | للاتصال بـ ADLS من الـ Backend |
| Kafka topics صح | مصطفى نفسه | `kafka-init-topics` في docker-compose |

---

## 🌐 الـ Ports والـ Endpoints المتوقعة

| Service | Port | URL |
|---------|------|-----|
| FastAPI App | 8000 | `http://localhost:8000` |
| Swagger UI | 8000 | `http://localhost:8000/docs` |
| Health Check | 8000 | `http://localhost:8000/health` |
| Kafka UI | 8080 | `http://localhost:8080` |
| Airflow | 8081 | `http://localhost:8081` |
| Spark Master | 8082 | `http://localhost:8082` |
