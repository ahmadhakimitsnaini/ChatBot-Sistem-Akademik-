"""
Skrip Kalibrasi Ambang Batas (Threshold θ) Mini-RAG (scripts/calibrate_threshold.py)
Mengevaluasi daya pisah Cosine Similarity antara kueri akademik valid
(langsung & parafrasa bahasa santai mahasiswa PNM) dan kueri di luar cakupan (Out-of-Scope).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import rag_engine

BENCHMARK_QUERIES: list[tuple[str, str, set[int] | None]] = [
    # 1. Pertanyaan Langsung (In-Scope)
    ("DIRECT-01", "Bagaimana prosedur daftar ulang dan pengisian KRS di PNM?", {1}),
    ("DIRECT-02", "Berapa batas jam alpa sebelum kena Surat Peringatan atau Putus Studi?", {8, 25}),
    ("DIRECT-03", "Bagaimana tabel konversi nilai angka ke nilai huruf di PNM?", {15}),
    ("DIRECT-04", "Apa syarat dan prosedur pengajuan Cuti Akademik?", {22}),
    ("DIRECT-05", "Apa syarat IPK dan masa studi untuk predikat Pujian (Cumlaude)?", {34}),
    ("DIRECT-06", "Kapan jadwal pelaksanaan UTS dan UAS pada Kalender Akademik 2025/2026?", {4, 14}),
    # 2. Pertanyaan Parafrasa / Bahasa Santai Mahasiswa (In-Scope)
    ("PARAPH-01", "Kalau sering bolos apakah tetap boleh ikut ujian akhir UAS?", {8}),
    ("PARAPH-02", "Gimana cara ngitung kompen kalau bolos alpa?", {10}),
    ("PARAPH-03", "Nilai D masih lulus semester nggak ya?", {18}),
    ("PARAPH-04", "Kalau lagi cuti kuliah atau dicutikan tetap bayar UKT gak?", {23}),
    ("PARAPH-05", "Kapan mahasiswa bisa kena DO atau dikeluarkan?", {25, 8}),
    ("PARAPH-06", "Boleh gak gak masuk kuliah karena sakit? Harus pakai surat dokter?", {9}),
    ("PARAPH-07", "Telat daftar ulang sanksinya apa?", {2}),
    ("PARAPH-08", "Magang D3 TI di semester berapa dan berapa SKS?", {29, 7}),
    ("PARAPH-09", "Gelar lulusan D3 Teknologi Informasi PNM itu apa?", {35}),
    ("PARAPH-10", "Batas waktu ambil ijazah dan transkrip setelah lulus berapa lama?", {21}),
    ("PARAPH-11", "Ikut MBKM bisa konversi berapa SKS?", {30}),
    ("PARAPH-12", "Kalau gak lulus ujian sidang Tugas Akhir gimana?", {32}),
    ("TYPO-01", "bagaimana cara regristrasi dan krs", {1}),
    ("TYPO-02", "telat daftar ulng sanksinya apa", {2}),
    ("TYPO-03", "syarat cumlade ipk berapa", {34}),
    ("SHORT-01", "syarat cuti", {22}),
    # 3. Pertanyaan Out-of-Scope & Gibberish (Harus Ditolak < θ)
    ("OOS-01", "Resep nasi goreng yang enak apa ya?", None),
    ("OOS-02", "Siapa presiden Indonesia sekarang?", None),
    ("OOS-03", "Cara install python dan docker di laptop windows", None),
    ("OOS-04", "Berapa harga tiket kereta api Madiun Surabaya?", None),
    ("OOS-05", "Rekomendasi tempat kos murah dekat jalan serayu", None),
    ("OOS-06", "asdfghjkl qwertyuiop", None),
]


def main() -> None:
    engine = rag_engine.initialize_rag_engine()
    print("=" * 100)
    print(f"KALIBRASI THRESHOLD MINI-RAG PNM ({len(engine['df'])} Entri FAQ Terindeks)")
    print("=" * 100)

    records: list[tuple[str, str, float, int, set[int] | None]] = []
    for label, query, expected_ids in BENCHMARK_QUERIES:
        refs = rag_engine.retrieve_faq(query, engine, top_k=3)
        top1_score = refs[0]["score"]
        top2_score = refs[1]["score"]
        top1_id = refs[0]["id"]
        records.append((label, query, top1_score, top1_id, expected_ids))

        if expected_ids is not None:
            hit_str = "✅ TEPAT" if top1_id in expected_ids else f"❌ MELESET (harapan {expected_ids})"
        else:
            hit_str = "🛡️ OOS"

        print(
            f"{label:9s} | Top1={top1_score:.4f} (Top2={top2_score:.4f}) | "
            f"ID=#{top1_id:02d} | {hit_str:12s} | {query}"
        )

    in_scope_scores = [r[2] for r in records if r[4] is not None]
    oos_scores = [r[2] for r in records if r[4] is None]

    min_in_scope = min(in_scope_scores)
    max_oos = max(oos_scores)

    print("-" * 100)
    print(f"Skor Terendah Kueri Akademik Valid (Min In-Scope) : {min_in_scope:.4f}")
    print(f"Skor Tertinggi Kueri Out-of-Scope  (Max OOS)      : {max_oos:.4f}")
    print(f"Margin Pemisah Aman (Gap)                         : {min_in_scope - max_oos:.4f}")
    print("-" * 100)

    print("\nEvaluasi Kandidat Threshold (θ):")
    for theta in (0.14, 0.16, 0.18, 0.20, 0.22):
        tp = sum(1 for r in records if r[4] is not None and r[2] >= theta and r[3] in r[4])
        fn = sum(1 for r in records if r[4] is not None and r[2] < theta)
        tn = sum(1 for r in records if r[4] is None and r[2] < theta)
        fp = sum(1 for r in records if r[4] is None and r[2] >= theta)
        total_in = len(in_scope_scores)
        total_oos = len(oos_scores)
        print(
            f"  θ = {theta:.2f} -> In-Scope Lolos & Tepat: {tp}/{total_in} (FN={fn}) | "
            f"OOS Ditolak Tepat: {tn}/{total_oos} (FP={fp})"
        )


if __name__ == "__main__":
    main()
