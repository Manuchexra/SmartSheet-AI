# SmartSheet AI — Mahsulot taklifi

> Bu hujjat SmartSheet AI'ning amaldagi MVP'si va uni tekshirish bo'yicha taklifni bayon qiladi. Tariflar, mijozlar soni va vaqt tejash ko'rsatkichlari hozircha bozor ma'lumotlari bilan tasdiqlanmagan.

## 1. Qisqacha taklif

**SmartSheet AI** jadval yaratish yoki mavjud jadvalni tahrirlash ishini chat, brauzerda ko'rish va Excel eksporti bilan birlashtiradigan web-ilova.

Foydalanuvchi jadvalga kerakli ustun va ma'lumotlarni tabiiy tilda tasvirlaydi yoki `.xlsx`/`.csv` faylini yuklaydi. Natijani ko'rib, kataklarini tahrirlaydi, chat orqali o'zgartirish so'raydi va yakuniy jadvalni `.xlsx` sifatida yuklab oladi.

**Qiymat taklifi:** jadvalni noldan yaratish yoki mavjud fayl ustida ishlashni boshlash, natijani ko'rib tekshirish va Excel formatida olish.

## 2. Kim uchun?

Quyidagi guruhlar dastlabki foydalanuvchi segmentlari sifatida tekshirilishi mumkin:

- kichik biznes egasi yoki ofis menejeri;
- HR va ma'muriy xodim;
- savdo mutaxassisi;
- loyiha menejeri;
- o'qituvchi yoki ta'lim markazi xodimi;
- Excel/CSV bilan muntazam ishlaydigan yakka mutaxassis.

Bular tasdiqlangan mijoz segmentlari emas. Birinchi segmentni tanlashdan oldin vazifalar, foydalanish chastotasi va to'lovga tayyorlik intervyu hamda pilot bilan tekshiriladi.

### Tipik vazifa misollari

- “Xodimlar uchun ism, lavozim, bo'lim va maosh ustunlari bilan ro'yxat yarat.”
- “Ushbu mijozlar jadvaliga aloqa holati ustunini qo'sh.”
- “Maosh ustunini yashil rangda ko'rsat.”
- Mavjud Excel/CSV faylini yuklab, sarlavha va qatorlarini brauzerda ko'rish.
- Tahrirlangan jadvalni Excel formatida hamkasbga yuborish.

Misollar funksiyani tushuntiradi; AI javobining aniqligi ma'lumot va so'rov sifatiga bog'liq, shuning uchun natijani tekshirish kerak.

## 3. Foydalanuvchi uchun qiymat

| Ehtiyoj | MVP'dagi imkoniyat | Pilotda tekshirish |
|---|---|---|
| Jadvalni noldan boshlash | Chat orqali AI/demo jadval yaratish | Birinchi foydali jadvalgacha ketgan vaqt va qayta so'rovlar |
| Mavjud fayl ustida ishlash | `.xlsx` va `.csv` importi | Importdan keyin qancha tuzatish kerak bo'ldi |
| Natijani moslashtirish | Kataklarni tahrirlash, qator boshqaruvi, undo/redo | Foydalanuvchi vazifani shu ilovada tugata oldimi |
| Ko'rinishni boshqarish | Jadval uslublari | Preview va eksport natijasi qanchalik mos |
| Natijani ulashish | `.xlsx` eksporti | Foydalanuvchi faylni odatiy ishida ishlata oldimi |

## 4. Amaldagi MVP ko'lami

### Mavjud imkoniyatlar

- chat yaratish, nomini o'zgartirish va o'chirish;
- tabiiy tildagi so'rov orqali jadval yaratish;
- mavjud chat jadvaliga AI tahrir so'rovlarini yuborish;
- `.xlsx` va UTF-8 `.csv` fayllarini import qilish;
- chat va jadval ma'lumotlarini SQLite'da saqlash;
- brauzerda kataklarni tahrirlash, qator qo'shish/o'chirish va undo/redo;
- jadval uslublarini saqlash va qo'llab-quvvatlanadigan formatni eksport qilish;
- ayrim formulalarni jadvalda ko'rsatish va xavfsiz formulalarni Excel'ga yozish;
- AI sozlanmagan holatda demo rejimdan foydalanish.

