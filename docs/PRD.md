# Product Requirements Document (PRD)
## Chatbot FAQ Asisten Akademik Kampus (Berbasis Mini-RAG & Cloud LLM)

---

## 1. Informasi Dokumen & Konteks Proyek

| Atribut | Keterangan |
| :--- | :--- |
| **Nama Produk** | Asisten Akademik Kampus (Chatbot FAQ ber-LLM) |
| **Versi Dokumen** | 1.0 |
| **Mata Kuliah** | Sistem Cerdas (TI24317) – Pertemuan 14 & UAS Pertemuan 15 |
| **Tema Modul** | B. Chatbot FAQ ber-LLM |
| **Tim Pengembang** | 1 Orang (*Solo Developer*) |
| **Target Deployment** | *Online* via Streamlit Community Cloud (`share.streamlit.io`) |
| **Sumber Data Utama** | Buku Pedoman Akademik Kampus |

> **Catatan Konteks Penilaian:** Sesuai Modul 14, proyek ini dirancang untuk memenuhi spesifikasi teknis tema B (minimal 28 entri FAQ + RAG mini + antarmuka chat) sekaligus siap dikembangkan menjadi Proyek Akhir Individu pada UAS Pertemuan 15.

---

## 2. Ringkasan Eksekutif & Latar Belakang

### 2.1 Pernyataan Masalah (*Problem Statement*)
Mahasiswa—terutama mahasiswa baru—sering mengalami kesulitan mencari informasi administratif dan akademik secara cepat di dalam Buku Pedoman Akademik Kampus yang tebal dan berbentuk dokumen statis (PDF). Akibatnya, pertanyaan berulang seputar KRS, UKT, cuti akademik, magang/PKL, dan syarat kelulusan sering membebani admin prodi maupun dosen wali.

### 2.2 Solusi yang Diusulkan
Membangun aplikasi web **Chatbot FAQ Asisten Akademik Kampus** berbasis Streamlit yang dapat diakses langsung melalui *browser* secara *online*. Aplikasi ini menggabungkan teknik **Mini-RAG (*Retrieval-Augmented Generation*)** menggunakan TF-IDF dan *Cosine Similarity* untuk mengambil pasal/informasi relevan dari basis data FAQ Buku Pedoman, lalu menggunakan **Cloud LLM API** untuk merangkai jawaban yang natural, ramah, dan bebas halusinasi.

---

## 3. Tujuan & Kriteria Keberhasilan (*Success Metrics*)

Proyek dinyatakan berhasil apabila memenuhi kriteria berikut (selaras dengan rubrik Modul 14):
1. **Fungsionalitas Penuh:** Aplikasi berjalan tanpa *error* di lingkungan lokal maupun *online* (Streamlit Community Cloud), dengan alur lengkap: `Input Pengguna` $\rightarrow$ `Pencarian Konteks (RAG)` $\rightarrow$ `Generasi Jawaban (LLM)` $\rightarrow$ `Output + Referensi`.
2. **Akurasi & Anti-Halusinasi:** Chatbot hanya menjawab berdasarkan isi Buku Pedoman Akademik. Pertanyaan di luar cakupan akademik ditolak secara sopan melalui mekanisme ambang batas (*threshold*).
3. **Penguasaan Kode 100%:** Karena dikerjakan mandiri, pengembang mampu menjelaskan arsitektur, alur data, dan setiap baris kode pada `app.py` maupun `rag_engine.py` saat sesi demo dan uji tanya-jawab.
4. **Dokumentasi Lengkap:** Tersedia `README.md` yang memuat deskripsi, sumber & lisensi Buku Pedoman, panduan instalasi lokal, tautan aplikasi *online*, serta catatan pengerjaan.

---

## 4. Target Pengguna

* **Pengguna Utama (Mahasiswa Aktif & Mahasiswa Baru):** Membutuhkan jawaban cepat, akurat, dan mudah dipahami terkait aturan akademik kampus kapan saja melalui *browser* HP atau laptop tanpa perlu membuka file PDF pedoman.
* **Pengguna Sekunder (Penguji / Dosen Pengampu):** Menguji fungsionalitas aplikasi, penanganan kasus batas (*edge cases*), transparansi mekanisme RAG, serta kualitas kode dan dokumentasi.

---

## 5. Ruang Lingkup Proyek (*Scope*)

