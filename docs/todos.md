# Roadmap & Todo List Pengembangan: Chatbot FAQ Asisten Akademik Kampus
**Berbasis Mini-RAG (TF-IDF + Cosine Similarity) & Cloud LLM**

> **Acuan Utama:** [PRD.md](./PRD.md) & Hasil Analisa Teknis  
> **Target Akhir:** Aplikasi berjalan stabil secara lokal & *online* (`share.streamlit.io`), lulus seluruh skenario uji (`TC-01` s.d. `TC-06`), bebas halusinasi, dan siap didemokan pada Pertemuan 14 & UAS Pertemuan 15.

---

## Ringkasan Progres Fase
- [x] **Fase 1:** Inisialisasi Proyek, Lingkungan Kerja & Keamanan Kredensial
- [x] **Fase 2:** Penyusunan & Pengayaan Dataset Basis Pengetahuan (`faq_akademik.csv`)
- [x] **Fase 3:** Pengembangan Mesin Utama Mini-RAG & Integrasi Cloud LLM (`rag_engine.py`)
- [x] **Fase 4:** Pembangunan Antarmuka Pengguna Interaktif (`app.py`)
- [x] **Fase 5:** Pengujian Sistem, Kalibrasi & Penanganan Kasus Batas (*Edge Cases*)
- [ ] **Fase 6:** Dokumentasi, Deployment Online & Persiapan Demo UAS

---

## Fase 1: Inisialisasi Proyek, Lingkungan Kerja & Keamanan Kredensial
**Tujuan:** Menyiapkan fondasi direktori proyek, manajemen pustaka Python, serta pengamanan API Key agar tidak bocor ke repositori publik (*NFR-02*).

- [x] **1.1. Pembuatan File `.gitignore`**
  - [x] Abaikan file kredensial lokal: `.env` dan `.streamlit/secrets.toml`.
  - [x] Abaikan direktori cache & virtual environment: `__pycache__/`, `.venv/`, `venv/`, `.DS_Store`.
- [x] **1.2. Pembuatan File `.env.example`**
  - [x] Sediakan template variabel lingkungan tanpa kunci asli (`DEEPSEEK_API_KEY="masukkan_api_key_deepseek_anda_di_sini"`, `DEEPSEEK_BASE_URL="https://api.deepseek.com"`, `DEEPSEEK_MODEL="deepseek-chat"`).
  - [x] Tambahkan komentar petunjuk cara mendapatkan API Key di platform DeepSeek.
- [x] **1.3. Pembuatan File `requirements.txt`**
  - [x] Definisikan pustaka inti dengan versi yang kompatibel untuk Streamlit Community Cloud:
    - `streamlit`
    - `pandas`
    - `scikit-learn`
    - `python-dotenv`
    - `openai` (OpenAI-compatible SDK untuk DeepSeek API)
- [x] **1.4. Penyiapan Lingkungan Lokal (*Virtual Environment*)**
  - [x] Buat dan aktifkan virtual environment Python lokal.
  - [x] Instal seluruh dependensi dari `requirements.txt`.
  - [x] Buat file `.env` lokal untuk pengujian koneksi API.

---

## Fase 2: Penyusunan & Pengayaan Dataset Basis Pengetahuan (`faq_akademik.csv`)
**Tujuan:** Membangun basis data FAQ minimal **28–35 entri** (*FR-01*) yang terstruktur dan diperkaya kata kunci/sinonim bahasa sehari-hari mahasiswa untuk mengatasi keterbatasan pencocokan kata pada TF-IDF (*Mitigasi Risiko 1 & TC-02*).

- [x] **2.1. Perancangan Skema Kolom CSV**
  - [x] Gunakan kolom wajib sesuai PRD: `id`, `kategori`, `pertanyaan`, `jawaban`, `sumber_pasal`.
  - [x] *(Rekomendasi Hasil Analisa)* Pastikan di dalam teks `pertanyaan` atau kolom tambahan/gabungan sudah disisipkan sinonim istilah populer mahasiswa (misal: *"bolos/absen/alfa"*, *"DO/keluar/dikeluarkan"*, *"IP/nilai/indeks prestasi"*, *"telat/terlambat"*, *"bayar/UKT/SPP"*).
