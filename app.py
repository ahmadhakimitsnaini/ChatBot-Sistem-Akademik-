"""
Antarmuka Pengguna Streamlit (app.py)
Proyek: Chatbot FAQ Asisten Akademik Kampus (Mini-RAG & DeepSeek Cloud LLM)
"""

from __future__ import annotations

import os
from typing import Any

import streamlit as st

from rag_engine import (
    DEFAULT_CSV_PATH,
    DEFAULT_THRESHOLD,
    DEFAULT_TOP_K,
    ask_academic_assistant,
    get_api_key,
    initialize_rag_engine,
)

# ==============================================================================
# 1. KONFIGURASI HALAMAN & CACHING SUMBER DAYA
# ==============================================================================

st.set_page_config(
    page_title="Asisten Akademik Kampus",
    page_icon="🎓",
    layout="wide",
)

WELCOME_MESSAGE: str = (
    "Halo! 👋 Saya **Asisten Akademik Politeknik Negeri Madiun (PNM)** "
    "*(Prodi D-III Teknologi Informasi)*. Silakan tanyakan aturan seputar "
    "**Daftar Ulang & KRS, Kehadiran/Alpa & Kompensasi, Konversi Nilai & IPK, "
    "Cuti, Dicutikan & DO, maupun Magang, Tugas Akhir & Predikat Kelulusan** "
    "berdasarkan Buku Pedoman Akademik PNM 2024/2025 & Kalender Akademik 2025/2026."
)

QUICK_PROMPTS: list[str] = [
    "Berapa batas jam alpa (bolos) sebelum kena SP atau Putus Studi (DO)?",
    "Bagaimana tabel konversi nilai angka ke huruf (A, AB, B, BC, C, D, E) di PNM?",
    "Apakah mahasiswa yang Cuti Akademik atau Dicutikan wajib membayar UKT?",
    "Apa syarat IPK dan masa studi untuk predikat Pujian (Cumlaude) di PNM?",
]


@st.cache_resource(show_spinner="Memuat basis pengetahuan Buku Pedoman Akademik...")
def get_cached_rag_engine() -> dict[str, Any]:
    """Memuat CSV dan membangun matriks TF-IDF satu kali di memori server."""
    return initialize_rag_engine(DEFAULT_CSV_PATH)


def get_initial_threshold() -> float:
    """Membaca nilai threshold default dari environment/secrets bila tersedia."""
    raw = os.getenv("RAG_THRESHOLD", str(DEFAULT_THRESHOLD))
    try:
        val = float(raw)
        return min(max(val, 0.05), 0.50)
    except ValueError:
        return DEFAULT_THRESHOLD


# ==============================================================================
# 2. INISIALISASI SESSION STATE & ENGINE
# ==============================================================================


def init_session_state() -> None:
    """Menginisialisasi riwayat percakapan dan antrean quick prompt."""
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": WELCOME_MESSAGE,
                "status": "WELCOME",
                "max_score": 1.0,
                "references": [],
                "error_detail": None,
            }
        ]
    if "pending_prompt" not in st.session_state:
        st.session_state.pending_prompt = None


def reset_conversation() -> None:
    """Mengosongkan riwayat obrolan kembali ke pesan sambutan awal (TC-06)."""
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": WELCOME_MESSAGE,
            "status": "WELCOME",
            "max_score": 1.0,
            "references": [],
            "error_detail": None,
        }
    ]
    st.session_state.pending_prompt = None


# ==============================================================================
# 3. KOMPONEN RENDER REFERENSI & SIDEBAR
# ==============================================================================


def render_references_expander(
    references: list[dict[str, Any]],
    status: str,
    max_score: float,
    error_detail: str | None = None,
) -> None:
    """Menampilkan badge status dan st.expander berisi Top-3 referensi pedoman."""
    if status == "FALLBACK_LOCAL":
        st.caption(
            "ℹ️ **Mode Fallback Lokal:** Menampilkan jawaban terverifikasi langsung dari basis data Buku Pedoman."
        )
        if error_detail:
            st.caption(f"Detail teknis: `{error_detail}`")
    elif status == "OUT_OF_SCOPE":
        st.caption(
            f"🛡️ **Gerbang Anti-Halusinasi Aktif:** Pertanyaan ditolak karena skor kemiripan tertinggi (`{max_score:.2f}`) di bawah ambang batas."
        )

    if not references or status in ("WELCOME", "INVALID_INPUT"):
        return

    with st.expander("📚 Lihat Referensi Pedoman Akademik (Top-3 Hasil Retrieval)"):
        for idx, ref in enumerate(references, start=1):
            score_pct = ref["score"] * 100
            st.markdown(
                f"**{idx}. {ref['sumber_pasal']}** — *{ref['kategori']}*  \n"
                f"Skor Kemiripan: **`{ref['score']:.3f}`** (`{score_pct:.1f}%`)"
            )
            st.markdown(f"- **Pertanyaan FAQ:** {ref['pertanyaan']}")
            st.markdown(f"- **Isi Pedoman:** {ref['jawaban']}")
            if idx < len(references):
                st.divider()


