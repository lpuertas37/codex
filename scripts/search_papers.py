#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from config_loader import load_topics
from logger_utils import log_line


def clean_abs(v):
    if not v: return 'abstract no disponible'
    t=re.sub(r'<[^>]+>',' ',str(v))
    return ' '.join(t.split()) or 'abstract no disponible'


def _requests_or_error():
    try:
        import requests
        return requests
    except ModuleNotFoundError:
        raise SystemExit('Falta requests. Instala dependencias con pip install -r requirements.txt para usar búsqueda real o sincronización real.')


def crossref(q,fd):
    requests=_requests_or_error()
    r=requests.get('https://api.crossref.org/works',params={'query':q,'filter':f'from-pub-date:{fd}','rows':5},timeout=20); r.raise_for_status()
    out=[]
    for it in r.json().get('message',{}).get('items',[]):
        out.append({'title':(it.get('title') or ['Sin título'])[0],'authors':[f"{a.get('given','')} {a.get('family','')}".strip() for a in it.get('author',[])],'year':((it.get('published-print') or it.get('published-online') or {}).get('date-parts',[[None]])[0][0]),'source':(it.get('container-title') or [''])[0],'doi':it.get('DOI','N/A'),'url':it.get('URL',''),'abstract':clean_abs(it.get('abstract')),'keywords':it.get('subject',[]),'origin':'Crossref'})
    return out


def openalex(q,fd):
    requests=_requests_or_error()
    r=requests.get('https://api.openalex.org/works',params={'search':q,'filter':f'from_publication_date:{fd}','per-page':5},timeout=20); r.raise_for_status()
    out=[]
    for it in r.json().get('results',[]):
        inv=it.get('abstract_inverted_index') or {}
        if inv:
            seq=sorted([(i,w) for w,arr in inv.items() for i in arr],key=lambda x:x[0]); abs_txt=' '.join(w for _,w in seq)
        else: abs_txt='abstract no disponible'
        out.append({'title':it.get('title','Sin título'),'authors':[a.get('author',{}).get('display_name','') for a in it.get('authorships',[])],'year':it.get('publication_year'),'source':it.get('primary_location',{}).get('source',{}).get('display_name',''),'doi':(it.get('doi') or 'N/A').replace('https://doi.org/',''),'url':it.get('id',''),'abstract':clean_abs(abs_txt),'keywords':[c.get('display_name','') for c in it.get('concepts',[])[:6]],'origin':'OpenAlex'})
    return out


def dedup(rows):
    seen=set(); out=[]
    for p in rows:
        t=' '.join((p.get('title') or '').lower().split())
        k=((p.get('doi') or '').lower(),t)
        if k in seen: continue
        seen.add(k); out.append(p)
    return out


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--days',type=int,default=30); ap.add_argument('--mock',action='store_true'); ap.add_argument('--dry-run',action='store_true'); a=ap.parse_args()
    mode = "mock" if a.mock else "real"
    log_line("logs/search_papers.log", f"mode={mode} dry_run={a.dry_run}")
    Path('data').mkdir(exist_ok=True)
    if a.mock:
        rows=json.loads(Path('data/mock_papers.json').read_text(encoding='utf-8'))
        for r in rows: r['origin']='Mock'; r['abstract']=clean_abs(r.get('abstract'))
    else:
        fd=(datetime.now(timezone.utc)-timedelta(days=a.days)).date().isoformat(); rows=[]
        for q in load_topics()[:20]:
            try: rows.extend(crossref(q,fd))
            except Exception: pass
            try: rows.extend(openalex(q,fd))
            except Exception: pass
    Path('data/raw_papers.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    clean=dedup(rows)
    Path('data/clean_papers.json').write_text(json.dumps(clean,ensure_ascii=False,indent=2),encoding='utf-8')
    Path('outputs/papers').mkdir(parents=True,exist_ok=True)
    Path('outputs/papers/weekly_papers.json').write_text(json.dumps(clean,ensure_ascii=False,indent=2),encoding='utf-8')
    log_line('logs/search_papers.log', f'papers_found={len(rows)} papers_clean={len(clean)} fallback_malla_used=unknown')

if __name__=='__main__': main()
