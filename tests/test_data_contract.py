import hashlib
import random
import tempfile
import unittest
from pathlib import Path

import joblib
import pandas as pd

from atlas.pipeline import FEATURES, TARGET, load_and_validate, run_pipeline
from scripts.generate_demo_data import generate


class DataContractTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.raw = generate(self.root / "demo.csv")
        self.frame = pd.read_csv(self.raw)

    def write_change(self, column, value):
        frame = self.frame.copy()
        frame[column] = frame[column].astype(object)
        frame.loc[0, column] = value
        frame.to_csv(self.raw, index=False)

    def test_invalid_cells_are_rejected_before_any_artifact_is_written(self):
        cases = [
            ("populacao_estimada", "desconhecida", "somente números"),
            ("chamados", 1.5, "inteiros"),
            ("populacao_estimada", 100.5, "inteiros"),
            ("tempo_medio_h", "inf", "finitos"),
            ("chuva_mm", "-inf", "finitos"),
            ("temperatura_c", "inf", "finitos"),
            ("chamados", -1, "fora das faixas"),
            ("cobertura_servico_pct", 101, "entre 0 e 100"),
            ("territorio", "  ", "não vazio"),
            ("territorio", " Aurora", "extremidades"),
            ("competencia", "01/01/2024", "data ISO"),
            ("competencia", "2024-01-02", "primeiro dia"),
            ("competencia", "2026-01-01", "2024 e 2025"),
            ("nivel_pressao", "CRITICO", "desconhecido"),
            ("origem", "FONTE_REAL", "fonte demonstrativa"),
            ("tempo_medio_h", None, "valores ausentes"),
        ]
        for column, value, message in cases:
            with self.subTest(column=column, value=value):
                self.write_change(column, value)
                with self.assertRaisesRegex(ValueError, message):
                    run_pipeline(self.raw, self.root / "artifacts")
                self.assertFalse((self.root / "artifacts").exists())

    def test_boolean_column_is_not_an_integer_measure(self):
        frame = self.frame.copy()
        frame["chamados"] = True
        frame.to_csv(self.raw, index=False)
        with self.assertRaisesRegex(ValueError, "booleanos"):
            load_and_validate(self.raw)

    def test_duplicate_territory_month_is_rejected(self):
        pd.concat([self.frame, self.frame.iloc[[0]]], ignore_index=True).to_csv(self.raw, index=False)
        with self.assertRaisesRegex(ValueError, "observações duplicadas"):
            load_and_validate(self.raw)

    def test_duplicate_header_is_rejected_before_pandas_can_rename_it(self):
        lines = self.raw.read_text(encoding="utf-8").splitlines()
        lines[0] += ",territorio"
        for index in range(1, len(lines)):
            lines[index] += ",Aurora"
        self.raw.write_text("\n".join(lines) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "colunas duplicados"):
            load_and_validate(self.raw)

    def test_missing_column_and_empty_source_are_rejected(self):
        self.frame.drop(columns=["chamados"]).to_csv(self.raw, index=False)
        with self.assertRaisesRegex(ValueError, "Colunas obrigatórias"):
            load_and_validate(self.raw)
        self.raw.write_text("", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "vazia"):
            load_and_validate(self.raw)

    def test_missing_period_or_class_cannot_publish_metrics(self):
        cases = [
            (self.frame[self.frame["competencia"].str.startswith("2024")], "2024 para treino"),
            (self.frame[self.frame[TARGET] != "Alto"], "três classes"),
        ]
        for frame, message in cases:
            with self.subTest(message=message):
                frame.to_csv(self.raw, index=False)
                with self.assertRaisesRegex(ValueError, message):
                    run_pipeline(self.raw, self.root / "artifacts")
                self.assertFalse((self.root / "artifacts").exists())

    def test_generator_is_reproducible_without_changing_global_random_state(self):
        state = random.getstate()
        other = generate(self.root / "other.csv")
        self.assertEqual(random.getstate(), state)
        self.assertEqual(self.raw.read_bytes(), other.read_bytes())

    def test_metrics_predictions_and_saved_model_reproduce_the_same_input(self):
        first = self.root / "first"
        second = self.root / "second"
        metrics = run_pipeline(self.raw, first)
        self.assertEqual(metrics, run_pipeline(self.raw, second))
        for name in ["metrics.json", "territories.json", "predictions.csv"]:
            self.assertEqual((first / name).read_bytes(), (second / name).read_bytes())
        self.assertEqual(metrics["dataset"]["source_sha256"], hashlib.sha256(self.raw.read_bytes()).hexdigest())
        self.assertEqual(metrics["dataset"]["rows"], 288)
        split = metrics["dataset"]["split"]
        self.assertEqual(split["train_rows"] + split["test_rows"], metrics["dataset"]["rows"])
        for counts in metrics["reproducibility"]["class_counts"].values():
            self.assertEqual(sum(counts.values()), 144)
            self.assertTrue(all(count > 0 for count in counts.values()))
        frame = load_and_validate(self.raw)
        test = frame[frame["competencia"].dt.year == 2025]
        saved_model = joblib.load(first / "model.joblib")
        expected = pd.read_csv(first / "predictions.csv")["predicao"].tolist()
        self.assertEqual(saved_model.predict(test[FEATURES]).tolist(), expected)


if __name__ == "__main__":
    unittest.main()
