#!/usr/bin/env python3
from __future__ import annotations
import argparse, subprocess, sys
from logger_utils import log_line

def run(cmd):
    print('>>',' '.join(cmd)); subprocess.run(cmd,check=True)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--mock',action='store_true'); ap.add_argument('--dry-run',action='store_true'); ap.add_argument('--days',type=int,default=30); ap.add_argument('--max-drafts',type=int,default=3); a=ap.parse_args()
    mode = "mock" if a.mock else "real"
    log_line("logs/pipeline.log", f"start mode={mode} dry_run={a.dry_run} max_drafts={a.max_drafts}")
    search=[sys.executable,'scripts/search_papers.py','--days',str(a.days)]
    if a.mock: search.append('--mock')
    run(search + (['--dry-run'] if a.dry_run else []))
    run([sys.executable,'scripts/classify_papers.py','--papers','data/clean_papers.json'] + (['--mock'] if a.mock else []) + (['--dry-run'] if a.dry_run else []))
    ns=[sys.executable,'scripts/notion_sync.py'] + (['--dry-run'] if a.dry_run else [])
    run(ns)
    run([sys.executable,'scripts/generate_article_drafts.py','--max-drafts',str(a.max_drafts)] + (['--mock'] if a.mock else []) + (['--dry-run'] if a.dry_run else []))
    log_line('logs/pipeline.log','completed')
    run(ns)

if __name__=='__main__': main()