- [x] **2.2. Pengisian Entri Kategori 1: Registrasi & KRS (6–7 Entri)**
  - [x] Jadwal dan prosedur pengisian KRS setiap awal semester.
  - [x] Ketentuan dan batas waktu perubahan/revisi KRS (*KRS Batal-Tambah*).
  - [x] Aturan penentuan beban SKS maksimal berdasarkan IPS semester sebelumnya.
  - [x] Sanksi dan prosedur jika terlambat melakukan registrasi ulang / pengisian KRS.
  - [x] Prosedur konsultasi dan persetujuan KRS oleh Dosen Wali (Pembimbing Akademik).
  - [x] Ketentuan pengambilan mata kuliah lintas semester atau mata kuliah bersyarat (*prasyarat*).
- [x] **2.3. Pengisian Entri Kategori 2: Perkuliahan & Kehadiran (6–7 Entri)**
  - [x] Syarat minimal persentase kehadiran (misal $\ge 75\%$ atau $80\%$) untuk dapat mengikuti UAS *(Kritis untuk TC-01 & TC-02: sertakan kata kunci "bolos", "absen", "tidak masuk", "ujian akhir")*.
  - [x] Prosedur pengajuan izin tidak hadir karena sakit (surat dokter) atau dispensasi kegiatan kampus.
  - [x] Aturan toleransi keterlambatan hadir di kelas dan tata tertib perkuliahan.
  - [x] Ketentuan pelaksanaan Ujian Tengah Semester (UTS) dan Ujian Akhir Semester (UAS).
  - [x] Prosedur ujian susulan bagi mahasiswa yang berhalangan hadir karena alasan sah.
  - [x] Beban belajar per 1 SKS (tatap muka, tugas terstruktur, dan belajar mandiri).
- [x] **2.4. Pengisian Entri Kategori 3: Evaluasi & Penilaian (6–7 Entri)**
  - [x] Tabel konversi nilai angka ke nilai huruf dan bobot (A, AB/B+, B, BC/C+, C, D, E).
  - [x] Rumus dan cara perhitungan Indeks Prestasi Semester (IPS) dan Indeks Prestasi Kumulatif (IPK).
  - [x] Batas nilai minimal kelulusan mata kuliah wajib dan mata kuliah pilihan.
  - [x] Ketentuan mengulang mata kuliah (remedial/semester pendek) untuk perbaikan nilai.
  - [x] Prosedur komplain atau sanggah nilai jika terdapat kesalahan input oleh dosen.
  - [x] Komponen penilaian akhir mata kuliah (kehadiran, tugas, kuis, UTS, UAS).
- [x] **2.5. Pengisian Entri Kategori 4: Status Mahasiswa & Administrasi (6–7 Entri)**
  - [x] Syarat, batas maksimal, dan prosedur pengajuan Cuti Akademik (berhenti studi sementara).
  - [x] Prosedur pengajuan aktif kuliah kembali setelah masa cuti akademik berakhir.
  - [x] Status mahasiswa Tidak Aktif (Mangkir) dan konsekuensi administratifnya.
  - [x] Kriteria evaluasi studi bertahap, surat peringatan akademik, dan aturan *Drop Out* (DO) / putus studi.
  - [x] Batas masa studi maksimal program Sarjana/Diploma.
  - [x] Prosedur pembayaran UKT, keringanan, atau penundaan pembayaran UKT.
- [x] **2.6. Pengisian Entri Kategori 5: Magang / PKL & Tugas Akhir (6–7 Entri)**
  - [x] Syarat jumlah SKS minimal dan IPK untuk mengambil Kerja Praktik (KP) / Magang / PKL.
  - [x] Syarat akademik dan administratif pengajuan proposal / judul Tugas Akhir (Skripsi).
  - [x] Ketentuan pembimbingan dan masa berlaku pengerjaan Tugas Akhir.
  - [x] Syarat pendaftaran Sidang Tugas Akhir (bebas tanggungan SKS, nilai D/E, perpustakaan, administrasi).
  - [x] Syarat kelulusan akhir, pendaftaran Yudisium, dan Wisuda.
  - [x] Predikat kelulusan (*Cumlaude* / Dengan Pujian, Sangat Memuaskan, Memuaskan) beserta syarat masa studi & IPK.
