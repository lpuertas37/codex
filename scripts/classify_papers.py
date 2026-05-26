#!/usr/bin/env python3
"""Clasifica papers contra la malla editorial maestra."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from logger_utils import log_line
from typing import Any



LOW_FIT_THRESHOLD = 2
HIGHLY_RELEVANT_THRESHOLD = 4


@dataclass
class Tema:
    linea_key: str
    linea_nombre: str
    tema_id: str
    producto_relacionado: str
    titulo_base: str
    keywords: list[str]
    intencion: str
    estado: str
    prioridad: int


def normalize(text: str) -> str:
    return " ".join(text.lower().split())


def load_malla(path: Path) -> list[Tema]:
    import json
    from config_loader import load_editorial_malla
    if path.name.endswith(".json"):
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = load_editorial_malla()
    lineas = data.get("lineas_editoriales", {})
    temas: list[Tema] = []
    for linea_key, linea_data in lineas.items():
        linea_nombre = linea_key.replace("_", " ").title()
        for tema in linea_data.get("temas", []):
            temas.append(
                Tema(
                    linea_key=linea_key,
                    linea_nombre=linea_nombre,
                    tema_id=tema["id"],
                    producto_relacionado=tema["producto_relacionado"],
                    titulo_base=tema["titulo_base"],
                    keywords=tema.get("keywords", []),
                    intencion=tema.get("intencion", ""),
                    estado=tema.get("estado", "pendiente"),
                    prioridad=int(tema.get("prioridad", 3)),
                )
            )
    return temas


def load_papers(path: Path) -> list[dict[str, Any]]:
    ext = path.suffix.lower()
    if ext == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    if ext == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    raise ValueError("Formato de papers no soportado. Usa JSON o CSV.")


def score_paper_against_tema(paper_text: str, tema: Tema) -> int:
    score = 0
    for kw in tema.keywords:
        kw_norm = normalize(kw)
        if kw_norm in paper_text:
            score += 2
        else:
            tokens = [t for t in kw_norm.split() if len(t) > 3]
            partial = sum(1 for t in tokens if t in paper_text)
            score += min(partial, 1)
    return score


def fit_level(score: int) -> int:
    if score >= 8:
        return 5
    if score >= 6:
        return 4
    if score >= 4:
        return 3
    if score >= 2:
        return 2
    return 1


def classify(paper: dict[str, Any], temas: list[Tema]) -> dict[str, Any]:
    title = paper.get("title", "Sin título")
    abstract = paper.get("abstract", "")
    text = normalize(f"{title} {abstract} {' '.join(map(str, paper.get('keywords', [])))}")

    scored = sorted(
        ((tema, score_paper_against_tema(text, tema)) for tema in temas),
        key=lambda x: x[1],
        reverse=True,
    )

    best_tema, best_score = scored[0]
    best_fit = fit_level(best_score)
    second_fit = fit_level(scored[1][1]) if len(scored) > 1 else 1

    recommendation = "Usar para artículo de malla"
    if best_fit <= LOW_FIT_THRESHOLD:
        recommendation = "Archivo / baja prioridad"
    elif second_fit >= 4:
        recommendation = "Paper transversal"

    return {
        "paper": title,
        "doi": paper.get("doi", "N/A"),
        "marca_destino": "Marca personal Luis" if "marca_personal" in best_tema.linea_key else "Líderes / Skillia",
        "linea_editorial_sugerida": best_tema.linea_nombre,
        "producto_relacionado": best_tema.producto_relacionado,
        "id_tema": best_tema.tema_id,
        "articulo_sugerido": best_tema.titulo_base,
        "nivel_ajuste": best_fit,
        "justificacion": (
            f"Coincidencia temática con {best_tema.tema_id} en producto '{best_tema.producto_relacionado}' "
            f"y keywords prioritarias."
        ),
        "recomendacion_uso": recommendation,
        "tema_estado": best_tema.estado,
        "idea_nueva_para_evaluar": recommendation == "Archivo / baja prioridad" and best_fit >= HIGHLY_RELEVANT_THRESHOLD,
    }


def generate_markdown(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Weekly paper to malla mapping",
        "",
        "| Paper | DOI | Línea editorial sugerida | Producto relacionado | ID de tema | Título base del artículo | Nivel de ajuste (1-5) | Justificación | Recomendación de uso |",
        "|---|---|---|---|---|---|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {paper} | {doi} | {linea_editorial_sugerida} | {producto_relacionado} | {id_tema} | {articulo_sugerido} | {nivel_ajuste} | {justificacion} | {recomendacion_uso} |".format(
                **row
            )
        )

    ideas = [r for r in rows if r.get("idea_nueva_para_evaluar")]
    lines.extend(["", "## Ideas nuevas para evaluar", ""])
    if ideas:
        for idea in ideas:
            lines.append(f"- **{idea['paper']}** ({idea['doi']}): {idea['justificacion']}")
    else:
        lines.append("- Sin ideas nuevas esta semana.")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--papers", default="outputs/papers/weekly_papers.json")
    parser.add_argument("--malla", default="config/editorial_malla.yaml")
    parser.add_argument("--output-json", default="outputs/papers/weekly_paper_classification.json")
    parser.add_argument("--output-md", default="outputs/papers/weekly_paper_to_malla_mapping.md")
    parser.add_argument('--mock', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    mode = "mock" if args.mock else "real"
    log_line("logs/classify_papers.log", f"mode={mode} dry_run={args.dry_run}")

    temas = load_malla(Path(args.malla))
    papers = load_papers(Path(args.papers))
    classified = [classify(p, temas) for p in papers]

    Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_json).write_text(
        json.dumps(classified, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    generate_markdown(classified, Path(args.output_md))
    high=sum(1 for x in classified if x['nivel_ajuste']>=4); med=sum(1 for x in classified if x['nivel_ajuste']==3); low=sum(1 for x in classified if x['nivel_ajuste']<=2)
    temas=sorted(set(x['id_tema'] for x in classified))
    log_line('logs/classify_papers.log', f'papers_classified={len(classified)} high={high} medium={med} low={low} temas={temas}')


if __name__ == "__main__":
    main()
