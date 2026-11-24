"""
Unit & Integration Tests untuk Mesin Mini-RAG (tests/test_rag_engine.py)
Menguji seluruh fungsi rag_engine.py secara terisolasi maupun terintegrasi
(termasuk simulasi mock DeepSeek API dan skenario Fallback Lokal).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pandas as pd

import rag_engine


class TestRagEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = rag_engine.initialize_rag_engine()

    def test_preprocess_text_edge_cases(self) -> None:
        self.assertEqual(rag_engine.preprocess_text(None), "")
        self.assertEqual(rag_engine.preprocess_text(float("nan")), "")
        self.assertEqual(rag_engine.preprocess_text(True), "")
        self.assertEqual(rag_engine.preprocess_text(["a", "b"]), "")
        self.assertEqual(rag_engine.preprocess_text({"k": "v"}), "")
        self.assertEqual(rag_engine.preprocess_text("   "), "")
        self.assertEqual(
            rag_engine.preprocess_text("Nilai D & IPK 3,50?!"),
            "nilai d ipk 3 50",
        )

    def test_load_faq_data_valid_schema(self) -> None:
        df = self.engine["df"]
        self.assertGreaterEqual(len(df), 28)
        for col in rag_engine.REQUIRED_COLUMNS + ["search_text"]:
            self.assertIn(col, df.columns)
        self.assertFalse(df["id"].duplicated().any())
        self.assertEqual(df["kategori"].nunique(), 5)

    def test_load_faq_data_validation_errors(self) -> None:
        with self.assertRaises(FileNotFoundError):
            rag_engine.load_faq_data("file_tidak_ada_12345.csv")

        with tempfile.TemporaryDirectory() as tmpdir:
            dup_csv = Path(tmpdir) / "dup.csv"
            pd.DataFrame(
                [
                    {
                        "id": 1,
                        "kategori": "A",
                        "pertanyaan": "Q1",
                        "jawaban": "A1",
                        "sumber_pasal": "P1",
                    },
                    {
                        "id": 1,
                        "kategori": "A",
                        "pertanyaan": "Q2",
                        "jawaban": "A2",
                        "sumber_pasal": "P2",
                    },
                ]
            ).to_csv(dup_csv, index=False)
            with self.assertRaises(ValueError):
                rag_engine.load_faq_data(dup_csv)

            float_csv = Path(tmpdir) / "float_id.csv"
            pd.DataFrame(
                [
                    {
                        "id": 1.5,
                        "kategori": "A",
                        "pertanyaan": "Q1",
                        "jawaban": "A1",
                        "sumber_pasal": "P1",
                    }
                ]
            ).to_csv(float_csv, index=False)
            with self.assertRaises(ValueError):
                rag_engine.load_faq_data(float_csv)

    def test_single_letter_grades_indexed_in_vocabulary(self) -> None:
        vocab = set(self.engine["vectorizer"].get_feature_names_out())
        for token in ("a", "ab", "b", "bc", "c", "d", "e", "nilai d", "nilai e"):
            self.assertIn(token, vocab, f"Token '{token}' wajib ada di vocabulary TF-IDF")

    def test_retrieve_faq_accuracy_on_pnm_pedoman(self) -> None:
        cases = [
            ("Berapa minimal kehadiran atau batas jam alpa ikut UAS?", {8}),
            ("Kalau sering bolos berapa jam kena SP 1 atau DO?", {8, 25}),
            ("Gimana cara hitung kompen kalau alpa?", {10}),
            ("Nilai D masih lulus semester nggak ya?", {18}),
            ("Tabel konversi nilai angka ke huruf A AB B BC C D E", {15}),
            ("Kalau cuti akademik atau dicutikan tetap bayar UKT gak?", {23}),
            ("Syarat IPK cumlaude pujian di PNM berapa?", {34}),
            ("Gelar lulusan D3 Teknologi Informasi PNM apa?", {35}),
            ("Kapan jadwal UTS dan UAS kalender akademik 2025/2026?", {4, 14}),
            # Uji toleransi typo & pertanyaan sangat singkat
            ("bagaimana cara regristrasi dan krs", {1}),
            ("syarat cuti", {22}),
            ("telat daftar ulng sanksinya apa", {2}),
            ("syarat cumlade ipk berapa", {34}),
        ]
        for query, expected_ids in cases:
            refs = rag_engine.retrieve_faq(query, self.engine, top_k=3)
            self.assertEqual(len(refs), 3)
            self.assertIn(
                refs[0]["id"],
                expected_ids,
                f"Kueri '{query}' menghasilkan Top-1 ID={refs[0]['id']} (skor={refs[0]['score']:.3f}), diharapkan salah satu dari {expected_ids}",
            )
            self.assertGreaterEqual(
                refs[0]["score"],
                0.18,
                f"Kueri valid '{query}' memiliki skor {refs[0]['score']:.3f} < 0.18",
            )

    def test_ask_academic_assistant_invalid_and_out_of_scope(self) -> None:
        # TC-04: Input kosong / karakter acak / hanya stopwords
        for invalid_q in ("", "   ", "???", "asdfghjkl", "apa ya sih"):
            res = rag_engine.ask_academic_assistant(invalid_q, self.engine, threshold=0.18)
            self.assertEqual(res["status"], "INVALID_INPUT", f"Gagal pada input: {invalid_q!r}")
            self.assertEqual(res["references"], [])

        # TC-03: Pertanyaan di luar cakupan pedoman akademik
        for oos_q in (
            "Resep nasi goreng yang enak apa ya?",
            "Cara install python di laptop windows",
            "Siapa presiden Indonesia sekarang?",
        ):
            res = rag_engine.ask_academic_assistant(oos_q, self.engine, threshold=0.18)
            self.assertEqual(res["status"], "OUT_OF_SCOPE", f"Gagal pada kueri OOS: {oos_q!r}")
            self.assertLess(res["max_score"], 0.18)

    @patch("rag_engine.OpenAI")
    @patch("rag_engine.get_api_key", return_value="sk-test-valid-key")
    def test_ask_academic_assistant_success_llm_mocked(
        self, _mock_key: MagicMock, mock_openai_cls: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="Berdasarkan Bab II Huruf G (Hal. 14), alpa >= 18 jam mendapat SP I."
                    )
                )
            ]
        )
        mock_openai_cls.return_value = mock_client

        res = rag_engine.ask_academic_assistant(
            "Berapa jam alpa kena SP 1?", self.engine, threshold=0.18
        )
        self.assertEqual(res["status"], "SUCCESS_LLM")
        self.assertIn("SP I", res["answer"])
        self.assertIsNone(res["error_detail"])
        self.assertEqual(len(res["references"]), 3)

    @patch("rag_engine.OpenAI", side_effect=RuntimeError("402 Insufficient Balance"))
    @patch("rag_engine.get_api_key", return_value="sk-test-expired-key")
    def test_ask_academic_assistant_fallback_on_api_error(
        self, _mock_key: MagicMock, _mock_openai_cls: MagicMock
    ) -> None:
        # TC-05: Simulasi kegagalan Cloud LLM API -> Fallback Lokal tanpa crash
        res = rag_engine.ask_academic_assistant(
            "Berapa jam alpa kena SP 1?", self.engine, threshold=0.18
        )
        self.assertEqual(res["status"], "FALLBACK_LOCAL")
        self.assertIn("Mode Fallback Lokal", res["answer"])
        self.assertIn("402 Insufficient Balance", res["error_detail"] or "")


if __name__ == "__main__":
    unittest.main()