- [x] **2.7. Validasi Dataset CSV**
  - [x] Pastikan total baris $\ge 28$ entri (target optimal: **30–35 entri**).
  - [x] Pastikan format tanda kutip (`"..."`) pada CSV valid, tidak ada kolom kosong (`NaN`), dan encoding menggunakan `UTF-8`.

---

## Fase 3: Pengembangan Mesin Utama Mini-RAG & Integrasi Cloud LLM (`rag_engine.py`)
**Tujuan:** Membangun logika pencari konteks berbasis TF-IDF + Cosine Similarity dan penghubung ke Cloud LLM API (DeepSeek) yang bersih, modular, terdokumentasi (*docstring*), dan tahan gagal (*FR-02, FR-03, FR-04, NFR-03, NFR-04*).

- [x] **3.1. Fungsi Pemuatan & Pembersihan Teks (`preprocess_text` & `load_faq_data`)**
  - [x] Buat fungsi normalisasi teks ringan: *lowercase*, pertahankan angka/desimal & alfanumerik, penanganan input non-scalar aman, dan *trimming* spasi.
  - [x] Buat fungsi pembaca `faq_akademik.csv` (dengan validasi keunikan `id` & default path berjangkar `__file__`) yang menggabungkan kolom `kategori + pertanyaan (2x) + jawaban` menjadi satu kolom indeks pencarian (`search_text`).
- [x] **3.2. Mesin Retriever TF-IDF (`build_tfidf_index`, `initialize_rag_engine` & `retrieve_faq`)**
  - [x] Inisialisasi `TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, token_pattern=r"(?u)\b\w+\b", stop_words=INDONESIAN_STOPWORDS)` dari `scikit-learn` untuk menangkap nilai huruf tunggal (`A/B/C/D/E`), kata tunggal, maupun frasa 2 kata.
  - [x] Hitung vektor pertanyaan pengguna dan bandingkan dengan matriks TF-IDF FAQ menggunakan `cosine_similarity`.
  - [x] Ambil *Top-$k$* ($k = 3$) entri FAQ dengan skor kemiripan tertinggi beserta metadata lengkapnya (`id`, `kategori`, `pertanyaan`, `jawaban`, `sumber_pasal`, `score`).
- [x] **3.3. Mekanisme Ambang Batas / Thresholding (*Anti-Halusinasi*)**
  - [x] Tetapkan parameter `threshold` default ($\theta = 0.18$, dapat dikonfigurasi).
  - [x] Implementasikan validasi input kosong / karakter acak (`status = "INVALID_INPUT"`, *TC-04*).
  - [x] Jika skor tertinggi $< \theta$, langsung kembalikan `status = "OUT_OF_SCOPE"` dan pesan penolakan sopan **tanpa memanggil Cloud LLM API** (*FR-03*).
- [x] **3.4. Resolusi Kunci API Hibrida (`get_api_key`)**
  - [x] Prioritas 1: Baca `DEEPSEEK_API_KEY` dari `st.secrets` (untuk lingkungan produksi Streamlit Community Cloud).
  - [x] Prioritas 2: Baca `DEEPSEEK_API_KEY` dari `os.getenv()` / `.env` (untuk lingkungan pengembangan lokal).
  - [x] Prioritas 3: Kembalikan `None` dengan aman (memicu mode *fallback* tanpa crash).