Amaldagi limitlar: 200 tagacha ma'lumot qatori, 20 tagacha ustun va import uchun 10 MB. Excel importida faol ishchi varaq olinadi. Barcha Excel formulalari, makroslari yoki workbook elementlari qo'llanadi deb va'da qilinmaydi.

### MVP'ga kirmaydigan imkoniyatlar

- login, akkaunt va parolni tiklash;
- qurilmalararo chat sinxronlash yoki akkaunt orqali chatni tiklash;
- to'lov, billing, tarif va avtomatik obuna;
- jamoaviy workspace, bir vaqtda tahrirlash, rollar yoki audit tarixi;
- Google Sheets, Microsoft 365 yoki CRM integratsiyalari;
- barcha Excel formulalari va makroslari;
- vaqt tejash bo'yicha qat'iy kafolat.

Chatlar brauzer profilidagi `localStorage` identifikatori bilan ajratiladi. Bu akkaunt autentifikatsiyasi yoki kuchli xavfsizlik chegarasi emas.

## 5. Foydalanuvchi oqimi

```text
Saytni ochish
    ↓
Yangi chat yaratish yoki mavjud chatni tanlash
    ↓
Jadval so'rovini yozish yoki Excel/CSV faylni yuklash
    ↓
Jadvalni ko'rish va natijani tekshirish
    ↓
Kataklarni qo'lda tahrirlash yoki chat orqali o'zgartirish
    ↓
Yakuniy jadvalni .xlsx sifatida yuklab olish
```

Hisob-kitob, maosh, mijoz yoki hisobot ma'lumotlarida AI yaratgan qiymatlarni foydalanuvchi tekshirishi lozim.

## 6. Texnik yechim

| Qism | Texnologiya/vazifa |
|---|---|
| Web interfeysi | HTML, CSS, vanilla JavaScript |
| API | Python va FastAPI |
| Validatsiya | Pydantic sxemalari |
| Saqlash | SQLAlchemy va SQLite |
| Sxema yangilash | Alembic migratsiyalari |
| Excel fayllari | openpyxl orqali import/eksport |
| AI ulanishi | Sozlangan HTTP API provayderi |
| Ishga tushirish | Uvicorn yoki Docker Compose |
| Testlar | pytest |

Backend chat, xabar, jadval va jadval uslublarini saqlaydi. Frontend `X-Client-ID` header'ida brauzer identifikatorini yuboradi. AI javobi sxema bo'yicha tekshiriladi. Xavfsiz deb topilgan formulalar Excel eksportida formula sifatida yoziladi.

## 7. Taklif etilayotgan pilot

### Maqsad

MVP foydalanuvchining haqiqiy jadval vazifasini bajara oladimi, natijani Excel'da ishlatish mumkinmi va yechim uchun pul to'lashga tayyormi — shuni tekshirish.

### Ishtirokchilar va davomiylik

- 5–10 nafar foydalanuvchi bilan boshlash;
- kamida ikki xil segmentni qamrab olish;
- jadval bilan muntazam ishlaydigan kishilarni tanlash;
- 2–4 hafta davomida kamida bitta real vazifani bajarish va qayta foydalanishni kuzatish.

Bu pilot uchun boshlang'ich taklif, bozor natijasi yoki statistik xulosa emas.

### Pilot qadamlari

1. **Boshlang'ich intervyu:** oxirgi real jadval vazifasi va hozirgi jarayonni tushunish.
2. **Birinchi vazifa:** foydalanuvchi jadval yaratadi yoki mavjud faylni import qiladi.
3. **Kuzatuv:** bajarish vaqti, xatolar, qo'lda tuzatishlar va savollarni qayd etish.
4. **Takroriy foydalanish:** pilot ichida boshqa vazifada ilovaga qaytishini tekshirish.
5. **Yakuniy suhbat:** qaysi qiymat uchun davom ettirishi yoki to'lashi mumkinligini aniqlash.

### Muvaffaqiyat o'lchovlari

- foydalanuvchi jadval yaratish/import bosqichini yakunladimi;
- natijani tahrirlab, `.xlsx` qilib yuklab oldimi;
- yakuniy faylni odatiy ish jarayonida ishlata oldimi;
- qancha katak yoki formatni tuzatishga to'g'ri keldi;
- keyinroq qaytib foydalandimi;
- foydalanishni davom ettirish yoki to'lashga rozimi, va nima sababdan.

