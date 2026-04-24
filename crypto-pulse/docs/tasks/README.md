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
| نسبة الإنجاز | ✅ 100% | ⏳ 40% |
| الأولوية | (مكتمل) | تحديث README + Integration Testing |

### ياسين محمود
| | Milestone 1 | Milestone 2 |
|--|------------|------------|
| نسبة الإنجاز | ✅ 100% | ✅ 100% |
| الأولوية | (مكتمل) | ✅ مكتمل — Silver Layer + Airflow DAG |

### مصطفى مطر
| | Milestone 1 | Milestone 2 |
|--|------------|------------|
| نسبة الإنجاز | ✅ 100% | ❌ 0% |
| الأولوية | (مكتمل) | JWT Authentication |

### أحمد أيمن
| | Milestone 1 | Milestone 2 |
|--|------------|------------|
| نسبة الإنجاز | ❌ 0% | ❌ 0% |
| الأولوية | producer_news.py (فارغ!) | FinBERT Sentiment |

### كريم
| | Milestone 1 | Milestone 2 |
|--|------------|------------|
| نسبة الإنجاز | ✅ 100% | ✅ 85% |
| الأولوية | (مكتمل) | dbt docs generate + Airflow integration |

---

## ⛓️ تسلسل التبعيات

```
عمرو (Azure + Kafka ✅)
    ↓
  ياسين (Bronze ✅) ──► ياسين (Silver ✅)
                            ↓
                        كريم (Gold dbt ✅ 85%)
                            ↓
                       مصطفى (FastAPI ← الأولوية الآن!)

أحمد (News/Reddit ← لم يبدأ! 🔴) ──► ياسين (Silver يضم Sentiment)
                            ↓
                        كريم (gold/market_sentiment ✅)
```

---

## 🚨 أولويات هذا الأسبوع

1. **أحمد** ← 🔴 اكتب `producer_news.py` فورًا — ملف فارغ تماماً ومعطّل جزء كبير من الـ pipeline!
2. **مصطفى** ← ابدأ في بناء نظام الـ JWT Authentication (الـ Gold Layer جاهزة الآن).
3. **كريم** ← أكمل توثيق الـ dbt (`dbt docs generate`) واربطه مع Airflow.
4. **عمرو** ← راجع الـ PRs وأكمل تحديث الـ README الرئيسي + اختبار التكامل الشامل.
5. **ياسين** ← ✅ أنهى كل مهامه — يمكنه مساعدة أحمد أو مصطفى.
