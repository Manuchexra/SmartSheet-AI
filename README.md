# SmartSheet AI

> **AI-Powered Spreadsheet Generator** — oddiy tildagi so'rovni Excel jadvalga aylantiradigan web-ilova.

![Version](https://img.shields.io/badge/version-1.0.0--MVP-blue)
![Python](https://img.shields.io/badge/python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![Docker](https://img.shields.io/badge/docker-ready-blue)

---

## 📋 Mundarija

- [Loyiha haqida](#-loyiha-haqida)
- [Imkoniyatlar](#-imkoniyatlar)
- [Texnologiyalar](#-texnologiyalar)
- [Tez boshlash](#-tez-boshlash)
- [Konfiguratsiya](#-konfiguratsiya)
- [API](#-api)
- [Testlar](#-testlar)
- [Loyiha strukturasi](#-loyiha-strukturasi)
- [Xavfsizlik](#-xavfsizlik)
- [Litsenziya](#-litsenziya)

---

## 🎯 Loyiha haqida

**SmartSheet AI** — foydalanuvchining oddiy tildagi so'rovini strukturali jadvalga aylantiradigan, natijani brauzerda ko'rsatadigan va Excel (`.xlsx`) formatida yuklab olish imkonini beradigan AI asosidagi web-ilova.

**Misol:**

> **Kirish:** "5 ta xodim uchun jadval yarat, ism, lavozim va maosh ustunlari bilan"
>
> **Natija:** AI 5 qatorli, 3 ustunli tayyor jadval yaratadi va uni `.xlsx` sifatida yuklab olish mumkin.

---

## ✨ Imkoniyatlar

- 🤖 **AI orqali jadval yaratish** — tabiiy tildagi so'rovdan
- 📊 **Brauzerda preview** — jadval darhol ko'rinadi
- ✏️ **Tahrirlash** — kataklar, sarlavhalar, qatorlar
- ↩️ **Undo** — oxirgi 20 amalni bekor qilish (`Ctrl+Z`)
- ➕ **Qator qo'shish/o'chirish**
- 📥 **Excel eksport** — `.xlsx` formatida yuklab olish
- 🎯 **Demo rejim** — AI ishlamasa, namunaviy jadval
- 📱 **Responsive** — desktop, planshet, mobil
- 🔒 **Xavfsiz** — CORS, XSS, formula injection himoyasi

---

## 🛠 Texnologiyalar

### Backend
- **Python 3.11**
- **FastAPI** — REST API
- **Pydantic** — validatsiya
- **openpyxl** — Excel yaratish
- **httpx** — AI API'ga so'rov
- **Uvicorn** — ASGI server

### Frontend
- **HTML5** — struktura
- **CSS3** — dizayn (CSS Variables, Flexbox, Grid)
- **JavaScript** (vanilla) — interaktivlik, Fetch API

### DevOps
- **Docker** + **Docker Compose**
- **pytest** — testlar

### AI provayderlari
- **Groq** (tavsiya) — bepul, tez
- **OpenAI** — sifatli, pullik
- Yoki **demo rejim** (AI'siz)

---

## 🚀 Tez boshlash

### Talablar

- [Docker](https://docs.docker.com/get-docker/) 20.10+
- [Docker Compose](https://docs.docker.com/compose/install/) 2.0+

> **Python o'rnatish shart emas** — hammasi Docker ichida.

### 1. Repozitoriyani klonlash

```bash
git clone <repo-url>
cd SmartSheet-AI