Natija yig'ilmasidan oldin sun'iy foizli muvaffaqiyat maqsadlari qo'ymang. Boshlang'ich o'lchovdan so'ng qaror mezonlarini kelishib oling.

### Ma'lumotlar va maxfiylik

Pilotdan oldin ma'lumot qayerda saqlanishi va AI yoqilganida qaysi tashqi provayderga yuborilishi mumkinligini ishtirokchiga tushuntiring. Haqiqiy shaxsiy yoki tijorat siri ma'lumoti shart bo'lmasa, sintetik yoki niqoblangan namunalardan foydalaning.

## 8. Bozorga chiqish gipotezasi

1. Takroriy jadval vazifasi bor segmentni intervyu va pilot orqali tanlash.
2. Tanlangan segment uchun 2–3 ta real foydalanish misolini tayyorlash.
3. O'zbekcha amaliy qo'llanma va demo orqali qiziqishni sinash.
4. Telegram, LinkedIn, ta'lim/biznes hamjamiyatlari yoki hamkorlik kanallarini alohida tajriba sifatida baholash.
5. Qiziqishdan birinchi eksport va qayta foydalanishgacha bo'lgan yo'lni o'lchash.
6. Natija ko'rsatgan kanalni kengaytirish, samarasizini to'xtatish.

Hech bir kanal, hamkorlik yoki mijoz soni kafolatlanmagan. Sotuv strategiyasi sinov natijalariga qarab aniqlanadi.

## 9. Tijorat modeli

Pulli reja, billing va to'lov integratsiyasi amaldagi MVP'da tasdiqlanmagan. Kelajakda tekshiriladigan variantlar:

- **Bepul sinov yoki limitli reja:** yangi foydalanuvchiga qiymatni tushunishga yordam berish.
- **Individual tarif:** muntazam jadval yaratadigan yakka foydalanuvchilar uchun.
- **Jamoaviy tarif:** akkaunt, umumiy workspace va ruxsatlar yaratilgandan keyin.
- **Tashkilot rejasi:** maxfiylik, qo'llab-quvvatlash yoki joylashtirish talablari tasdiqlansa.

Tariflar AI so'rovlari xarajati, infratuzilma, qo'llab-quvvatlash va pilotdagi to'lashga tayyorlik asosida belgilanadi. Oldingi hujjatlarda uchragan narxlar amaldagi tarif emas.

## 10. Xatarlar va zarur ishlar

| Xatar yoki bo'shliq | Hozirgi holat | Tavsiya |
|---|---|---|
| AI noto'g'ri jadval yaratishi | Natijani inson tekshirishi kerak | Preview va tuzatish oqimini ravshan qilish |
| Chatni qurilmada tiklash | Brauzer-local ID; akkaunt yo'q | Cheklovni hujjatlashtirish, talab bo'lsa auth loyihalash |
| Maxfiy ma'lumot | AI provayder sozlamasiga bog'liq | Provayder siyosati va ma'lumot uzatilishini pilotdan oldin baholash |
| Excel mosligi | Import/eksportda qo'llab-quvvatlanadigan qism bilan cheklangan | Muhim workbook turlari bilan sinovlarni kengaytirish |
| Tijorat iqtisodiyoti | Tarif va billing yo'q | AI xarajati va foydalanuvchi qiymatini o'lchab, keyin narxlash |
| Zaxira va tiklash | Asosiy saqlash SQLite'da | Pilot miqyosiga mos zaxira/tiklash jarayonini sinash |

## 11. Kerakli qarorlar

- Birinchi sinov segmenti qaysi?
- Pilot ishtirokchilariga qanday chiqiladi?
- Qaysi ma'lumotlar AI provayderiga yuborilishi mumkin?
- Pilotda qanday natijalar o'lchanadi va rozilik qanday olinadi?
- Akkaunt, chat sinxronlash yoki jamoaviy foydalanish qachon zarur bo'ladi?
- Pulli tarifni qaysi metrika va sinov usuli bilan baholaymiz?

## Yakuniy taklif

SmartSheet AI'ni avval takroriy jadval vazifalari bor kichik foydalanuvchi guruhida sinash tavsiya etiladi. Pilotda vazifa bajarilishi, eksport sifati, qo'lda tuzatish, qayta foydalanish va to'lovga tayyorlik kuzatiladi. Shu dalillardan keyingina tarif, marketing va jamoaviy funksiyalarga sarmoya kiritish haqida qaror qabul qilinadi.