### 5.1 Dalam Ruang Lingkup (*In-Scope*)
* Basis pengetahuan terstruktur minimal $28$–$35$ entri FAQ yang diekstrak dari Buku Pedoman Akademik Kampus.
* Mesin *retriever* lokal menggunakan `TfidfVectorizer` dan `cosine_similarity` (`scikit-learn`).
* Integrasi dengan penyedia *Cloud LLM API* menggunakan **DeepSeek API** (`deepseek-chat` melalui SDK `openai` yang *OpenAI-compatible*).
* Antarmuka *chat* interaktif di Streamlit lengkap dengan riwayat percakapan (`st.session_state`), tombol pertanyaan cepat, tombol reset, dan *expander* referensi sumber FAQ.
* *Deployment* publik melalui GitHub dan Streamlit Community Cloud dengan manajemen kunci API aman (`st.secrets`).

### 5.2 Di Luar Ruang Lingkup (*Out-of-Scope*)
* Integrasi langsung ke database SIAKAD kampus (nilai personal, jadwal individu, atau status pembayaran UKT mahasiswa tertentu).
* Sistem autentikasi/login pengguna dan penyimpanan riwayat percakapan permanen di database eksternal.
* *Fine-tuning* model LLM sendiri atau penggunaan *vector database* berskala besar (seperti Pinecone/Milvus).

---

## 6. Spesifikasi Kebutuhan Fungsional (*Functional Requirements*)

| ID | Fitur | Deskripsi Kebutuhan | Prioritas |
| :--- | :--- | :--- | :--- |
| **FR-01** | **Basis Pengetahuan FAQ** | Sistem memuat file `faq_akademik.csv` berisi minimal $28$ entri dengan kolom: `id`, `kategori`, `pertanyaan`, `jawaban`, dan `sumber_pasal`. | Wajib |
| **FR-02** | **Mini-RAG Retriever** | Sistem mengubah pertanyaan pengguna dan seluruh pertanyaan/jawaban FAQ menjadi vektor TF-IDF, lalu menghitung skor kemiripan menggunakan *cosine similarity* untuk mengambil $k$ entri teratas ($k = 3$). | Wajib |
| **FR-03** | **Ambang Batas (*Threshold*)** | Jika skor kemiripan tertinggi kurang dari nilai ambang batas (misalnya $\theta < 0.20$), sistem **tidak memanggil LLM** dan langsung mengembalikan pesan standar bahwa informasi tidak ditemukan dalam pedoman akademik. | Wajib |
| **FR-04** | **Generasi Jawaban LLM** | Sistem mengirimkan *top-$k$* konteks FAQ beserta pertanyaan pengguna ke *Cloud LLM API* dengan *system prompt* ketat agar LLM hanya merangkum fakta dari konteks yang diberikan. | Wajib |
| **FR-05** | **Antarmuka Chat Interaktif** | Menggunakan komponen `st.chat_message` dan `st.chat_input`. Riwayat pesan selama sesi aktif disimpan di `st.session_state`. | Wajib |
| **FR-06** | **Transparansi Referensi** | Di bawah setiap jawaban bot, tampilkan `st.expander("Lihat Referensi Pedoman")` yang memuat entri FAQ, nomor pasal/halaman, dan skor kemiripan hasil *retriever*. | Wajib |
| **FR-07** | **Sidebar & Utilitas** | Menyediakan panel samping berisi informasi singkat aplikasi, daftar kategori topik yang didukung, 3–4 tombol pertanyaan cepat (*quick prompts*), dan tombol **"Reset Percakapan"**. | Tambahan (Direkomendasikan) |

---

## 7. Spesifikasi Kebutuhan Non-Fungsional (*Non-Functional Requirements*)

1. **Performa & Efisiensi (*Caching*):**
   * Pemuatan dataset CSV dan pembentukan matriks TF-IDF **wajib** dibungkus dengan dekorator `@st.cache_resource` (atau `@st.cache_data`) agar tidak dijalankan ulang setiap kali pengguna mengirim pesan.
   * Waktu respons end-to-end ditargetkan $\le 5$ detik dalam kondisi jaringan normal.
2. **Keamanan Kredensial:**
   * Kunci API (*API Key*) **dilarang keras** ditulis langsung (*hardcoded*) di dalam kode sumber atau diunggah ke repositori GitHub publik.
   * Gunakan file `.env` (masuk ke `.gitignore`) untuk pengujian lokal dan fitur `st.secrets` pada Streamlit Community Cloud.
3. **Keandalan & Penanganan Galat (*Error Handling*):**
   * Pemanggilan *Cloud LLM API* wajib dibungkus blok `try-except` untuk menangani *timeout*, kuota habis (*rate limit*), atau kegagalan jaringan.
   * *Fallback* opsional: jika API gagal dihubungi, sistem dapat menampilkan jawaban mentah dari entri FAQ dengan skor kemiripan tertinggi beserta pesan pemberitahuan.
4. **Keterbacaan & Pemisahan Kode:**
   * Terapkan prinsip pemisahan peran (sesuai Modul 14): logika data & RAG diletakkan di `rag_engine.py`, sedangkan antarmuka pengguna diletakkan di `app.py`.

