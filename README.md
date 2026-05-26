# codex

## Instalación
```bash
pip install -r requirements.txt
```

## Ejecutar tests
```bash
pytest -q
```

## Configurar Notion (2 bases)
1. Crear base **Papers** y base **Malla Editorial**.
2. Compartir ambas bases con la integración de Notion.
3. Copiar los IDs y configurar variables.

## Variables de entorno
Copiar `.env.example` y completar:
- `NOTION_TOKEN`
- `NOTION_PAPERS_DATABASE_ID`
- `NOTION_MALLA_DATABASE_ID`

## Recomendado primer paso (sin tocar Notion)
```bash
python scripts/run_weekly_pipeline.py --mock --dry-run
```

## Pipeline mock
```bash
python scripts/run_weekly_pipeline.py --mock
```

## Pipeline real
```bash
python scripts/run_weekly_pipeline.py --days 30
```

## Dry-run solo sincronización Notion
```bash
python scripts/notion_sync.py --dry-run
```

## Upsert y deduplicación
- Papers: upsert por DOI; si no hay DOI, por `Título normalizado`.
- Malla: upsert por `ID de tema`.
- Evita duplicados al actualizar registros existentes.

## Revisar outputs
- `data/raw_papers.json`
- `data/clean_papers.json`
- `outputs/papers/weekly_paper_classification.json`
- `outputs/papers/weekly_paper_to_malla_mapping.md`
- `outputs/articles/*.md`
- `outputs/notion/notion_sync_report.md`

## Validación mínima sin internet
Si `pip install -r requirements.txt` falla por restricciones de red, igual puedes validar el flujo básico con:

```bash
python scripts/run_weekly_pipeline.py --mock --dry-run
```

Este modo:
- no llama APIs externas,
- no sincroniza realmente Notion,
- usa `data/mock_papers.json`,
- usa `config/editorial_malla.fallback.json` si `pyyaml` no está instalado.

## Primera conexión real con Notion
1. Crear una integración interna en Notion.
2. Compartir las dos bases (Papers y Malla Editorial) con la integración.
3. Copiar `database_id` de ambas bases.
4. Configurar `.env` con `NOTION_TOKEN`, `NOTION_PAPERS_DATABASE_ID`, `NOTION_MALLA_DATABASE_ID`.
5. Validar esquema sin escribir datos:
   - `python scripts/notion_sync.py --validate-schema`
6. Ejecutar validación local segura:
   - `python scripts/run_weekly_pipeline.py --mock --dry-run`
7. Ejecutar mock con sync real:
   - `python scripts/run_weekly_pipeline.py --mock`
8. Verificar no duplicados re-ejecutando el comando anterior y revisando `outputs/notion/notion_sync_report.md` (debe subir "actualizados", no "creados" para los mismos registros).


## Crear bases automáticamente (Notion)
Con `NOTION_TOKEN` y `NOTION_PARENT_PAGE_ID` configurados:

```bash
python scripts/create_notion_databases.py
```

El script crea (o reutiliza) las bases **Papers** y **Malla Editorial** sin duplicarlas, y genera `.env.generated` con:
- `NOTION_PAPERS_DATABASE_ID`
- `NOTION_MALLA_DATABASE_ID`
