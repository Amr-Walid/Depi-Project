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
| نسبة الإنجاز | ✅ 100% | ⏳ 25% |
| الأولوية | (مكتمل) | تحديث README.md |

### ياسين محمود
| | Milestone 1 | Milestone 2 |
|--|------------|------------|
| نسبة الإنجاز | ⏳ 50% | ❌ 0% |
| الأولوية | historical_loader.py | silver_processor.py |

### مصطفى مطر
| | Milestone 1 | Milestone 2 |
|--|------------|------------|
| نسبة الإنجاز | ✅ 100% | ❌ 0% |
| الأولوية | (مكتمل) | JWT Auth |

### أحمد أيمن
| | Milestone 1 | Milestone 2 |
|--|------------|------------|
| نسبة الإنجاز | ❌ 10% | ❌ 0% |
| الأولوية | producer_news.py | FinBERT Sentiment |

### كريم
| | Milestone 1 | Milestone 2 |
|--|------------|------------|
| نسبة الإنجاز | ✅ 100% | ⏳ 20% |
| الأولوية | (مكتمل) | Staging & Gold Models |

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
2. **كريم** ← كمل ملفات الـ Staging و الـ Gold Models.
3. **أحمد** ← اكتب `producer_news.py` فورًا (producers/producer_news.py فارغ!)
4. **مصطفى** ← ابدأ في بناء نظام الـ JWT Authentication.
5. **عمرو** ← راجع الـ PRs و حدّث الـ README الرئيسي.