---

## 8. Arsitektur Sistem & Alur Data

```text
[Pengguna (Browser)]
        │  1. Mengirim pertanyaan (st.chat_input)
        ▼
[app.py (Streamlit UI)]
        │  2. Memanggil fungsi pencarian konteks
        ▼
[rag_engine.py (TF-IDF + Cosine Similarity)] ◄── [faq_akademik.csv (≥28 entri)]
        │
        ├──► Jika skor tertinggi < threshold (misal 0.20)
        │         └──► Kembalikan respons "Di luar cakupan Pedoman Akademik"
        │
        └──► Jika skor tertinggi >= threshold
                  │  3. Kirim Top-3 Konteks FAQ + Pertanyaan + System Prompt
                  ▼
           [Cloud LLM API (DeepSeek - deepseek-chat)]
                  │  4. Kembalikan jawaban natural berbasis konteks
                  ▼
[app.py (Streamlit UI)] ──► Tampilkan Jawaban + Expander Referensi + Simpan ke Session State
```

---

## 9. Struktur Dataset & Direktori Proyek

### 9.1 Skema Dataset (`faq_akademik.csv`)
Minimal $28$ entri yang mencakup topik inti Buku Pedoman Akademik, dibagi secara proporsional ke beberapa kategori:
* **Registrasi & KRS** (misal: batas waktu KRS, revisi KRS, beban SKS maksimal).
* **Perkuliahan & Kehadiran** (misal: syarat minimal presensi UAS, izin sakit/dispensasi, keterlambatan).
* **Evaluasi & Penilaian** (misal: konversi nilai huruf ke angka, perhitungan IPS/IPK, syarat lulus mata kuliah, remedial/mengulang).
* **Status Mahasiswa & Administrasi** (misal: prosedur cuti akademik, aktif kembali, pindah kelas, sanksi DO/peringatan akademik).
* **Magang / PKL & Tugas Akhir** (misal: syarat SKS magang, syarat pengajuan judul TA, syarat sidang dan yudisium).

**Contoh Struktur Kolom:**
```csv
id,kategori,pertanyaan,jawaban,sumber_pasal
1,Perkuliahan,"Berapa syarat minimal kehadiran mahasiswa untuk bisa mengikuti UAS?","Mahasiswa wajib memenuhi kehadiran minimal 75% dari total pertemuan dalam satu semester untuk dapat mengikuti UAS.","Bab IV Pasal 12"
```

### 9.2 Struktur Direktori Proyek (*Deliverables*)
```text
chatbot-asisten-akademik/
├── app.py                  # Antarmuka Streamlit (UI & Session State)
├── rag_engine.py           # Modul TF-IDF Retriever, Thresholding, & pemanggilan Cloud LLM
├── faq_akademik.csv        # Basis pengetahuan minimal 28 entri dari Buku Pedoman
├── requirements.txt        # Daftar pustaka Python untuk deployment Streamlit Cloud
├── README.md               # Dokumentasi lengkap (deskripsi, sumber/lisensi, cara jalan, link demo)
├── .gitignore              # Mengabaikan .env, __pycache__/, .streamlit/secrets.toml
└── .env.example            # Contoh variabel lingkungan (tanpa API Key asli)
```

---

## 10. Rencana Pengujian (*Test Plan & Edge Cases*)

| ID Uji | Skenario Pengujian | Input Contoh | Hasil yang Diharapkan |
| :--- | :--- | :--- | :--- |
| **TC-01** | Pertanyaan langsung sesuai FAQ | *"Berapa minimal kehadiran untuk ikut UAS?"* | Jawaban akurat sesuai pedoman, *expander* menampilkan pasal yang tepat. |
| **TC-02** | Pertanyaan dengan parafrasa/sinonim | *"Kalau sering bolos apakah tetap boleh ujian akhir?"* | *Retriever* tetap menemukan entri kehadiran (atau dapat disempurnakan dengan kata kunci), LLM menjawab relevan. |
| **TC-03** | Pertanyaan di luar topik (*Out-of-Scope*) | *"Resep nasi goreng yang enak apa ya?"* | Skor $< \theta$; bot menolak dengan sopan tanpa memanggil LLM dan tanpa halusinasi. |
| **TC-04** | Input kosong / karakter acak | *"asdfghjkl"* atau spasi kosong | Tidak terjadi *crash*; ditangani oleh validasi input atau *threshold*. |
| **TC-05** | Simulasi kegagalan Cloud API | *API Key* tidak valid atau koneksi diputus | Muncul pesan galat ramah (`st.error` / `st.warning`) tanpa menampilkan *traceback* mentah Python. |
| **TC-06** | Reset percakapan | Klik tombol *"Reset Chat"* di sidebar | Riwayat percakapan di layar bersih kembali ke pesan sambutan awal. |

