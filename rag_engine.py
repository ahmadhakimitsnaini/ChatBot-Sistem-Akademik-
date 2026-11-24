"""
Mesin Utama Mini-RAG & Integrasi Cloud LLM (rag_engine.py)
Proyek: Chatbot FAQ Asisten Akademik Kampus

Modul ini menangani:
1. Pra-pemrosesan teks & pemuatan dataset FAQ (`faq_akademik.csv`).
2. Pembentukan indeks ruang vektor TF-IDF & pencarian Cosine Similarity.
3. Gerbang ambang batas (Threshold Gate) untuk mencegah halusinasi LLM.
4. Resolusi kunci API hibrida (`st.secrets` -> `.env` -> `None`).
5. Generasi jawaban natural menggunakan DeepSeek API (`deepseek-chat` via SDK `openai`)
   beserta mekanisme Graceful Degradation (Fallback Lokal).
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ==============================================================================
# KONSTANTA & KONFIGURASI DEFAULT
# ==============================================================================

DEFAULT_CSV_PATH: Path = Path(__file__).resolve().parent / "faq_akademik.csv"
DEFAULT_THRESHOLD: float = 0.18
DEFAULT_TOP_K: int = 3

DEFAULT_DEEPSEEK_BASE_URL: str = "https://zro.moonmath.ai/v1"
DEFAULT_DEEPSEEK_MODEL: str = "deepseek-v4.1-flash"
DEFAULT_LLM_TEMPERATURE: float = 0.1
DEFAULT_LLM_MAX_TOKENS: int = 2048
DEFAULT_LLM_TIMEOUT: float = 25.0

REQUIRED_COLUMNS: list[str] = [
    "id",
    "kategori",
    "pertanyaan",
    "jawaban",
    "sumber_pasal",
]
TEXT_COLUMNS: list[str] = [
    "kategori",
    "pertanyaan",
    "jawaban",
    "sumber_pasal",
]

# Daftar kata fungsi umum (stopwords ringan) Bahasa Indonesia untuk menekan noise
# pada kueri di luar topik tanpa membuang istilah penting domain akademik
# (seperti 'tidak', 'boleh', 'nilai', 'lulus', 'a', 'b', 'c', 'd', 'e', 'sks', 'ipk').
INDONESIAN_STOPWORDS: list[str] = sorted(
    {
        "ada",
        "adakah",
        "adalah",
        "agar",
        "aja",
        "akan",
        "aku",
        "anda",
        "antara",
        "apa",
        "apabila",
        "apakah",
        "atas",
        "atau",
        "bagaimana",
        "banget",
        "bawah",
        "belum",
        "berapa",
        "bila",
        "bisa",
        "cara",
        "contoh",
        "contohnya",
        "cuma",
        "dalam",
        "dan",
        "dapat",
        "dari",
        "deh",
        "dengan",
        "di",
        "dia",
        "dimana",
        "dong",
        "enggak",
        "ga",
        "gak",
        "gimana",
        "gua",
        "gue",
        "hanya",
        "harus",
        "ia",
        "ialah",
        "ingin",
        "ini",
        "itu",
        "jadi",
        "jika",
        "juga",
        "kah",
        "kagak",
        "kalau",
        "kalo",
        "kami",
        "kamu",
        "kan",
        "kapan",
        "karena",
        "ke",
        "kenapa",
        "kepada",
        "kira",
        "kita",
        "kok",
        "ku",
        "kurang",
        "lagi",
        "lah",
        "lebih",
        "mana",
        "masih",
        "mau",
        "melalui",
        "mengapa",
        "mengenai",
        "menjadi",
        "mereka",
        "merupakan",
        "misal",
        "misalnya",
        "mu",
        "nggak",
        "nih",
        "nya",
        "oleh",
        "pada",
        "paling",
        "para",
        "pengen",
        "perlu",
        "pernah",
        "pun",
        "saat",
        "saja",
        "sama",
        "sangat",
        "saya",
        "sebagai",
        "sebuah",
        "secara",
        "sedang",
        "sehingga",
        "sekitar",
        "sekali",
        "selama",
        "seluruh",
        "seperti",
        "seputar",
        "serta",
        "siapa",
        "sih",
        "sudah",
        "supaya",
        "tah",
        "telah",
        "tentang",
        "terhadap",
        "terkait",
        "tersebut",
        "tetapi",
        "tuh",
        "untuk",
        "wah",
        "ya",
        "yah",
        "yaitu",
        "yakni",
        "yang",
        "yuk",
    }
)

SYSTEM_PROMPT: str = """Anda adalah "Asisten Akademik Kampus", asisten virtual resmi yang membantu mahasiswa memahami peraturan di Buku Pedoman Akademik.
Tugas Anda adalah menjawab pertanyaan mahasiswa HANYA berdasarkan [KONTEKS PEDOMAN AKADEMIK] yang diberikan.

