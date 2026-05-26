#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from config_loader import load_topics
from logger_utils import log_line

PRIORITY_QUERIES = [
    "organizational climate","workplace climate","organizational culture","competing values framework",
    "psychosocial risks","workplace stress","burnout","mental health at work","employee engagement",
    "turnover intention","people analytics","leadership assessment","psychometrics","validity evidence",
    "performance management","360 feedback",
]


def normalize_doi(doi: str) -> str:
    if not doi: return ""
    d = str(doi).strip().lower()
    d = re.sub(r"^doi:\s*", "", d, flags=re.I)
    d = d.replace("https://doi.org/", "").replace("http://doi.org/", "")
    return d.strip()


def doi_url(doi: str) -> str:
    d = normalize_doi(doi)
    return f"https://doi.org/{d}" if d and "/" in d else ""


def detect_language(title: str, abstract: str, source_lang: str | None = None) -> str:
    if source_lang in ("en", "es"): return source_lang
    text = f"{title} {abstract}".lower()
    es_markers = [" de ", " y ", " en ", " organizacional", "laboral", "riesgos"]
    en_markers = [" the ", " and ", " workplace", "organizational", "employee", "burnout"]
    es = sum(1 for m in es_markers if m in text)
    en = sum(1 for m in en_markers if m in text)
    if en > es: return "en"
    if es > en: return "es"
    return "unknown"


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
    requests=_requests_or_error(); out=[]
    r=requests.get('https://api.crossref.org/works',params={'query':q,'filter':f'from-pub-date:{fd}','rows':8},timeout=20); r.raise_for_status()
    for it in r.json().get('message',{}).get('items',[]):
        doi=normalize_doi(it.get('DOI',''))
        out.append({'title':(it.get('title') or ['Sin título'])[0],'authors':[f"{a.get('given','')} {a.get('family','')}".strip() for a in it.get('author',[])],'year':((it.get('published-print') or it.get('published-online') or {}).get('date-parts',[[None]])[0][0]),'source':(it.get('container-title') or [''])[0],'doi':doi or 'N/A','doi_normalizado':doi,'doi_url':doi_url(doi),'url_fuente':it.get('URL',''),'openalex_url':'','semantic_scholar_url':'','url':it.get('URL',''),'abstract':clean_abs(it.get('abstract')),'keywords':it.get('subject',[]),'origin':'Crossref','language':detect_language((it.get('title') or [''])[0], clean_abs(it.get('abstract')), None),'publication_type':it.get('type','')})
    return out


def openalex(q,fd):
    requests=_requests_or_error(); out=[]
    r=requests.get('https://api.openalex.org/works',params={'search':q,'filter':f'from_publication_date:{fd}','per-page':8},timeout=20); r.raise_for_status()
    for it in r.json().get('results',[]):
        inv=it.get('abstract_inverted_index') or {}
        abs_txt=' '.join(w for _,w in sorted([(i,w) for w,arr in inv.items() for i in arr],key=lambda x:x[0])) if inv else 'abstract no disponible'
        doi=normalize_doi((it.get('doi') or '').replace('https://doi.org/',''))
        out.append({'title':it.get('title','Sin título'),'authors':[a.get('author',{}).get('display_name','') for a in it.get('authorships',[])],'year':it.get('publication_year'),'source':it.get('primary_location',{}).get('source',{}).get('display_name',''),'doi':doi or 'N/A','doi_normalizado':doi,'doi_url':doi_url(doi),'url_fuente':it.get('primary_location',{}).get('landing_page_url','') or it.get('id',''),'openalex_url':it.get('id',''),'semantic_scholar_url':'','url':it.get('id',''),'abstract':clean_abs(abs_txt),'keywords':[c.get('display_name','') for c in it.get('concepts',[])[:6]],'origin':'OpenAlex','language':detect_language(it.get('title',''), abs_txt, it.get('language')),'publication_type':it.get('type_crossref','')})
    return out


