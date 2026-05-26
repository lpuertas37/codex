#!/usr/bin/env python3
"""Genera borradores de artículos SOLO para temas en malla editorial."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from logger_utils import log_line
from typing import Any


ALLOWED_ESTADOS = {"pendiente", "en investigación"}


def load_yaml(path: Path) -> dict[str, Any]:
    from config_loader import load_editorial_malla
    if path.name.endswith(".json"):
        return json.loads(path.read_text(encoding="utf-8"))
    return load_editorial_malla()


def load_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def sanitize_filename(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value.lower())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--malla", default="config/editorial_malla.yaml")
    parser.add_argument("--classification", default="outputs/papers/weekly_paper_classification.json")
    parser.add_argument("--output-dir", default="outputs/articles")
    parser.add_argument("--notion-output", default="outputs/articles/notion_malla_editorial_payload.json")
    parser.add_argument('--max-drafts', type=int, default=3)
    parser.add_argument('--mock', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    log_line('logs/generate_article_drafts.log', f'mode={'mock' if args.mock else 'real'} dry_run={args.dry_run} max_drafts={args.max_drafts}')

    malla = load_yaml(Path(args.malla))
    classified = load_json(Path(args.classification))

    temas_by_id = {}
    for linea_key, linea_data in malla.get("lineas_editoriales", {}).items():
        for tema in linea_data.get("temas", []):
            temas_by_id[tema["id"]] = {
                **tema,
                "linea": linea_key,
                "formatos": linea_data.get("formatos", []),
            }

    papers_by_tema = defaultdict(list)
    for p in classified:
        papers_by_tema[p["id_tema"]].append(p)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    notion_rows = []
    generated=0
    for tema_id, tema in temas_by_id.items():
        if generated>=args.max_drafts: break
        if tema.get("estado", "").lower() not in ALLOWED_ESTADOS:
            continue

        papers = papers_by_tema.get(tema_id, [])
        if not papers:
            continue

        transversales = [p for p in papers if p.get("recomendacion_uso") == "Paper transversal"]
        principales = [p for p in papers if p.get("recomendacion_uso") != "Archivo / baja prioridad"]

        draft = [
            f"# {tema['titulo_base']}",
            "",
            f"- ID de tema: {tema_id}",
            f"- Producto relacionado: {tema['producto_relacionado']}",
            f"- Intención: {tema.get('intencion', '')}",
            f"- Formato sugerido: {tema.get('formatos', ['Artículo SEO'])[0] if tema.get('formatos') else 'Artículo SEO'}",
            "",
            "## Papers base asignados",
        ]
        for p in principales:
            draft.append(f"- {p['paper']} ({p['doi']}) - ajuste {p['nivel_ajuste']}/5")

        draft.extend(["", "## Paper transversal", ""])
        if transversales:
            for p in transversales:
                draft.append(f"- {p['paper']} ({p['doi']})")
        else:
            draft.append("- Ninguno")

        draft.extend(
            [
                "",
                "## Borrador",
                "",
                "[Pendiente de redacción asistida con evidencia de los papers asignados.]",
            ]
        )

        file_name = f"{sanitize_filename(tema_id)}_{sanitize_filename(tema['titulo_base'])}.md"
        (out_dir / file_name).write_text("\n".join(draft) + "\n", encoding="utf-8")

        generated += 1
        notion_rows.append(
            {
                "ID de tema": tema_id,
                "Estado": "Con papers asignados",
                "Papers asignados": [f"{p['paper']} ({p['doi']})" for p in principales],
                "Paper principal": principales[0]["paper"] if principales else "",
                "Resumen del enfoque": tema["titulo_base"],
                "URL del borrador": str((out_dir / file_name).as_posix()),
            }
        )

    Path(args.notion_output).parent.mkdir(parents=True, exist_ok=True)
    log_line('logs/generate_article_drafts.log', f'borradores_generados={generated}')
    Path(args.notion_output).write_text(
        json.dumps(
            {
                "database_name": "Malla Editorial",
                "note": "Payload de sincronización para Notion (si está configurada integración API).",
                "rows": notion_rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
