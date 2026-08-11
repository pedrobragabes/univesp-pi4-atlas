from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "demonstracao_territorial.csv"
ARTIFACTS = ROOT / "artifacts"
FEATURES = ["territorio", "mes", "populacao_estimada", "chamados", "tempo_medio_h", "chuva_mm", "temperatura_c", "cobertura_servico_pct"]
TARGET = "nivel_pressao"
REQUIRED = {"competencia", "territorio", "populacao_estimada", "chamados", "tempo_medio_h", "chuva_mm", "temperatura_c", "cobertura_servico_pct", TARGET, "origem"}


def load_and_validate(path: Path = RAW_PATH) -> pd.DataFrame:
    frame = pd.read_csv(path)
    missing = REQUIRED - set(frame.columns)
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {sorted(missing)}")
    if frame.empty or frame[list(REQUIRED)].isna().any().any():
        raise ValueError("A fonte está vazia ou contém valores ausentes.")
    if set(frame["origem"]) != {"SINTETICO_DEMONSTRACAO"}:
        raise ValueError("A versão inicial aceita somente a fonte demonstrativa declarada.")
    if not frame["cobertura_servico_pct"].between(0, 100).all():
        raise ValueError("Cobertura de serviço deve estar entre 0 e 100.")
    if not frame["temperatura_c"].between(-20, 60).all() or (frame[["populacao_estimada", "chamados", "tempo_medio_h", "chuva_mm"]] < 0).any().any():
        raise ValueError("Há valores numéricos fora das faixas aceitas.")
    if not set(frame[TARGET]).issubset({"Baixo", "Moderado", "Alto"}):
        raise ValueError("Nível de pressão desconhecido.")
    frame["competencia"] = pd.to_datetime(frame["competencia"], errors="raise")
    frame["mes"] = frame["competencia"].dt.month
    return frame


def build_model() -> Pipeline:
    numeric = [column for column in FEATURES if column not in {"territorio"}]
    preprocessor = ColumnTransformer([
        ("territorio", OneHotEncoder(handle_unknown="ignore"), ["territorio"]),
        ("numericas", "passthrough", numeric),
    ])
    return Pipeline([
        ("preprocess", preprocessor),
        ("model", RandomForestClassifier(n_estimators=160, max_depth=9, min_samples_leaf=2, random_state=42, class_weight="balanced")),
    ])


def run_pipeline(raw_path: Path = RAW_PATH, artifacts: Path = ARTIFACTS) -> dict:
    frame = load_and_validate(raw_path)
    # A separação temporal evita que observações futuras participem do treino.
    train = frame[frame["competencia"].dt.year == 2024].copy()
    test = frame[frame["competencia"].dt.year == 2025].copy()
    if train.empty or test.empty:
        raise ValueError("O conjunto deve conter dados de 2024 para treino e de 2025 para teste.")
    expected_levels = {"Baixo", "Moderado", "Alto"}
    if set(train[TARGET]) != expected_levels or set(test[TARGET]) != expected_levels:
        raise ValueError("Treino e teste devem conter as três classes de pressão.")
    model = build_model()
    baseline = DummyClassifier(strategy="most_frequent")
    model.fit(train[FEATURES], train[TARGET])
    baseline.fit(train[FEATURES], train[TARGET])
    prediction = model.predict(test[FEATURES])
    baseline_prediction = baseline.predict(test[FEATURES])

    labels = ["Baixo", "Moderado", "Alto"]
    metrics = {
        "dataset": {
            "rows": len(frame), "territories": int(frame["territorio"].nunique()),
            "source": "SINTETICO_DEMONSTRACAO", "generated_for": "validacao_tecnica",
            "split": {"train": "2024", "test": "2025", "train_rows": len(train), "test_rows": len(test)},
        },
        "model": {
            "name": "RandomForestClassifier", "accuracy": round(float(accuracy_score(test[TARGET], prediction)), 4),
            "macro_f1": round(float(f1_score(test[TARGET], prediction, average="macro")), 4),
            "baseline_accuracy": round(float(accuracy_score(test[TARGET], baseline_prediction)), 4),
            "labels": labels, "confusion_matrix": confusion_matrix(test[TARGET], prediction, labels=labels).tolist(),
            "classification_report": classification_report(test[TARGET], prediction, labels=labels, output_dict=True, zero_division=0),
        },
        "warning": "Resultados demonstrativos não descrevem territórios reais nem sustentam decisão pública.",
    }

    test_output = test[["competencia", "territorio", TARGET]].copy()
    test_output["predicao"] = prediction
    test_output["confianca"] = model.predict_proba(test[FEATURES]).max(axis=1).round(4)
    territory = frame.groupby("territorio", as_index=False).agg(
        observacoes=("territorio", "size"), chamados_medios=("chamados", "mean"),
        resposta_media_h=("tempo_medio_h", "mean"), cobertura_media_pct=("cobertura_servico_pct", "mean"),
    )
    high_share = frame.assign(alto=frame[TARGET].eq("Alto")).groupby("territorio")["alto"].mean().mul(100)
    territory["pressao_alta_pct"] = territory["territorio"].map(high_share)
    for column in ["chamados_medios", "resposta_media_h", "cobertura_media_pct", "pressao_alta_pct"]:
        territory[column] = territory[column].round(2)

    artifacts.mkdir(parents=True, exist_ok=True)
    (artifacts / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    territory.sort_values("pressao_alta_pct", ascending=False).to_json(artifacts / "territories.json", orient="records", force_ascii=False, indent=2)
    test_output.to_csv(artifacts / "predictions.csv", index=False)
    joblib.dump(model, artifacts / "model.joblib")
    return metrics


if __name__ == "__main__":
    print(json.dumps(run_pipeline(), ensure_ascii=False, indent=2))
