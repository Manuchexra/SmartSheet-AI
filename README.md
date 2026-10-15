# SmartSheet AI

> Oddiy tildagi so'rovlar va mavjud jadval fayllaridan tahrirlash mumkin bo'lgan, uslublangan Excel jadvallarini yaratishga mo'ljallangan web-ilova.

![Version](https://img.shields.io/badge/version-1.0.0--MVP-blue)
![Python](https://img.shields.io/badge/python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![Docker](https://img.shields.io/badge/docker-ready-blue)

---

## Mundarija

- [Loyiha haqida](#loyiha-haqida)
- [Asosiy imkoniyatlar](#asosiy-imkoniyatlar)
- [Ishlash jarayoni](#ishlash-jarayoni)
- [Texnologiyalar](#texnologiyalar)
- [Tez boshlash: Docker](#tez-boshlash-docker)
- [Mahalliy ishlab chiqish](#mahalliy-ishlab-chiqish)
- [Konfiguratsiya](#konfiguratsiya)
- [Ma'lumotlar bazasi va migratsiyalar](#malumotlar-bazasi-va-migratsiyalar)
- [API ma'lumotnomasi](#api-malumotnomasi)
- [Testlar](#testlar)
- [Loyiha strukturasi](#loyiha-strukturasi)
- [Cheklovlar va xavfsizlik](#cheklovlar-va-xavfsizlik)
- [Muammolarni bartaraf etish](#muammolarni-bartaraf-etish)
- [Litsenziya](#litsenziya)

---

## Loyiha haqida

**SmartSheet AI** foydalanuvchiga jadvalni chat orqali yaratish yoki o'zi ishlatayotgan Excel/CSV faylini yuklab, shu jadvalni keyingi so'rovlar bilan tahrirlash imkonini beradi. Jadval brauzerda ko'rinadi, kataklar bevosita tahrirlanadi va natija `.xlsx` fayli sifatida yuklab olinadi.

Masalan:

> **So'rov:** “5 ta xodim uchun ism, lavozim va maosh ustunlari bilan jadval yarat.”
>
> **Natija:** AI yoki demo rejim jadvalni yaratadi; foydalanuvchi kataklarni to'g'ridan-to'g'ri tahrirlashi, rang va ko'rinishini o'zgartirishi, so'ng Excel fayli sifatida saqlashi mumkin.

Ilova chatlar, xabarlar va jadvallarni SQLite bazasida saqlaydi. Har bir chat bitta jadval va shu jadval bilan bog'liq suhbat tarixini saqlaydi.

## Asosiy imkoniyatlar

- **Tabiiy tildan jadval yaratish:** ustunlar, qatorlar va jadval nomini so'rovdan aniqlash.
- **Mavjud jadval bilan suhbat:** chatga yuklangan yoki yaratilgan jadvalni keyingi AI so'rovlari bilan tahrirlash.
- **Fayl importi:** `.xlsx` va `.csv` fayl yuklash. Excel файlдаги faol (birinchi tanlangan) ishchi varaq olinadi; imkon qadar mavjud katak uslublari ham saqlanadi.
- **Brauzerda ko'rish va tahrirlash:** katak qiymatlari va jadval tuzilmasini o'zgartirish, qator qo'shish yoki o'chirish.
- **Uslublar:** sarlavha, tana, qator, ustun va alohida kataklar uchun fon/matn rangi, shrift, qalin/kursiv yozuv, tekislash va chegaralar. Standart jadval chegaralari qora va ingichka bo'ladi.
- **Excel eksporti:** `.xlsx` faylda qiymatlar, qo'llab-quvvatlanadigan formatlash, formulalar, ustun kengligi, filtr va muzlatilgan sarlavha saqlanadi.
- **Formulalar:** formulalar katakda hisoblangan ko'rinish bilan chiqadi, formula matni esa saqlanadi. Brauzerda `CONCAT`, `SUM`, `AVERAGE`, `COUNT`, `MAX`, `MIN`, `IF`, `ROUND` va oddiy arifmetik ifodalar hisoblanadi. Excel eksportida xavfsiz formula Excel formulasi sifatida yoziladi.
- **Undo / Redo:** brauzerdagi oxirgi jadval tahrirlarini `Ctrl+Z` va `Ctrl+Y` orqali qaytarish yoki qayta bajarish.
- **Chatlar tarixini boshqarish:** chat yaratish, nomini o'zgartirish va o'chirish.
- **Brauzer profili bo'yicha chatlar:** chatlar alohida brauzer profili identifikatori bilan ajratiladi.
- **Demo rejim:** AI provayderi ulanmaganida namunaviy jadval andozalari yoki oddiy matn bilan ishlash.
- **Moslashuvchan interfeys:** desktop, planshet va mobil ekranlarga mos UI.

Jadval uchun amaldagi standart cheklovlar: **200 ta ma'lumot qatori** va **20 ta ustun**. Bundan tashqari, bitta brauzer profilida **100 tagacha chat** ochish mumkin; chatdagi xabarlar soni konfiguratsiyaga bog'liq.

## Ishlash jarayoni

1. Brauzer `X-Client-ID` header'ida doimiy UUID yuboradi. ID `localStorage` ichida saqlanadi.
2. FastAPI so'rovlarni tekshiradi va chat/jadval/xabarlarni SQLAlchemy orqali SQLite bazasida унумли saqlaydi.
3. Jadval so'rovi sozlangan AI provayderiga yuboriladi. AI javobi strukturaga mosligi va qiymatlari bo'yicha validatsiya qilinadi.
4. Jadval va unga tegishli uslublar chatga saqlanib, brauzer interfeysiga qaytariladi.
5. Excel eksport endpointi validatsiyalangan jadval ma'lumotlaridan `.xlsx` yaratadi.

AI bilan chat ichidagi jadvalni tahrirlashda AI mavjud bo'lmasa yoki so'rov muvaffaqiyatsiz bo'lsa, chat endpointi aniq xato javobini beradi. Mustaqil `/tables/generate` endpointi esa demo natijaga o'tishi mumkin.

## Texnologiyalar

### Backend

- **Python 3.11**
- **FastAPI** va **Uvicorn** — REST API va web-server
- **Pydantic** — so'rov/javob validatsiyasi
- **SQLAlchemy** — ORM va ma'lumotlar bazasi
- **Alembic** — sxema migratsiyalari
- **SQLite** — asosiy ma'lumotlar bazasi
- **openpyxl** — Excel importi va eksporti
- **httpx** — AI API bilan HTTP aloqasi

### Frontend

- HTML5, CSS3 va vanilla JavaScript
- Fetch API orqali backend bilan aloqa
- `frontend/js/formula-eval.js` — brauzerda qo'llab-quvvatlanadigan formulalarni hisoblash

### Ishlab chiqish va testlar

- Docker va Docker Compose
- pytest

## Tez boshlash: Docker

### Talablar

- Docker Engine yoki Docker Desktop
- Docker Compose v2 (`docker compose`)

Python'ni kompyuterga alohida o'rnatish shart emas.

### 1. Repozitoriyani klonlash

```bash
git clone https://github.com/Manuchexra/SmartSheet-AI.git
cd SmartSheet-AI
```

### 2. Muhit faylini yaratish

`.env.example` faylidan `.env` nusxasini oling:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Demo rejimida AI kalitini kiritish shart emas. Haqiqiy AI ishlashi uchun `.env` dagi `AI_PROVIDER`, `AI_API_KEY`, `AI_MODEL` va `AI_API_URL` qiymatlarini provayder sozlamalariga moslang. `.env` faylini Git'ga yubormang.

### 3. Ilovani ishga tushirish

```bash
docker compose up --build -d
```

Brauzerda [http://localhost:8000](http://localhost:8000) manzilini oching.

Foydali Docker buyruqlari:

```bash
docker compose ps
docker compose logs -f backend
docker compose down
```

Ma'lumotlar `./data` papkasidagi SQLite faylida saqlanadi; konteynerni qayta yaratish chatlarni o'chirmaydi. `docker compose down -v` kabi volume o'chiradigan buyruqlarni ishlatishdan oldin ma'lumotlaringizni zaxiralang.

## Mahalliy ishlab chiqish

### Talablar

- Python 3.11
- pip
- (Ixtiyoriy) AI provayder API kaliti

Virtual muhit yarating va kerakli paketlarni o'rnating:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

macOS/Linux:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

So'ng backend'ni ishga tushiring:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Ilova `http://localhost:8000` da ochiladi. `--reload` ishlab chiqish uchun mo'ljallangan; production muhitida foydalanmang.

### API hujjatlari

Server ishlayotganida FastAPI hujjatlari:

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- OpenAPI JSON: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

## Konfiguratsiya

Konfiguratsiya `.env` faylidan olinadi; o'zgaruvchi nomlari harf kattaligini hisobga olmaydi. Asosiy parametrlar:

| O'zgaruvchi | Vazifasi | Standart |
|---|---|---|
| `APP_NAME` | Ilova nomi | `SmartSheet AI` |
| `APP_ENV` | Muhit; `development` yoki production sozlamalari | `development` |
| `APP_HOST` | Server host qiymati | `0.0.0.0` |
| `APP_PORT` | Server port qiymati | `8000` |
| `AI_PROVIDER` | AI rejimi/provayderi (`groq`, `openai`, `gemini` yoki `demo`) | `demo` |
| `AI_API_KEY` | Provayder API kaliti | bo'sh |
| `AI_MODEL` | Provayder model identifikatori | bo'sh |
| `AI_API_URL` | Provayderning chat-completions API manzili | bo'sh |
| `DATABASE_URL` | SQLAlchemy ulanish URL'i | `sqlite:///./data/smartsheet.db` |
| `MAX_ROWS` | Jadvaldagi eng ko'p ma'lumot qatori (1–200) | `200` |
| `MAX_COLUMNS` | Jadvaldagi eng ko'p ustun | `20` |
| `MAX_PROMPT_LENGTH` | AI so'rov matni uchun uzunlik chegarasi | `2000` |
| `MAX_CHATS` | Bitta brauzer profilidagi chatlar chegarasi | `100` |
| `MAX_MESSAGES_PER_CHAT` | Har bir chatdagi xabarlar chegarasi | `50` |

Undo/redo tarixi frontend'da 20 ta jadval amaligacha saqlanadi.

`.env.example` dagi qiymatlar loyiha konfiguratsiyasini ko'rsatadi; ishlatiladigan haqiqiy qiymatlar muhit o'zgaruvchilari va `.env` faylingizga bog'liq. Masalan, `.env.example` da `MAX_MESSAGES_PER_CHAT=500` bo'lishi mumkin, konfiguratsiya klassidagi standart qiymat esa `50`.

### AI provayderi

AI so'rovi `AI_API_URL` manziliga `AI_MODEL` model nomi bilan yuboriladi. Kalit `AI_API_KEY` orqali uzatiladi. Sozlamalar provayder tomonidan taqdim etilgan endpoint, model va kalitga mos bo'lishi kerak. `AI_PROVIDER=demo` holatida AI API'ga so'rov yuborilmaydi.

```dotenv
AI_PROVIDER=demo
AI_API_KEY=
AI_MODEL=
AI_API_URL=
```

Kalitlarni frontend JavaScript'iga yoki Git omboriga qo'ymang.

## Ma'lumotlar bazasi va migratsiyalar

Model tuzilmalari:

- **Chat:** sarlavha, yaratilgan/yangilangan vaqt va brauzer identifikatori.
- **Message:** chatga tegishli rol (`user` yoki `ai`), matn va vaqt.
- **Table:** chatga tegishli sarlavha, ustunlar, qatorlar, uslublar, manba va versiya.

Alembic migratsiyalari:

1. `001_initial` — chatlar, xabarlar va jadvallar.
2. `002_add_styles` — jadval uslublarini saqlash.
3. `003_add_browser_scope` — chatlarni brauzer identifikatori bilan ajratish.

Backend startup paytida migratsiyalarni avtomatik `head` gacha yangilaydi. Migratsiyani qo'lda ishlatish:

```bash
alembic upgrade head
alembic current
```

Migration revision'i bo'lmagan eski baza to'liq boshlang'ich sxemaga mos bo'lsa, startup uni xavfsiz aniqlab yangilaydi. Qisman yoki kutilmagan sxema aniqlansa, migratsiya avtomatik sxema yaratishga urinmaydi va backend aniq xato beradi. Bunday holatda avval bazaning zaxira nusxasini olib, sxemani tekshiring; ma'lumotlar bazasi faylini tekshirmasdan o'chirmang.

## API ma'lumotnomasi

Barcha API endpointlari `/api/v1` prefiksidan boshlanadi. Chatga tegishli endpointlar brauzer identifikatori uchun UUID formatidagi `X-Client-ID` header'ini talab qiladi. Frontend bu header'ni avtomatik qo'shadi.

| Method | Endpoint | Tavsif |
|---|---|---|
| `GET` | `/health` | Ilova holatini tekshirish |
| `POST` | `/chats` | Yangi chat yaratish |
| `GET` | `/chats` | Joriy brauzer chatlarini ro'yxatlash |
| `GET` | `/chats/{chat_id}` | Chat ma'lumotini olish |
| `PATCH` | `/chats/{chat_id}` | Chat nomini o'zgartirish |
| `DELETE` | `/chats/{chat_id}` | Chat va unga tegishli ma'lumotlarni o'chirish |
| `POST` | `/chats/{chat_id}/generate` | Chatda AI orqali jadval yaratish yoki tahrirlash |
| `GET` | `/chats/{chat_id}/messages` | Chat xabarlarini olish |
| `POST` | `/chats/{chat_id}/messages` | Chatga xabar qo'shish |
| `DELETE` | `/chats/{chat_id}/messages/{message_id}` | Chatdagi xabarni o'chirish |
| `GET` | `/chats/{chat_id}/table` | Chat jadvalini olish |
| `POST` | `/chats/{chat_id}/table` | Yangi jadval yaratish |
| `PUT` | `/chats/{chat_id}/table` | Jadval yaratish yoki to'liq yangilash |
| `PATCH` | `/chats/{chat_id}/table` | Jadvalning tanlangan qismlarini yangilash |
| `DELETE` | `/chats/{chat_id}/table` | Chat jadvalini o'chirish |
| `POST` | `/chats/{chat_id}/table/upload` | `.xlsx` yoki `.csv` faylni import qilish |
| `POST` | `/tables/generate` | Chatga saqlamasdan AI jadval yaratish |
| `POST` | `/excel/export` | Jadval ma'lumotlaridan `.xlsx` yaratish |

Masalan, chatda jadval yaratish/tahrirlash:

```bash
curl -X POST "http://localhost:8000/api/v1/chats/1/generate" \
  -H "Content-Type: application/json" \
  -H "X-Client-ID: 11111111-1111-4111-8111-111111111111" \
  -d "{\"prompt\":\"Xodimlar uchun ism, lavozim va maosh jadvali yarat\"}"
```

Jadval JSON'i `title`, `columns`, `rows`, `styles`, `source` kabi maydonlardan iborat. `source` qiymati `ai`, `demo`, `manual` yoki `upload` bo'ladi. To'liq sxema va endpoint javoblarini `/docs` sahifasidan ko'ring.

## Testlar

Testlarni ishga tushirish:

```bash
pytest -q
```

Testlar bazasini ishlab turgan ma'lumotlar bazasidan ajratish uchun test jarayoniga alohida `DATABASE_URL` bering. PowerShell misoli:

```powershell
$env:DATABASE_URL = "sqlite:///./data/smartsheet-test.db"
pytest -q
```

Test tugagach muhit o'zgaruvchisini joriy PowerShell oynasidan olib tashlash:

```powershell
Remove-Item Env:DATABASE_URL
```

Asosiy test qamrovi: API va AI javoblari, chat/xabar/jadval CRUD, `.xlsx` eksporti, jadval importi, migratsiyalar hamda brauzerlararo chat ajratilishi.

## Loyiha strukturasi

```text
SmartSheet-AI/
├── alembic/                     # DB migratsiyalari
│   └── versions/
├── backend/
│   ├── api/
│   │   └── endpoints/           # FastAPI endpointlari
│   ├── db/                      # Engine, sessiya va startup migration
│   ├── models/                  # Chat, Message va Table ORM modellari
│   ├── modules/
│   │   ├── ai/                  # Promptlar, AI provayderi va demo rejim
│   │   ├── chats/               # Chat sxemalari, scope va CRUD
│   │   ├── excel/               # Excel eksporti
│   │   ├── formulas/            # Formula validatsiyasi/xavfsizligi
│   │   ├── messages/            # Xabarlar
│   │   ├── styles/              # Uslub sxemalari va default qiymatlar
│   │   ├── table_generator/     # Jadval yaratish sxemalari
│   │   └── tables/              # Jadval CRUD va fayl importi
│   ├── config.py                # Ilova sozlamalari
│   └── main.py                  # FastAPI ilovasi, middleware va startup
├── data/                        # SQLite ma'lumotlar bazasi
├── frontend/
│   ├── assets/                  # Statik assetlar
│   ├── css/                     # Interfeys stili
│   ├── js/                      # UI, API va formula hisoblash
│   └── index.html               # Bosh sahifa
├── tests/                       # pytest testlari
├── .env.example                 # Muhit sozlamalari namunasi
├── Dockerfile                   # Productionga yaqin Docker image
├── docker-compose.yml           # Docker Compose konfiguratsiyasi
├── requirements.txt             # Python bog'liqliklari
└── README.md
```

## Cheklovlar va xavfsizlik

- **Brauzer scope autentifikatsiya emas.** `X-Client-ID` localStorage'dagi ID bo'lib, chatlarni kundalik foydalanishda brauzer profillari bo'yicha ajratadi. U maxfiylik yoki foydalanuvchini tasdiqlashning mustaqil xavfsizlik chegarasi hisoblanmaydi; kuchli autentifikatsiya kerak bo'lsa login/akkaunt tizimi qo'shilishi lozim.
- **Brauzer ma'lumotlarini tozalash:** localStorage yoki sayt ma'lumotlari o'chirilsa, yangi ID yaratiladi va eski chatlar bu brauzerda ko'rinmay qoladi. Boshqa profil yoki qurilmadagi chatlar avtomatik sinxronlanmaydi.
- **Birinchi ishga tushirish:** egasiz legacy chatlar yangi versiyadan keyin chatlar ro'yxatini birinchi so'ragan brauzerga biriktiriladi.
- **Yuklash:** faqat `.xlsx` va UTF-8 `.csv`; maksimal fayl hajmi 10 MB. Jadvalda sarlavha va kamida bitta ma'lumot qatori, 20 tadan ko'p bo'lmagan ustun va 200 tadan ko'p bo'lmagan ma'lumot qatori bo'lishi kerak.
- **Formula xavfsizligi:** faqat ruxsat etilgan formulalar Excel formulasi sifatida eksport qilinadi; xavfli formula funksiyalari bloklanadi. Brauzerdagi formula hisoblagich barcha Excel funksiyalarini qo'llab-quvvatlamaydi.
- **Production:** `APP_ENV` production bo'lganda CORS origin'larini server konfiguratsiyasida aniq va ishonchli domenlar bilan sozlang. HTTPS, AI kalitlarini maxfiy saqlash, ma'lumotlar bazasini zaxiralash va kirish huquqlarini cheklashni ham ta'minlang.
- **Maxfiylik:** AI provayderi sozlangan bo'lsa, so'rov matni va unga kiritilgan jadval ma'lumotlari provayderga yuborilishi mumkin. Maxfiy ma'lumotlar bilan ishlashdan oldin provayder siyosatini tekshiring.

## Muammolarni bartaraf etish

### `table chats already exists` migratsiya xatosi

Ko'pincha Alembic revision yozuvi yo'q eski, ammo jadvallari avvaldan yaratilgan SQLite bazasida uchraydi. Backend startup migratsiyasi to'liq boshlang'ich sxemani tekshiradi va bunday bazani xavfsiz qabul qilishga mo'ljallangan. Avval:

1. Backend logida qaysi sxema/revision aniqlanganini ko'ring.
2. `.env` dagi `DATABASE_URL` aynan kutilgan bazaga ko'rsatayotganini tekshiring.
3. Bazani o'chirish yoki qo'lda `stamp` qilishdan oldin uning zaxira nusxasini oling.

### `no such column: tables.styles`

Bu bazada jadvallar mavjud, lekin uslublar migratsiyasi hali bajarilmaganini anglatishi mumkin. Backend startup migratsiyasi yoki qo'lda `alembic upgrade head` bajarilganini, ilova va Alembic bir xil `DATABASE_URL` ishlatayotganini tekshiring.

### AI so'rovi ishlamayapti

- `AI_PROVIDER`, `AI_API_KEY`, `AI_MODEL` va `AI_API_URL` qiymatlari bo'sh emasligi hamda provayderga mosligini tekshiring.
- Backend loglarini ko'ring: `docker compose logs -f backend`.
- AI sozlanmagan bo'lsa, `.env` da `AI_PROVIDER=demo` ishlatib interfeysning qolgan qismini sinab ko'ring.

### Chat brauzerda ko'rinmayapti

Chat yaratilgan brauzer profili va localStorage saqlanganini tekshiring. Boshqa brauzer profili yoki qurilmada chatlar ataylab alohida ko'rsatiladi; bu akkauntlararo sinxronlash xizmati emas.

## Litsenziya

Repozitoriyada litsenziya fayli bo'lmasa, loyiha uchun alohida litsenziya shartlari e'lon qilinmagan deb hisoblang.
