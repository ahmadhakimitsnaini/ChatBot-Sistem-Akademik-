"""
Antarmuka Pengguna Streamlit (app.py) — Dark Forest Glassmorphism (Opsi A: 3 Zona)
Proyek: Chatbot FAQ Asisten Akademik Politeknik Negeri Madiun (PNM)
Berbasis Hybrid Mini-RAG (TF-IDF Word + Char-WB) & Cloud LLM (OpenAI-Compatible)
"""

from __future__ import annotations

import html
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
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
# 1. KONFIGURASI HALAMAN, KONSTANTA & CACHING
# ==============================================================================

st.set_page_config(
    page_title="PNM·AI — Asisten Akademik Kampus",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

STYLES_PATH: Path = Path(__file__).resolve().parent / "assets" / "styles.css"
ALL_CATEGORIES_LABEL: str = "Semua Topik"

WELCOME_MESSAGE: str = (
    "Halo! 👋 Saya **Asisten Akademik Politeknik Negeri Madiun (PNM)** "
    "*(Prodi D-III Teknologi Informasi)*.\n\n"
    "Anda dapat mengetik pertanyaan langsung di bawah ini atau memilih salah satu "
    "topik dari panel **Jelajah Topik & FAQ** di sebelah kiri. Seluruh jawaban "
    "merujuk langsung pada **Buku Pedoman Akademik PNM 2024/2025** dan "
    "**Kalender Akademik 2025/2026**."
)

CATEGORY_ICONS: dict[str, str] = {
    "Registrasi & KRS": "📝",
    "Perkuliahan & Kehadiran": "📅",
    "Evaluasi & Penilaian": "📊",
    "Status Mahasiswa & Administrasi": "🏛️",
    "Magang / PKL & Tugas Akhir": "🎓",
}


@st.cache_data(show_spinner=False)
def load_custom_css(css_path: Path) -> str:
    """Memuat stylesheet eksternal satu kali dan menyimpannya di cache."""
    if not css_path.is_file():
        return ""
    return css_path.read_text(encoding="utf-8")


@st.cache_resource(show_spinner="Memuat basis pengetahuan Buku Pedoman Akademik PNM...")
def get_cached_rag_engine() -> dict[str, Any]:
    """Memuat CSV dan membangun indeks Hybrid TF-IDF satu kali di memori server."""
    return initialize_rag_engine(DEFAULT_CSV_PATH)


def get_initial_threshold() -> float:
    """Membaca nilai threshold default dari environment bila tersedia."""
    raw = os.getenv("RAG_THRESHOLD", str(DEFAULT_THRESHOLD))
    try:
        val = float(raw)
        return min(max(val, 0.05), 0.50)
    except ValueError:
        return DEFAULT_THRESHOLD


def current_time_label() -> str:
    """Mengembalikan label waktu singkat (HH:MM) untuk metadata pesan chat."""
    return datetime.now().strftime("%H:%M")


# ==============================================================================
# 2. MANAJEMEN SESSION STATE
# ==============================================================================


def create_welcome_entry() -> dict[str, Any]:
    """Membangun objek pesan sambutan awal asisten."""
    return {
        "role": "assistant",
        "content": WELCOME_MESSAGE,
        "status": "WELCOME",
        "max_score": 1.0,
        "references": [],
        "error_detail": None,
        "timestamp": current_time_label(),
    }


def init_session_state() -> None:
    """Menginisialisasi state percakapan, filter kategori, dan antrean prompt."""
    if "messages" not in st.session_state:
        st.session_state.messages = [create_welcome_entry()]
    if "pending_prompt" not in st.session_state:
        st.session_state.pending_prompt = None
    if "selected_category" not in st.session_state:
        st.session_state.selected_category = ALL_CATEGORIES_LABEL


def reset_conversation() -> None:
    """Mengosongkan riwayat percakapan kembali ke pesan sambutan awal (TC-06)."""
    st.session_state.messages = [create_welcome_entry()]
    st.session_state.pending_prompt = None


# ==============================================================================
# 3. ZONA 1: SIDEBAR NAVIGASI & STATUS SISTEM
# ==============================================================================


def render_sidebar(df: pd.DataFrame) -> float:
    """Merender sidebar bergaya dark-glass: brand, new chat, menu kategori, demo & status."""
    api_key_ready = get_api_key("DEEPSEEK_API_KEY") is not None

    with st.sidebar:
        st.markdown(
            """
            <div class="brand-header">
                <span class="brand-title">PNM·AI</span>
                <span class="brand-tag">D-III TI</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("＋  Percakapan Baru", use_container_width=True, type="primary"):
            reset_conversation()
            st.rerun()

        st.markdown('<div class="nav-section-label">Menu Kategori</div>', unsafe_allow_html=True)

        # Tombol Semua Topik
        all_active = st.session_state.selected_category == ALL_CATEGORIES_LABEL
        all_prefix = "✦ " if all_active else "○ "
        if st.button(
            f"{all_prefix}Semua Topik ({len(df)})",
            key="nav_cat_all",
            use_container_width=True,
        ):
            st.session_state.selected_category = ALL_CATEGORIES_LABEL
            st.rerun()

        # Tombol per Kategori Resmi
        for idx, cat in enumerate(df["kategori"].unique()):
            count = int((df["kategori"] == cat).sum())
            icon = CATEGORY_ICONS.get(cat, "📌")
            is_active = st.session_state.selected_category == cat
            prefix = "▸ " if is_active else ""
            if st.button(
                f"{prefix}{icon} {cat} ({count})",
                key=f"nav_cat_{idx}",
                use_container_width=True,
            ):
                st.session_state.selected_category = cat
                st.rerun()

        st.markdown('<div class="nav-section-label">Pengaturan Demo</div>', unsafe_allow_html=True)
        with st.expander("⚙️ Kalibrasi Threshold (θ)", expanded=False):
            threshold = st.slider(
                "Ambang Batas Kemiripan (θ)",
                min_value=0.05,
                max_value=0.50,
                value=get_initial_threshold(),
                step=0.01,
                help="Pertanyaan dengan skor Hybrid TF-IDF di bawah θ ditolak tanpa memanggil Cloud LLM.",
            )
            st.caption("Default terkalibrasi: **0.18** (100% presisi pada 28 kueri uji).")

        # Kartu Status Sistem (adaptasi panel bawah referensi)
        status_cls = "online" if api_key_ready else "fallback"
        status_txt = "🟢 Cloud LLM Aktif" if api_key_ready else "🟡 Fallback Lokal"
        st.markdown(
            f"""
            <div class="status-card">
                <div class="status-card-title">Basis Pengetahuan PNM</div>
                <div class="status-card-desc">
                    <strong>{len(df)} pasal terindeks</strong> dari Buku Pedoman Akademik
                    PNM 2024/2025 (SK Direktur No. 265/2024) &amp; Kaldik 2025/2026.
                </div>
                <span class="status-pill {status_cls}">{status_txt}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return threshold


# ==============================================================================
# 4. ZONA 2: PANEL JELAJAH TOPIK & PERTANYAAN CEPAT
# ==============================================================================


def render_topic_explorer(df: pd.DataFrame) -> None:
    """Merender panel kiri-tengah berisi pencarian cepat dan kartu pertanyaan FAQ."""
    active_cat = st.session_state.selected_category
    filtered_df = (
        df if active_cat == ALL_CATEGORIES_LABEL else df[df["kategori"] == active_cat]
    )

    with st.container(border=True):
        st.markdown(
            f"""
            <div class="panel-header-row">
                <h2 class="panel-header-title">Jelajah Topik</h2>
                <span class="count-pill">{len(filtered_df)} pasal</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        search_term = st.text_input(
            "Cari topik atau pasal",
            placeholder="🔍 Cari pasal (alpa, UKT, nilai D, cuti)...",
            label_visibility="collapsed",
            key="topic_search_input",
        ).strip()

        if search_term:
            mask = (
                filtered_df["pertanyaan"].str.contains(search_term, case=False, na=False)
                | filtered_df["jawaban"].str.contains(search_term, case=False, na=False)
                | filtered_df["kategori"].str.contains(search_term, case=False, na=False)
                | filtered_df["sumber_pasal"].str.contains(search_term, case=False, na=False)
            )
            filtered_df = filtered_df[mask]

        st.markdown('<div class="topic-list-wrap">', unsafe_allow_html=True)
        with st.container(height=500, border=False):
            if filtered_df.empty:
                st.markdown(
                    """
                    <div class="empty-topic-state">
                        <strong>Topik tidak ditemukan</strong><br/>
                        Coba kata kunci lain seperti <em>KRS, alpa, kompen, nilai D, cuti, magang,</em> atau <em>cumlaude</em>.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                for cat_name, group in filtered_df.groupby("kategori", sort=False):
                    icon = CATEGORY_ICONS.get(str(cat_name), "📌")
                    safe_cat = html.escape(str(cat_name))
                    st.markdown(
                        f'<div class="category-divider-pill"><span>{icon} {safe_cat}</span></div>',
                        unsafe_allow_html=True,
                    )
                    for _, row in group.iterrows():
                        faq_id = int(row["id"])
                        question = str(row["pertanyaan"])
                        short_q = (
                            question[:86].rstrip() + "…" if len(question) > 88 else question
                        )
                        pasal = str(row["sumber_pasal"])
                        label = f"{short_q}\n📄 {pasal}"
                        if st.button(
                            label,
                            key=f"topic_card_{faq_id}",
                            use_container_width=True,
                        ):
                            st.session_state.pending_prompt = question
                            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# 5. ZONA 3: PANEL CHAT AKTIF & EXPANDER REFERENSI
# ==============================================================================


def render_status_badge(status: str, max_score: float, error_detail: str | None) -> None:
    """Menampilkan indikator status respons (ikon + teks, bukan warna semata)."""
    if status == "SUCCESS_LLM":
        st.markdown(
            f'<span class="status-pill online">✨ DeepSeek LLM • Skor {max_score:.2f}</span>',
            unsafe_allow_html=True,
        )
    elif status == "FALLBACK_LOCAL":
        st.markdown(
            f'<span class="status-pill fallback">⚡ Mode Fallback Lokal • Skor {max_score:.2f}</span>',
            unsafe_allow_html=True,
        )
        if error_detail:
            st.caption(f"Info teknis: {error_detail}")
    elif status == "OUT_OF_SCOPE":
        st.markdown(
            f'<span class="status-pill shield">🛡️ Gerbang Anti-Halusinasi • Skor {max_score:.2f}</span>',
            unsafe_allow_html=True,
        )


def render_references_expander(
    references: list[dict[str, Any]],
    status: str,
    max_score: float,
    error_detail: str | None = None,
) -> None:
    """Menampilkan badge status dan st.expander berisi Top-3 referensi pasal pedoman."""
    render_status_badge(status=status, max_score=max_score, error_detail=error_detail)

    if not references or status in ("WELCOME", "INVALID_INPUT"):
        return

    with st.expander("📚 Lihat Referensi Pedoman Akademik (Top-3 Hasil Retrieval)"):
        for idx, ref in enumerate(references, start=1):
            score_pct = ref["score"] * 100
            pasal = html.escape(str(ref["sumber_pasal"]))
            kategori = html.escape(str(ref["kategori"]))
            pertanyaan = html.escape(str(ref["pertanyaan"]))
            jawaban = html.escape(str(ref["jawaban"]))
            st.markdown(
                f"""
                <div class="ref-card">
                    <div class="ref-card-head">
                        <span class="ref-pasal">{idx}. {pasal} — {kategori}</span>
                        <span class="ref-score">Skor {ref['score']:.3f} ({score_pct:.1f}%)</span>
                    </div>
                    <div class="ref-body">
                        <strong>Pertanyaan FAQ:</strong> {pertanyaan}<br/>
                        <strong>Isi Pedoman:</strong> {jawaban}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_message_item(msg: dict[str, Any]) -> None:
    """Merender satu gelembung percakapan beserta header pengirim & timestamp."""
    role = msg["role"]
    avatar = "🎓" if role == "assistant" else "👤"
    ts = html.escape(str(msg.get("timestamp", "")))

    with st.chat_message(role, avatar=avatar):
        if role == "assistant":
            st.markdown(
                f"""
                <div class="msg-meta-row">
                    <div class="msg-sender-group">
                        <span class="msg-sender-name">Asisten PNM</span>
                        <span class="msg-badge">pnm.ai</span>
                    </div>
                    <span class="msg-time">{ts}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="msg-meta-row">
                    <span class="msg-sender-name">Anda</span>
                    <span class="msg-time">{ts}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(msg["content"])

        if role == "assistant":
            render_references_expander(
                references=msg.get("references", []),
                status=msg.get("status", ""),
                max_score=float(msg.get("max_score", 0.0)),
                error_detail=msg.get("error_detail"),
            )


def render_chat_workspace(engine: dict[str, Any], threshold: float) -> None:
    """Merender panel kanan (Zona 3): header identitas terpusat, riwayat chat, dan input."""
    with st.container(border=True):
        st.markdown(
            """
            <div class="chat-hero">
                <div class="chat-hero-avatar">🎓</div>
                <h1 class="chat-hero-title">Asisten Akademik PNM</h1>
                <div class="chat-hero-subtitle">
                    Buku Pedoman Akademik 2024/2025 &amp; Kalender Akademik 2025/2026
                </div>
                <div class="chat-hero-meta">
                    <span>Prodi D-III Teknologi Informasi</span>
                    <span>•</span>
                    <span>Hybrid Mini-RAG + DeepSeek</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Tangkap input dari chat_input atau klik kartu di Zona 2
        chat_container = st.container(height=425, border=False)
        with chat_container:
            for msg in st.session_state.messages:
                render_message_item(msg)

        chat_input_query = st.chat_input(
            "Ketik pertanyaan akademik Anda (misal: batas jam alpa, nilai D, syarat cuti)...",
            key="main_chat_input",
        )

        active_query: str | None = None
        if st.session_state.pending_prompt:
            active_query = st.session_state.pending_prompt
            st.session_state.pending_prompt = None
        elif chat_input_query is not None:
            active_query = chat_input_query

        if active_query is not None:
            user_entry = {
                "role": "user",
                "content": active_query,
                "timestamp": current_time_label(),
            }
            st.session_state.messages.append(user_entry)

            with chat_container:
                render_message_item(user_entry)
                with st.chat_message("assistant", avatar="🎓"):
                    with st.spinner("Mencari pasal di Buku Pedoman Akademik PNM..."):
                        result = ask_academic_assistant(
                            query=active_query,
                            engine=engine,
                            threshold=threshold,
                            top_k=DEFAULT_TOP_K,
                        )
                    assistant_entry = {
                        "role": "assistant",
                        "content": result["answer"],
                        "status": result["status"],
                        "max_score": result["max_score"],
                        "references": result["references"],
                        "error_detail": result["error_detail"],
                        "timestamp": current_time_label(),
                    }
                    st.markdown(
                        f"""
                        <div class="msg-meta-row">
                            <div class="msg-sender-group">
                                <span class="msg-sender-name">Asisten PNM</span>
                                <span class="msg-badge">pnm.ai</span>
                            </div>
                            <span class="msg-time">{assistant_entry['timestamp']}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.markdown(assistant_entry["content"])
                    render_references_expander(
                        references=assistant_entry["references"],
                        status=assistant_entry["status"],
                        max_score=assistant_entry["max_score"],
                        error_detail=assistant_entry["error_detail"],
                    )

            st.session_state.messages.append(assistant_entry)


# ==============================================================================
# 6. ENTRY POINT APLIKASI
# ==============================================================================


def main() -> None:
    css = load_custom_css(STYLES_PATH)
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    init_session_state()

    try:
        engine = get_cached_rag_engine()
    except Exception as exc:
        st.error(f"Gagal memuat basis pengetahuan FAQ: {exc}")
        st.stop()

    threshold = render_sidebar(engine["df"])

    # Tata letak Opsi A: Zona 2 (Jelajah Topik ~32%) | Zona 3 (Chat Aktif ~68%)
    col_topics, col_chat = st.columns([1.05, 2.25], gap="medium")
    with col_topics:
        render_topic_explorer(engine["df"])
    with col_chat:
        render_chat_workspace(engine=engine, threshold=threshold)


if __name__ == "__main__":
    main()
