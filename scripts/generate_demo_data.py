from __future__ import annotations

import csv
import math
import random
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "raw" / "demonstracao_territorial.csv"
TERRITORIES = ["Aurora", "Central", "Estação", "Horizonte", "Jardins", "Lago Norte", "Mercado", "Nova Esperança", "Parque Sul", "Pioneiros", "Ribeira", "Vila Verde"]


def generate(output: Path = OUTPUT, seed: int = 42) -> Path:
    random.seed(seed)
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for territory_index, territory in enumerate(TERRITORIES):
        population = 5500 + territory_index * 1250 + random.randint(-350, 350)
        service_base = 58 + (territory_index % 5) * 7
        for offset in range(24):
            year = 2024 + offset // 12
            month = offset % 12 + 1
            rain = max(8, 115 + 82 * math.sin((month - 1) / 12 * 2 * math.pi) + random.gauss(0, 22))
            temperature = 22.5 + 4.2 * math.sin((month - 2) / 12 * 2 * math.pi) + random.gauss(0, 1.2)
            coverage = min(98, max(38, service_base + random.gauss(0, 5)))
            calls = max(4, round(population / 520 + rain / 24 + (100 - coverage) / 5 + random.gauss(0, 4)))
            response_hours = max(2.5, 9 + calls * .72 + (100 - coverage) * .19 + random.gauss(0, 4))
            pressure = calls / (population / 1000) * .38 + response_hours / 24 * .34 + (100 - coverage) / 45 * .28
            # Limiares fixos produzem três faixas interpretáveis sem usar
            # quantis calculados a partir do próprio conjunto de avaliação.
            if pressure >= 2.05:
                level = "Alto"
            elif pressure >= 1.65:
                level = "Moderado"
            else:
                level = "Baixo"
            rows.append({
                "competencia": date(year, month, 1).isoformat(), "territorio": territory,
                "populacao_estimada": population, "chamados": calls,
                "tempo_medio_h": round(response_hours, 2), "chuva_mm": round(rain, 2),
                "temperatura_c": round(temperature, 2), "cobertura_servico_pct": round(coverage, 2),
                "nivel_pressao": level, "origem": "SINTETICO_DEMONSTRACAO",
            })
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return output


if __name__ == "__main__":
    print(generate())