- [x] **3.5. Fungsi Generasi Jawaban Cloud LLM & Orkestrator (`generate_llm_answer`, `build_fallback_response`, `ask_academic_assistant`)**
  - [x] Susun *System Prompt* ketat pada model `deepseek-chat` yang menginstruksikan LLM untuk:
    1. Berperan sebagai **Asisten Akademik Kampus** yang ramah, sopan, dan jelas.
    2. **Hanya** menjawab berdasarkan *Top-3 Konteks Pedoman Akademik* yang dilampirkan.
    3. Menyebutkan rujukan pasal/bab sesuai konteks dan dilarang keras mengarang aturan di luar konteks.
  - [x] Atur konfigurasi `temperature=0.1`, `max_tokens=512`, `timeout=15.0`, dan `max_retries=1` agar jawaban konsisten, faktual, dan responsif.
  - [x] Bungkus pemanggilan API dengan blok `try-except` (*NFR-03*):
    - Jika API berhasil: kembalikan `status = "SUCCESS_LLM"` + jawaban LLM + daftar referensi *Top-3*.
    - Jika API gagal (*timeout*, *saldo/quota habis HTTP 402/429*, atau *API key tidak valid*): aktifkan **Mode Fallback Otomatis** (`status = "FALLBACK_LOCAL"`) yang menampilkan jawaban langsung dari entri FAQ peringkat 1 beserta penanda informasi bahwa respons berasal dari basis data lokal (*TC-05*).

---

## Fase 4: Pembangunan Antarmuka Pengguna Interaktif (`app.py`)
**Tujuan:** Membangun aplikasi web Streamlit yang responsif, cepat (*cached*), transparan menampilkan pasal referensi, dan menyimpan riwayat sesi percakapan (*FR-05, FR-06, FR-07, NFR-01*).

- [x] **4.1. Konfigurasi Halaman & Caching Sumber Daya**
  - [x] Setel `st.set_page_config(page_title="Asisten Akademik Kampus", page_icon="🎓", layout="wide")`.
  - [x] Bungkus pemuatan dataset CSV dan pembentukan matriks TF-IDF dengan dekorator `@st.cache_resource` agar hanya diinisialisasi satu kali saat server menyala (*NFR-01*).
- [x] **4.2. Desain Sidebar & Utilitas (*FR-07*)**
  - [x] Tampilkan identitas aplikasi, deskripsi singkat, dan indikator status koneksi LLM / jumlah FAQ terindeks.
  - [x] Tampilkan daftar 5 kategori topik akademik yang didukung.
  - [x] Buat 3–4 tombol **Pertanyaan Cepat (*Quick Prompts*)** yang langsung memicu percakapan saat diklik.
  - [x] Buat tombol **"🔄 Reset Percakapan"** yang mengosongkan `st.session_state.messages` dan mengembalikan sapaan awal (*TC-06*).
  - [x] *(Opsional Pengujian)* Sediakan pengaturan *expander* di sidebar untuk melihat/menguji nilai *Threshold* ($\theta$) saat demo dengan dosen penguji.
- [x] **4.3. Manajemen `st.session_state` & Render Riwayat Chat (*FR-05*)**
  - [x] Inisialisasi `st.session_state.messages` dengan pesan sambutan awal dari asisten.
  - [x] Simpan setiap pesan asisten lengkap dengan atribut: `role`, `content`, `references` (daftar *Top-3* FAQ & skor), dan `status` (LLM / Out-of-Scope / Fallback).
  - [x] Render seluruh riwayat pesan menggunakan `st.chat_message("user")` dan `st.chat_message("assistant")`.
- [x] **4.4. Komponen Transparansi Referensi (*FR-06*)**
  - [x] Di bawah setiap pesan asisten, tampilkan `st.expander("📚 Lihat Referensi Pedoman Akademik")`.
  - [x] Tampilkan di dalam *expander*: Nomor/Nama Pasal (`sumber_pasal`), Kategori, Pertanyaan & Jawaban asli dari CSV, serta **Skor Kemiripan (*Cosine Similarity*)** dalam format persentase/desimal.
- [x] **4.5. Alur Pemrosesan Input Pengguna**
  - [x] Tangkap input baik dari `st.chat_input("Tanyakan aturan akademik kampus...")` maupun dari tombol *Quick Prompt* di sidebar.
  - [x] Tampilkan indikator loading (`st.spinner("Mencari di Buku Pedoman Akademik...")`) saat memanggil `rag_engine.py`.

