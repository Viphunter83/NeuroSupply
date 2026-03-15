# NeuroSupply (v2.4.0)

Интеллектуальная система управления запасами для современных ресторанов.

## 🌟 Основная идея
NeuroSupply — это AI-платформа, которая переводит управление закупками с "интуиции" на точные данные. Система прогнозирует продажи, анализирует техкарты и автоматически формирует заказы поставщикам, минимизируя списания и ошибки персонала.

## 🚀 Ключевые возможности (v2.4.0)
- **AI Forecasting (v2.1)**: Профессиональная ML-модель для точного прогноза спроса.
- **Pure Web Architecture**: Полный отказ от Google Sheets для управления настройками. Все параметры — в Dashboard.
- **Direct iiko Sync**: Прямая интеграция с iiko Cloud/Resto для получения остатков и рецептур.
- **PWA Dashboard**: Современная панель управления (Next.js) с поддержкой мобильных устройств.
- **Mini App**: Легкий интерфейс для поваров (Vue 3) для инвентаризации "на ходу".

## 🛠 Технологии
- **Backend**: FastAPI, PostgreSQL, SQLAlchemy, Pandas, Scikit-learn.
- **Frontend**: Next.js 15 (Dashboard), Vue 3 (Mini App).
- **Integrations**: iiko API, Procob (Export Status).
- **Infrastructure**: Cloudflare Tunnel, Supabase.

## 📖 Документация
- [Процессы и логика](BUSINESS_LOGIC_GUIDE.md)
- [Руководство для клиента](README_CLIENT.md)
- [Гайд по презентации](PRESENTATION_GUIDE.md)
- [Состояние проекта](PROJECT_STATE.md)
