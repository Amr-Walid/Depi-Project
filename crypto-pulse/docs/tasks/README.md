# 📋 CryptoPulse — دليل التاسكات الكامل

> **حالة المراجعة:** أبريل 2026 | راجع بناءً على الملفات الفعلية في المشروع

---

## 🗂️ الملفات

| الملف | المحتوى |
|-------|---------|
| [00_project_structure.md](./00_project_structure.md) | هيكل المشروع الكامل + خريطة الملكية |
| [01_amr_tasks.md](./01_amr_tasks.md) | عمرو وليد — Lead Engineer |
| [02_yassin_tasks.md](./02_yassin_tasks.md) | ياسين محمود — Spark/DataOps |
| [03_mostafa_tasks.md](./03_mostafa_tasks.md) | مصطفى مطر — Backend/Docker |
| [04_ahmed_tasks.md](./04_ahmed_tasks.md) | أحمد أيمن — ML/Analyst |
| [05_karim_tasks.md](./05_karim_tasks.md) | كريم — dbt/Analytics |

---

## 📊 الوضع الحالي (Dashboard)

### عمرو وليد
| | Milestone 1 | Milestone 2 |
|--|------------|------------|
| نسبة الإنجاز | ✅ 95% | ❌ 10% |
| الأولوية | مراجعة PRs | رسم Architecture |

### ياسين محمود
| | Milestone 1 | Milestone 2 |
|--|------------|------------|
| نسبة الإنجاز | ⏳ 50% | ❌ 0% |
| الأولوية | historical_loader.py | silver_processor.py |

### مصطفى مطر
| | Milestone 1 | Milestone 2 |
|--|------------|------------|
| نسبة الإنجاز | ⏳ 60% | ❌ 0% |
| الأولوية | backend/Dockerfile | JWT Auth |

### أحمد أيمن
| | Milestone 1 | Milestone 2 |
|--|------------|------------|
| نسبة الإنجاز | ❌ 10% | ❌ 0% |
| الأولوية | producer_news.py | FinBERT Sentiment |

### كريم
| | Milestone 1 | Milestone 2 |
|--|------------|------------|
| نسبة الإنجاز | ⏳ 20% | ❌ 0% |
| الأولوية | dbt_project.yml | Gold Models |

---

## ⛓️ تسلسل التبعيات

```
عمرو (Azure + Kafka) 
    ↓
  ياسين (Bronze) ──► ياسين (Silver)
                          ↓
                      كريم (Gold dbt)
                          ↓
                     مصطفى (FastAPI)
                          
أحمد (News/Reddit) ──► ياسين (Silver يضم Sentiment)
                          ↓
                      كريم (gold/market_sentiment)
```

---

## 🚨 أولويات هذا الأسبوع

1. **ياسين** ← اكتب `historical_loader.py` + ابدأ `silver_processor.py`
2. **مصطفى** ← أنشئ `backend/Dockerfile` + اكتب `backend/app/main.py`
3. **أحمد** ← اكتب `producer_news.py` فورًا (producers/producer_news.py فارغ!)
4. **كريم** ← اكتب `dbt_project.yml` + أول staging model
5. **عمرو** ← ارسم `docs/architecture.png`
