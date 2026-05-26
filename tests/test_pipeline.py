from pathlib import Path
import subprocess, sys


def test_fallback_malla_exists():
    assert Path('config/editorial_malla.fallback.json').exists()


def test_pipeline_mock_dry_run_executes():
    rc=subprocess.run([sys.executable,'scripts/run_weekly_pipeline.py','--mock','--dry-run'],check=False)
    assert rc.returncode==0


def test_notion_dry_run_executes_and_report():
    rc=subprocess.run([sys.executable,'scripts/notion_sync.py','--dry-run'],check=False)
    assert rc.returncode==0
    assert Path('outputs/notion/notion_sync_report.md').exists()


def test_classification_output_generated():
    subprocess.run([sys.executable,'scripts/run_weekly_pipeline.py','--mock','--dry-run'],check=False)
    assert Path('outputs/papers/weekly_paper_classification.json').exists()