---

## 11. Rencana Deployment Online (Streamlit Community Cloud)

1. **Persiapan Dependensi:** Buat file `requirements.txt` berisi pustaka minimal yang dipakai (`streamlit`, `pandas`, `scikit-learn`, `openai`, `python-dotenv`).
2. **Unggah ke GitHub:** Inisialisasi repositori Git, pastikan `.env` dan `.streamlit/secrets.toml` tercantum di `.gitignore`, lalu *push* seluruh file proyek ke repositori GitHub.
3. **Konfigurasi di Streamlit Cloud:**
   * Masuk ke `share.streamlit.io` menggunakan akun GitHub.
   * Pilih **Create app** $\rightarrow$ arahkan ke repositori, branch `main`, dan file utama `app.py`.
   * Buka menu **Advanced settings $\rightarrow$ Secrets**, lalu masukkan kunci API dengan format TOML:
     ```toml
     DEEPSEEK_API_KEY = "masukkan_api_key_asli_di_sini"
     DEEPSEEK_BASE_URL = "https://api.deepseek.com"
     DEEPSEEK_MODEL = "deepseek-chat"
     RAG_THRESHOLD = "0.18"
     ```
4. **Verifikasi Publik:** Uji tautan URL publik aplikasi dari perangkat berbeda (laptop dan *smartphone*) untuk memastikan seluruh skenario uji (TC-01 hingga TC-06) berjalan lancar.

---

## 12. Linimasa Pengerjaan (*Solo Developer*)

| Fase | Target Waktu | Aktivitas Utama | Output (*Deliverable*) |
| :--- | :--- | :--- | :--- |
| **Fase 1: Data & Setup** | Hari 1 (P14) | Ekstraksi minimal 28 entri FAQ dari Buku Pedoman Kampus ke CSV; siapkan *environment* dan uji koneksi Cloud LLM API. | `faq_akademik.csv`, `requirements.txt` |
| **Fase 2: Core RAG** | Hari 1 (P14) | Bangun `rag_engine.py` (TF-IDF, *Cosine Similarity*, kalibrasi nilai *threshold*, dan integrasi prompt LLM). | `rag_engine.py` berfungsi di terminal |
| **Fase 3: UI Prototipe** | Hari 1 (P14) | Bangun `app.py` dasar (`st.chat_message`, `st.chat_input`, `@st.cache_resource`) untuk *progress check* P14. | Aplikasi lokal berjalan setengah jadi |
| **Fase 4: Polish & Edge Cases** | H+1 s.d. H+3 | Tambahkan *sidebar*, tombol reset, *quick prompts*, *expander* referensi, serta `try-except` API error. | Aplikasi lokal stabil & lulus TC-01 s.d. TC-06 |
| **Fase 5: Online Deploy & Docs** | H+4 s.d. H+5 | *Push* ke GitHub, *deploy* ke Streamlit Community Cloud, konfigurasi `st.secrets`, dan lengkapi `README.md`. | Tautan aplikasi *online* aktif + `README.md` |
| **Fase 6: Persiapan Demo UAS** | H-1 (Menuju P15) | Simulasi demo 10 menit (alur normal, *edge case*, bedah kode `rag_engine.py` & `app.py`). | Siap demo final UAS Pertemuan 15 |

---

## 13. Analisis & Mitigasi Risiko

| Risiko | Dampak | Strategi Mitigasi |
| :--- | :--- | :--- |
| **Skor TF-IDF rendah saat pengguna memakai bahasa santai/sinonim** | Pertanyaan valid keliru dianggap *out-of-scope*. | Gabungkan kolom `pertanyaan` + `kategori` + kata kunci sinonim di dalam teks yang diindeks TF-IDF, dan lakukan kalibrasi nilai *threshold* (misal uji rentang $0.15$–$0.25$). |
| **Halusinasi jawaban dari LLM** | Bot mengarang aturan akademik yang tidak ada di Buku Pedoman. | Gunakan *temperature* rendah ($0.0$–$0.2$) pada konfigurasi API dan berikan instruksi tegas di *system prompt* untuk hanya merujuk konteks. |
| **Kuota / Rate Limit API Cloud habis saat demo** | Aplikasi gagal menjawab saat dinilai penguji. | Siapkan mekanisme *fallback* yang menampilkan langsung jawaban teks dari entri FAQ teratas, serta siapkan akun/API key cadangan. |
| **Aplikasi tidur (*sleeping*) di Streamlit Cloud** | Penundaan 30–60 detik saat demo dimulai. | Buka dan aktifkan tautan aplikasi 10–15 menit sebelum giliran demo, dan tetap sediakan versi lokal (`localhost`) sebagai cadangan. |