import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from atlas.pipeline import load_and_validate, run_pipeline
from atlas.web import create_app
from scripts.generate_demo_data import generate


class AtlasTest(unittest.TestCase):
    def test_pipeline_is_reproducible_and_beats_baseline(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            raw = generate(root / "demo.csv", seed=42)
            metrics = run_pipeline(raw, root / "artifacts")
            self.assertEqual(metrics["dataset"]["rows"], 288)
            self.assertEqual(metrics["dataset"]["split"]["train_rows"], 144)
            self.assertEqual(metrics["dataset"]["split"]["test_rows"], 144)
            self.assertGreater(metrics["model"]["accuracy"], metrics["model"]["baseline_accuracy"])
            self.assertGreater(metrics["model"]["macro_f1"], 0.70)
            self.assertTrue((root / "artifacts" / "predictions.csv").exists())

    def test_validation_rejects_undeclared_source(self):
        with tempfile.TemporaryDirectory() as folder:
            raw = generate(Path(folder) / "demo.csv")
            frame = pd.read_csv(raw)
            frame.loc[0, "origem"] = "FONTE_NAO_DOCUMENTADA"
            frame.to_csv(raw, index=False)
            with self.assertRaisesRegex(ValueError, "fonte demonstrativa"):
                load_and_validate(raw)

    def test_dashboard_and_api_use_artifacts(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            raw = generate(root / "demo.csv")
            artifacts = root / "artifacts"
            run_pipeline(raw, artifacts)
            client = create_app(artifacts).test_client()
            response = client.get("/")
            self.assertEqual(response.status_code, 200)
            self.assertIn("Dados não são", response.get_data(as_text=True))
            self.assertNotIn("style=", response.get_data(as_text=True))
            self.assertIn("<progress", response.get_data(as_text=True))
            api = client.get("/api/resumo")
            self.assertEqual(api.status_code, 200)
            self.assertEqual(len(json.loads(api.data)["territories"]), 12)
            self.assertIn("frame-ancestors", response.headers["Content-Security-Policy"])


if __name__ == "__main__":
    unittest.main()