Aturan Ketat:
1. Jawablah dengan bahasa Indonesia yang sopan, ramah, jelas, dan terstruktur.
2. Cantumkan rujukan sumber pasal/bab (misal: "Berdasarkan Bab IV Pasal 12...") sesuai konteks yang relevan.
3. DILARANG KERAS mengarang, menebak, atau menambahkan aturan akademik di luar konteks yang tersedia.
4. Jika dari ketiga konteks yang diberikan ternyata tidak ada yang menjawab inti pertanyaan pengguna, katakan dengan jujur bahwa informasi spesifik tersebut belum tercantum dalam basis data FAQ pedoman saat ini."""


# ==============================================================================
# 1. PRA-PEMROSESAN TEKS & PEMUATAN DATASET
# ==============================================================================


def preprocess_text(text: object) -> str:
    """
    Menormalkan teks untuk kebutuhan pencocokan TF-IDF.

    Tahapan:
    1. Penanganan input None, NaN, atau tipe non-scalar (list/dict/ndarray) secara aman.
    2. Case folding ke huruf kecil.
    3. Menghapus karakter non-alfanumerik (mempertahankan huruf a-z, angka 0-9, dan spasi).
    4. Merapikan spasi berlebih dan spasi di awal/akhir teks.
    """
    if text is None or isinstance(text, bool):
        return ""
    if not pd.api.types.is_scalar(text):
        return ""
    if pd.isna(text):
        return ""

    normalized = str(text).lower()
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def strip_stopwords(text: object) -> str:
    """Menormalkan teks lalu membuang kata fungsi umum (INDONESIAN_STOPWORDS)."""
    clean = preprocess_text(text)
    if not clean:
        return ""
    stop_set = set(INDONESIAN_STOPWORDS)
    tokens = [tok for tok in clean.split() if tok not in stop_set]
    return " ".join(tokens)


def load_faq_data(csv_path: str | Path = DEFAULT_CSV_PATH) -> pd.DataFrame:
    """
    Memuat dataset FAQ dari file CSV, memvalidasi skema & keunikan ID,
    serta membentuk kolom virtual 'search_text' dan 'question_text'.

    - 'search_text': gabungan kategori, pertanyaan (digandakan 2x), dan jawaban.
    - 'question_text': gabungan kategori dan pertanyaan (untuk mencegah dilusi
      skor pada kueri mahasiswa yang sangat singkat atau mengandung typo).
    """
    path = Path(csv_path)
    if not path.is_file():
        raise FileNotFoundError(f"File dataset FAQ tidak ditemukan: {path.resolve()}")

    df = pd.read_csv(path, encoding="utf-8")
    if df.empty:
        raise ValueError("Dataset CSV kosong (tidak memiliki baris data).")

    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Kolom wajib tidak lengkap. Kolom yang hilang: {', '.join(missing_cols)}"
        )

    if df["id"].isna().any():
        raise ValueError("Kolom 'id' mengandung nilai kosong (NaN).")

    numeric_ids = pd.to_numeric(df["id"], errors="raise")
    if (numeric_ids % 1 != 0).any():
        raise ValueError("Kolom 'id' wajib berisi bilangan bulat (integer).")

    df["id"] = numeric_ids.astype(int)
    if df["id"].duplicated().any():
        dup_ids = df.loc[df["id"].duplicated(), "id"].tolist()
        raise ValueError(f"Kolom 'id' mengandung nilai duplikat: {dup_ids}")

    df[TEXT_COLUMNS] = df[TEXT_COLUMNS].fillna("").astype(str)

    combined_text = (
        df["kategori"]
        + " "
        + df["pertanyaan"]
        + " "
        + df["pertanyaan"]
        + " "
        + df["jawaban"]
    )
    df["search_text"] = combined_text.apply(strip_stopwords)
    df["question_text"] = (df["kategori"] + " " + df["pertanyaan"]).apply(
        strip_stopwords
    )

    if (df["search_text"] == "").all():
        raise ValueError("Seluruh baris 'search_text' kosong setelah pra-pemrosesan.")

    return df


# ==============================================================================
# 2. MESIN RETRIEVER HYBRID TF-IDF (WORD + CHAR_WB) & COSINE SIMILARITY
# ==============================================================================


def build_tfidf_index(df: pd.DataFrame) -> tuple[TfidfVectorizer, csr_matrix]:
    """
    Membangun objek TfidfVectorizer level kata (word n-gram) dan matriks TF-IDF
    dari kolom 'search_text'.
    """
    if "search_text" not in df.columns:
        raise ValueError("DataFrame harus memiliki kolom 'search_text'.")

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        sublinear_tf=True,
        token_pattern=r"(?u)\b\w+\b",
    )
    tfidf_matrix = vectorizer.fit_transform(df["search_text"])
    return vectorizer, tfidf_matrix


def initialize_rag_engine(csv_path: str | Path = DEFAULT_CSV_PATH) -> dict[str, Any]:
    """
    Memuat dataset CSV dan menginisialisasi indeks Hybrid Multi-View TF-IDF:
    1. Word N-gram (1, 2) pada dokumen lengkap ('search_text')
    2. Char-WB N-gram (3, 5) pada dokumen lengkap — tahan typo & variasi imbuhan
    3. Word N-gram (1, 2) & Char-WB (3, 5) pada ringkasan judul/pertanyaan ('question_text')

    Dirancang untuk dibungkus dengan @st.cache_resource pada app.py.
    """
    df = load_faq_data(csv_path)
    vectorizer, tfidf_matrix = build_tfidf_index(df)

    char_vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        sublinear_tf=True,
    )
    char_matrix = char_vectorizer.fit_transform(df["search_text"])

    q_word_vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        sublinear_tf=True,
        token_pattern=r"(?u)\b\w+\b",
    )
    q_word_matrix = q_word_vectorizer.fit_transform(df["question_text"])

    q_char_vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        sublinear_tf=True,
    )
    q_char_matrix = q_char_vectorizer.fit_transform(df["question_text"])

    return {
        "df": df,
        "vectorizer": vectorizer,
        "tfidf_matrix": tfidf_matrix,
        "char_vectorizer": char_vectorizer,
        "char_matrix": char_matrix,
        "q_word_vectorizer": q_word_vectorizer,
        "q_word_matrix": q_word_matrix,
        "q_char_vectorizer": q_char_vectorizer,
        "q_char_matrix": q_char_matrix,
    }


def retrieve_faq(
    query: str,
    engine: dict[str, Any],
    top_k: int = DEFAULT_TOP_K,
) -> list[dict[str, Any]]:
    """
    Mencari Top-k entri FAQ yang paling mirip dengan pertanyaan pengguna
    menggunakan Hybrid Multi-View Cosine Similarity (Word + Char-WB TF-IDF)
    sehingga tetap akurat pada pertanyaan singkat, sinonim, maupun typo ringan.
    """
    df: pd.DataFrame = engine["df"]
    vectorizer: TfidfVectorizer = engine["vectorizer"]
    tfidf_matrix: csr_matrix = engine["tfidf_matrix"]

    k = max(1, min(int(top_k), len(df)))
    clean_query = strip_stopwords(query)

    if not clean_query:
        scores = np.zeros(len(df), dtype=float)
    else:
        sim_word = cosine_similarity(
            vectorizer.transform([clean_query]), tfidf_matrix
        ).flatten()

        if "char_vectorizer" in engine and "q_word_vectorizer" in engine:
            sim_char = cosine_similarity(
                engine["char_vectorizer"].transform([clean_query]),
                engine["char_matrix"],
            ).flatten()
            sim_q_word = cosine_similarity(
                engine["q_word_vectorizer"].transform([clean_query]),
                engine["q_word_matrix"],
            ).flatten()
            sim_q_char = cosine_similarity(
                engine["q_char_vectorizer"].transform([clean_query]),
                engine["q_char_matrix"],
            ).flatten()
            scores = (
                0.35 * sim_word
                + 0.25 * sim_char
                + 0.25 * sim_q_word
                + 0.15 * sim_q_char
            )
        else:
            scores = sim_word

    top_indices = np.argsort(scores)[::-1][:k]

    results: list[dict[str, Any]] = []
    for idx in top_indices:
        row = df.iloc[int(idx)]
        results.append(
            {
                "id": int(row["id"]),
                "kategori": str(row["kategori"]),
                "pertanyaan": str(row["pertanyaan"]),
                "jawaban": str(row["jawaban"]),
                "sumber_pasal": str(row["sumber_pasal"]),
                "score": float(scores[int(idx)]),
            }
        )
    return results


# ==============================================================================
# 3. RESOLUSI KREDENSIAL & INTEGRASI DEEPSEEK CLOUD LLM
# ==============================================================================


def _is_valid_key_string(value: object) -> bool:
    """Memeriksa apakah string API key bukan nilai kosong atau teks placeholder."""
    if not isinstance(value, str):
        return False
    cleaned = value.strip()
    if not cleaned:
        return False
    placeholder_markers = ("masukkan_api_key", "your_api_key", "isi_api_key")
    return not any(marker in cleaned.lower() for marker in placeholder_markers)


def get_api_key(env_var: str = "DEEPSEEK_API_KEY") -> str | None:
    """
    Mengambil API Key dengan rantai resolusi hibrida:
    1. st.secrets (untuk lingkungan produksi Streamlit Community Cloud).
    2. Variabel lingkungan os.getenv / file .env (untuk pengembangan lokal).
    3. None (jika tidak tersedia, sehingga sistem beralih ke mode Fallback Lokal).
    """
    try:
        import streamlit as st

        secret_val = st.secrets.get(env_var)
        if _is_valid_key_string(secret_val):
            return str(secret_val).strip()
    except Exception:
        pass

    load_dotenv(override=False)
    env_val = os.getenv(env_var)
    if _is_valid_key_string(env_val):
        return str(env_val).strip()

    return None


def _get_config_value(key: str, default: str) -> str:
    """Membaca konfigurasi non-rahasia (seperti BASE_URL atau MODEL) dari st.secrets atau .env."""
    try:
        import streamlit as st

        val = st.secrets.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    except Exception:
        pass

    load_dotenv(override=False)
    env_val = os.getenv(key)
    if isinstance(env_val, str) and env_val.strip():
        return env_val.strip()
    return default


def build_user_prompt(query: str, references: list[dict[str, Any]]) -> str:
    """Merakit blok konteks Top-k hasil retrieval beserta pertanyaan mahasiswa."""
    context_blocks: list[str] = []
    for i, ref in enumerate(references, start=1):
        block = (
            f"---\n"
            f"Referensi {i} (Skor Kemiripan: {ref['score']:.2f} | "
            f"Kategori: {ref['kategori']} | Sumber: {ref['sumber_pasal']})\n"
            f"Pertanyaan Terkait: {ref['pertanyaan']}\n"
            f"Isi Aturan/Jawaban: {ref['jawaban']}"
        )
        context_blocks.append(block)

    joined_context = "\n".join(context_blocks) + "\n---"
    return (
        f"[KONTEKS PEDOMAN AKADEMIK (TOP-{len(references)} HASIL RETRIEVAL)]\n"
        f"{joined_context}\n\n"
        f"[PERTANYAAN MAHASISWA]\n"
        f"{query.strip()}"
    )


def generate_llm_answer(
    query: str,
    references: list[dict[str, Any]],
    api_key: str,
    base_url: str | None = None,
    model: str | None = None,
) -> str:
    """
    Memanggil DeepSeek API (OpenAI-compatible) menggunakan model deepseek-chat
    dengan temperature rendah untuk menghasilkan jawaban natural bebas halusinasi.
    """
    resolved_base_url = base_url or _get_config_value(
        "DEEPSEEK_BASE_URL", DEFAULT_DEEPSEEK_BASE_URL
    )
    resolved_model = model or _get_config_value(
        "DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL
    )

    client = OpenAI(
        api_key=api_key,
        base_url=resolved_base_url,
        timeout=DEFAULT_LLM_TIMEOUT,
        max_retries=1,
    )

    request_kwargs: dict[str, Any] = {
        "model": resolved_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(query, references)},
        ],
        "temperature": DEFAULT_LLM_TEMPERATURE,
        "max_tokens": DEFAULT_LLM_MAX_TOKENS,
    }

    default_effort = "none" if "zro.moonmath.ai" in resolved_base_url else ""
    reasoning_effort = _get_config_value("LLM_REASONING_EFFORT", default_effort)
    if reasoning_effort:
        request_kwargs["reasoning_effort"] = reasoning_effort

    response = client.chat.completions.create(**request_kwargs)

    content = response.choices[0].message.content if response.choices else None
    if not content or not content.strip():
        raise RuntimeError("Respons dari DeepSeek API kosong.")
    return content.strip()


def build_fallback_response(top_reference: dict[str, Any]) -> str:
    """
    Menyusun jawaban terverifikasi langsung dari entri FAQ peringkat ke-1
    ketika Cloud LLM API tidak dapat diakses (Graceful Degradation).
    """
    return (
        f"Berdasarkan **{top_reference['sumber_pasal']}** "
        f"(Kategori: *{top_reference['kategori']}*):\n\n"
        f"{top_reference['jawaban']}\n\n"
        f"---\n"
        f"*Catatan: Jawaban ini disajikan langsung dari basis data lokal Buku Pedoman Akademik "
        f"(Mode Fallback Lokal aktif karena layanan Cloud LLM sedang tidak terhubung).*"
    )


def _format_api_error(exc: Exception) -> str:
    """Menyusun ringkasan error teknis yang bersih dan aman tanpa membocorkan payload mentah."""
    raw = f"{type(exc).__name__}: {exc}"
    lower = raw.lower()
    if "401" in lower or "authentication" in lower or "invalid" in lower:
        return "AuthenticationError (401): Kunci DEEPSEEK_API_KEY tidak valid atau belum aktif."
    if "402" in lower or "insufficient balance" in lower:
        return "APIStatusError (402 Insufficient Balance): Saldo akun DeepSeek API tidak mencukupi."
    if "429" in lower or "rate limit" in lower:
        return "RateLimitError (429): Batas kuota permintaan Cloud LLM tercapai."
    if "timeout" in lower:
        return "APITimeoutError: Waktu tunggu koneksi ke Cloud LLM habis (timeout)."
    if "connection" in lower:
        return "APIConnectionError: Tidak dapat terhubung ke server Cloud LLM."
    return f"{type(exc).__name__}: Gangguan pemanggilan layanan Cloud LLM."


# ==============================================================================
# 4. ORKESTRATOR UTAMA ASISTEN AKADEMIK
# ==============================================================================


def ask_academic_assistant(
    query: str,
    engine: dict[str, Any],
    threshold: float = DEFAULT_THRESHOLD,
    top_k: int = DEFAULT_TOP_K,
) -> dict[str, Any]:
    """
    Fungsi orkestrator utama yang dipanggil oleh app.py.

    Alur Keputusan:
    1. Jika kueri kosong atau seluruh skor == 0.0 -> status = "INVALID_INPUT".
    2. Jika 0.0 < max_score < threshold -> status = "OUT_OF_SCOPE" (tanpa memanggil LLM).
    3. Jika max_score >= threshold -> panggil DeepSeek LLM ("SUCCESS_LLM") atau
       beralih otomatis ke jawaban lokal FAQ #1 ("FALLBACK_LOCAL") bila API gagal.
    """
    clean_query = preprocess_text(query)
    meaningful_tokens = [
        tok for tok in clean_query.split() if tok not in INDONESIAN_STOPWORDS
    ]

    if not clean_query or not meaningful_tokens:
        return {
            "answer": (
                "Mohon masukkan pertanyaan akademik yang valid dan spesifik. "
                "Contoh: *\"Berapa syarat minimal kehadiran untuk mengikuti UAS?\"*"
            ),
            "status": "INVALID_INPUT",
            "max_score": 0.0,
            "references": [],
            "error_detail": None,
        }

    references = retrieve_faq(query=query, engine=engine, top_k=top_k)
    max_score = references[0]["score"] if references else 0.0

    # Input 1 kata acak / gibberish yang berada di bawah ambang batas (TC-04)
    if max_score < threshold and len(meaningful_tokens) <= 1:
        return {
            "answer": (
                "Maaf, input yang Anda masukkan terlalu singkat atau tidak dikenali. "
                "Silakan tulis pertanyaan lengkap seputar akademik kampus (misal: KRS, UKT, "
                "kehadiran UAS, nilai/IPK, cuti akademik, magang, atau tugas akhir)."
            ),
            "status": "INVALID_INPUT",
            "max_score": 0.0,
            "references": [],
            "error_detail": None,
        }

    if max_score < threshold:
        return {
            "answer": (
                "Maaf, pertanyaan Anda berada di luar cakupan **Buku Pedoman Akademik Kampus** "
                f"(skor kemiripan tertinggi: `{max_score:.2f}` < ambang batas `{threshold:.2f}`).\n\n"
                "Saya hanya dapat menjawab pertanyaan seputar:\n"
                "- **Registrasi & KRS**\n"
                "- **Perkuliahan & Kehadiran**\n"
                "- **Evaluasi & Penilaian**\n"
                "- **Status Mahasiswa & Administrasi**\n"
                "- **Magang / PKL & Tugas Akhir**"
            ),
            "status": "OUT_OF_SCOPE",
            "max_score": max_score,
            "references": references if max_score > 0.0 else [],
            "error_detail": None,
        }

    api_key = get_api_key("DEEPSEEK_API_KEY")
    if not api_key:
        return {
            "answer": build_fallback_response(references[0]),
            "status": "FALLBACK_LOCAL",
            "max_score": max_score,
            "references": references,
            "error_detail": "DEEPSEEK_API_KEY belum dikonfigurasi (menggunakan basis data lokal).",
        }

    try:
        llm_answer = generate_llm_answer(
            query=query,
            references=references,
            api_key=api_key,
        )
        return {
            "answer": llm_answer,
            "status": "SUCCESS_LLM",
            "max_score": max_score,
            "references": references,
            "error_detail": None,
        }
    except Exception as exc:
        return {
            "answer": build_fallback_response(references[0]),
            "status": "FALLBACK_LOCAL",
            "max_score": max_score,
            "references": references,
            "error_detail": _format_api_error(exc),
        }