def render_sidebar(engine: dict[str, Any]) -> float:
    """Merender sidebar informasi, quick prompts, tombol reset, dan kalibrasi threshold."""
    df = engine["df"]
    api_key_ready = get_api_key("DEEPSEEK_API_KEY") is not None

    with st.sidebar:
        st.title("🎓 Asisten Akademik")
        st.caption(
            "Chatbot FAQ berbasis **Mini-RAG (TF-IDF + Cosine Similarity)** "
            "& **DeepSeek Cloud LLM**."
        )

        if api_key_ready:
            st.success(f"🟢 Cloud LLM Aktif ({len(df)} FAQ Terindeks)")
        else:
            st.warning(
                f"🟡 Mode Fallback Lokal ({len(df)} FAQ Terindeks)\n\n"
                "Isi `DEEPSEEK_API_KEY` di `.env` atau `st.secrets` untuk mengaktifkan generasi DeepSeek LLM."
            )

        st.divider()
        st.subheader("📂 Kategori Topik")
        for cat in df["kategori"].unique():
            count = int((df["kategori"] == cat).sum())
            st.markdown(f"- **{cat}** ({count} pasal)")

        st.divider()
        st.subheader("⚡ Pertanyaan Cepat")
        for i, prompt_text in enumerate(QUICK_PROMPTS):
            if st.button(prompt_text, key=f"quick_prompt_{i}", use_container_width=True):
                st.session_state.pending_prompt = prompt_text

        st.divider()
        if st.button("🔄 Reset Percakapan", use_container_width=True, type="primary"):
            reset_conversation()
            st.rerun()

        with st.expander("⚙️ Pengaturan Pengujian (Demo)"):
            threshold = st.slider(
                "Ambang Batas Kemiripan (θ)",
                min_value=0.05,
                max_value=0.50,
                value=get_initial_threshold(),
                step=0.01,
                help="Pertanyaan dengan skor Cosine Similarity di bawah θ akan ditolak tanpa memanggil Cloud LLM.",
            )
    return threshold


# ==============================================================================
# 4. ALUR UTAMA APLIKASI (MAIN LOOP)
# ==============================================================================


def main() -> None:
    init_session_state()

    try:
        engine = get_cached_rag_engine()
    except Exception as exc:
        st.error(f"Gagal memuat basis pengetahuan FAQ: {exc}")
        st.stop()

    threshold = render_sidebar(engine)

    st.title("🎓 Chatbot FAQ Asisten Akademik Kampus")
    st.caption(
        "Tanyakan informasi peraturan akademik kampus secara cepat, akurat, dan lengkap dengan rujukan pasalnya."
    )

    # Render seluruh riwayat percakapan
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                render_references_expander(
                    references=msg.get("references", []),
                    status=msg.get("status", ""),
                    max_score=float(msg.get("max_score", 0.0)),
                    error_detail=msg.get("error_detail"),
                )

    # Tangkap input dari chat_input atau tombol Quick Prompt di sidebar
    chat_input_query = st.chat_input("Tanyakan aturan akademik kampus (misal: syarat kehadiran UAS)...")
    active_query: str | None = None

    if st.session_state.pending_prompt:
        active_query = st.session_state.pending_prompt
        st.session_state.pending_prompt = None
    elif chat_input_query is not None:
        active_query = chat_input_query

    if active_query is not None:
        st.session_state.messages.append(
            {
                "role": "user",
                "content": active_query,
            }
        )
        with st.chat_message("user"):
            st.markdown(active_query)

        with st.chat_message("assistant"):
            with st.spinner("Mencari di Buku Pedoman Akademik..."):
                result = ask_academic_assistant(
                    query=active_query,
                    engine=engine,
                    threshold=threshold,
                    top_k=DEFAULT_TOP_K,
                )
            st.markdown(result["answer"])
            render_references_expander(
                references=result["references"],
                status=result["status"],
                max_score=result["max_score"],
                error_detail=result["error_detail"],
            )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": result["answer"],
                "status": result["status"],
                "max_score": result["max_score"],
                "references": result["references"],
                "error_detail": result["error_detail"],
            }
        )


if __name__ == "__main__":
    main()