def semantic_scholar(q,fd):
    requests=_requests_or_error(); out=[]
    r=requests.get('https://api.semanticscholar.org/graph/v1/paper/search',params={'query':q,'limit':5,'fields':'title,abstract,year,authors,url,externalIds,publicationTypes,venue'},timeout=20)
    if r.status_code>=300: return out
    for it in r.json().get('data',[]):
        doi=normalize_doi((it.get('externalIds') or {}).get('DOI',''))
        out.append({'title':it.get('title','Sin título'),'authors':[a.get('name','') for a in it.get('authors',[])],'year':it.get('year'),'source':it.get('venue',''),'doi':doi or 'N/A','doi_normalizado':doi,'doi_url':doi_url(doi),'url_fuente':it.get('url',''),'openalex_url':'','semantic_scholar_url':it.get('url',''),'url':it.get('url',''),'abstract':clean_abs(it.get('abstract')),'keywords':[],'origin':'SemanticScholar','language':detect_language(it.get('title',''), it.get('abstract',''), None),'publication_type':','.join(it.get('publicationTypes') or [])})
    return out


def pubmed(q,fd):
    requests=_requests_or_error(); out=[]
    if not any(k in q.lower() for k in ['stress','burnout','mental health','psychosocial']): return out
    s=requests.get('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi',params={'db':'pubmed','term':q,'retmode':'json','retmax':5},timeout=20)
    ids=(s.json().get('esearchresult',{}) or {}).get('idlist',[])
    for pmid in ids:
        out.append({'title':f'PubMed PMID {pmid}','authors':[],'year':None,'source':'PubMed','doi':'N/A','doi_normalizado':'','doi_url':'','url_fuente':f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/','openalex_url':'','semantic_scholar_url':'','url':f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/','abstract':'abstract no disponible','keywords':[],'origin':'PubMed','language':'en','publication_type':'journal-article'})
    return out


def dedup(rows):
    seen=set(); out=[]
    for p in rows:
        t=' '.join((p.get('title') or '').lower().split())
        k=((p.get('doi_normalizado') or '').lower(),t)
        if k in seen: continue
        seen.add(k); out.append(p)
    return out


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--days',type=int,default=30); ap.add_argument('--mock',action='store_true'); ap.add_argument('--dry-run',action='store_true'); ap.add_argument('--max-papers',type=int,default=20); a=ap.parse_args()
    mode = "mock" if a.mock else "real"
    log_line("logs/search_papers.log", f"mode={mode} dry_run={a.dry_run} max_papers={a.max_papers}")
    Path('data').mkdir(exist_ok=True)
    if a.mock:
        rows=json.loads(Path('data/mock_papers.json').read_text(encoding='utf-8'))
        for r in rows:
            r['origin']='Mock'; r['abstract']=clean_abs(r.get('abstract')); doi=normalize_doi(r.get('doi','')); r['doi_normalizado']=doi; r['doi_url']=doi_url(doi); r['url_fuente']=r.get('url',''); r['openalex_url']=''; r['semantic_scholar_url']=''; r['language']=detect_language(r.get('title',''), r.get('abstract',''), None); r['publication_type']='mock'
    else:
        fd=(datetime.now(timezone.utc)-timedelta(days=a.days)).date().isoformat(); rows=[]
        queries = PRIORITY_QUERIES + load_topics()
        for q in list(dict.fromkeys(queries))[:30]:
            for fn in (crossref, openalex, semantic_scholar, pubmed):
                try: rows.extend(fn(q,fd))
                except Exception: pass
    Path('data/raw_papers.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    clean=dedup(rows)
    Path('data/clean_papers.json').write_text(json.dumps(clean,ensure_ascii=False,indent=2),encoding='utf-8')
    Path('outputs/papers').mkdir(parents=True,exist_ok=True)
    Path('outputs/papers/weekly_papers.json').write_text(json.dumps(clean[:a.max_papers],ensure_ascii=False,indent=2),encoding='utf-8')
    log_line('logs/search_papers.log', f'papers_found={len(rows)} papers_clean={len(clean)} papers_saved={min(len(clean),a.max_papers)}')

if __name__=='__main__': main()