---

## Fase 5: Pengujian Sistem, Kalibrasi & Penanganan Kasus Batas (*Edge Cases*)
**Tujuan:** Memverifikasi seluruh skenario pengujian pada Bagian 10 PRD (`TC-01` s.d. `TC-06`) dan memastikan waktu respons $\le 5$ detik.

- [x] **5.1. Kalibrasi Nilai Threshold ($\theta$) via Skrip/Terminal**
  - [x] Uji 5 pertanyaan langsung, 5 pertanyaan parafrasa/bahasa santai, dan 5 pertanyaan di luar topik untuk memastikan nilai $\theta$ (sekitar $0.18 - 0.22$) memisahkan pertanyaan valid dan *out-of-scope* secara presisi.
- [x] **5.2. Eksekusi Rencana Pengujian Wajib (Bagian 10 PRD)**
  - [x] **Uji TC-01 (Pertanyaan Langsung):** *"Berapa minimal kehadiran untuk ikut UAS?"* $\rightarrow$ Jawaban akurat + pasal tepat di *expander*.
  - [x] **Uji TC-02 (Parafrasa / Bahasa Santai):** *"Kalau sering bolos apakah tetap boleh ujian akhir?"* $\rightarrow$ Retriever menemukan entri kehadiran + LLM menjawab relevan.
  - [x] **Uji TC-03 (Out-of-Scope):** *"Resep nasi goreng yang enak apa ya?"* $\rightarrow$ Skor $< \theta$, ditolak sopan tanpa memanggil LLM.
  - [x] **Uji TC-04 (Input Kosong / Karakter Acak):** *"asdfghjkl"* atau spasi $\rightarrow$ Tidak crash, ditangani dengan aman.
  - [x] **Uji TC-05 (Simulasi Kegagalan Cloud API):** Kosongkan/salahkan API Key sementara $\rightarrow$ Tidak muncul *traceback* Python mentah, muncul notifikasi ramah & jawaban *fallback* dari FAQ teratas.
  - [x] **Uji TC-06 (Reset Percakapan):** Klik tombol *"Reset Percakapan"* $\rightarrow$ Layar bersih kembali ke pesan sambutan awal.

---

## Fase 6: Dokumentasi, Deployment Online & Persiapan Demo UAS
**Tujuan:** Menyelesaikan dokumentasi akhir, mempublikasikan aplikasi ke Streamlit Community Cloud, dan mempersiapkan penguasaan kode 100% (*Kriteria Keberhasilan 3 & 4*).

- [x] **6.1. Penyusunan `README.md` Lengkap**
  - [x] Deskripsi aplikasi, latar belakang masalah, dan fitur utama.
  - [x] Diagram arsitektur Mini-RAG (`TF-IDF` + `Cosine Similarity` + `Cloud LLM`).
  - [x] Penjelasan sumber data Buku Pedoman Akademik & lisensi/cakupan dataset.
  - [x] Panduan instalasi & cara menjalankan di lokal langkah demi langkah.
  - [x] Tautan (*link*) aplikasi online di Streamlit Community Cloud.
- [ ] **6.2. Deployment ke GitHub & Streamlit Community Cloud**
  - [ ] Pastikan `.env` tidak ikut ter-commit (`git status`).
  - [ ] Push seluruh kode ke repositori GitHub.
  - [ ] Hubungkan repositori ke `share.streamlit.io`, atur `app.py` sebagai *main file*, dan tambahkan API Key pada menu **Advanced Settings $\rightarrow$ Secrets**.
  - [ ] Uji URL publik dari browser laptop dan HP.
- [ ] **6.3. Persiapan Penguasaan Kode & Demo UAS (Pertemuan 15)**
  - [ ] Siapkan alur presentasi & demo 10 menit (pembukaan, demo *happy path*, demo *anti-halusinasi/out-of-scope*, dan penjelasan kode `rag_engine.py` serta `app.py`).
  - [ ] Pastikan aplikasi online sudah dibangunkan (*wake up*) 15 menit sebelum jadwal demo dan server `localhost` siap sebagai cadangan.
