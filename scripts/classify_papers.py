#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from config_loader import load_editorial_malla
from logger_utils import log_line

@dataclass
class Tema:
    linea_key:str; linea_nombre:str; tema_id:str; producto_relacionado:str; titulo_base:str; keywords:list[str]; intencion:str; estado:str; prioridad:int

def normalize(t:str)->str: return ' '.join((t or '').lower().split())

def load_malla(path:Path)->list[Tema]:
    data=load_editorial_malla() if path.suffix!='.json' else json.loads(path.read_text())
    out=[]
    for k,ld in data.get('lineas_editoriales',{}).items():
        for t in ld.get('temas',[]):
            out.append(Tema(k,k.replace('_',' ').title(),t['id'],t['producto_relacionado'],t['titulo_base'],t.get('keywords',[]),t.get('intencion',''),t.get('estado','pendiente'),int(t.get('prioridad',3))))
    return out

def load_papers(path:Path)->list[dict[str,Any]]:
    if path.suffix=='.json': return json.loads(path.read_text(encoding='utf-8'))
    with path.open('r',encoding='utf-8',newline='') as h: return list(csv.DictReader(h))

def score(text:str,tema:Tema)->int:
    return sum(2 if normalize(k) in text else 1 if any(tok in text for tok in normalize(k).split() if len(tok)>3) else 0 for k in tema.keywords)

def fit_level(sc:int)->int: return 5 if sc>=8 else 4 if sc>=6 else 3 if sc>=4 else 2 if sc>=2 else 1

def quality_score(p:dict[str,Any], fit:int)->tuple[int,str,str]:
    q=1; reasons=[]
    lang=p.get('language','unknown')
    if lang=='en': q+=1; reasons.append('en')
    elif lang=='es': reasons.append('es penalizado')
    if p.get('doi_url') or p.get('url_fuente') or p.get('url'): q+=1; reasons.append('url/doi')
    if (p.get('abstract') or '').lower()!='abstract no disponible': q+=1; reasons.append('abstract')
    if p.get('source'): q+=1; reasons.append('fuente')
    if (p.get('year') or 0)>=2019: q+=1; reasons.append('reciente')
    if fit>=3: q+=1; reasons.append('ajuste malla')
    q=max(1,min(5,q))
    estado='Seleccionado' if q>=4 else 'Revisar' if q==3 else 'Archivo / baja prioridad' if q==2 else 'Descartar'
    return q, ', '.join(reasons), estado

def classify(p:dict[str,Any],temas:list[Tema])->dict[str,Any]:
    text=normalize(f"{p.get('title','')} {p.get('abstract','')} {' '.join(map(str,p.get('keywords',[])))}")
    ranked=sorted(((t,score(text,t)) for t in temas), key=lambda x:x[1], reverse=True)
    t,sc=ranked[0]; fit=fit_level(sc)
    q,mot,estado=quality_score(p,fit)
    rec='Usar para artículo de malla' if q>=3 else ('Archivo / baja prioridad' if q==2 else 'Descartar')
    return {'paper':p.get('title','Sin título'),'doi':p.get('doi','N/A'),'doi_normalizado':p.get('doi_normalizado',''),'doi_url':p.get('doi_url',''),'url_fuente':p.get('url_fuente',p.get('url','')),'openalex_url':p.get('openalex_url',''),'semantic_scholar_url':p.get('semantic_scholar_url',''),'language':p.get('language','unknown'),'marca_destino':'Marca personal Luis' if 'marca_personal' in t.linea_key else 'Líderes / Skillia','linea_editorial_sugerida':t.linea_nombre,'producto_relacionado':t.producto_relacionado,'id_tema':t.tema_id,'articulo_sugerido':t.titulo_base,'nivel_ajuste':fit,'justificacion':f"Coincidencia con {t.tema_id}",'quality_score':q,'motivo_calidad':mot,'estado_sugerido':estado,'recomendacion_uso':rec}

def gen_md(rows,out:Path):
    out.parent.mkdir(parents=True,exist_ok=True)
    L=['# Weekly paper to malla mapping','','| Paper | DOI | Idioma | DOI URL | URL fuente | Línea editorial sugerida | Producto relacionado | ID de tema | Título base | Ajuste | Quality | Motivo calidad | Estado sugerido | Justificación | Recomendación |','|---|---|---|---|---|---|---|---|---|---:|---:|---|---|---|---|']
    for r in rows:
        L.append(f"| {r['paper']} | {r['doi']} | {r['language']} | {r['doi_url']} | {r['url_fuente']} | {r['linea_editorial_sugerida']} | {r['producto_relacionado']} | {r['id_tema']} | {r['articulo_sugerido']} | {r['nivel_ajuste']} | {r['quality_score']} | {r['motivo_calidad']} | {r['estado_sugerido']} | {r['justificacion']} | {r['recomendacion_uso']} |")
    out.write_text('\n'.join(L)+'\n',encoding='utf-8')

def quality_report(rows):
    from collections import Counter
    Path('outputs/review').mkdir(parents=True,exist_ok=True)
    c=Counter(r.get('language','unknown') for r in rows)
    doi=sum(1 for r in rows if r.get('doi_url')); url=sum(1 for r in rows if r.get('url_fuente'))
    top=sorted(rows,key=lambda x:(x['quality_score'],x['nivel_ajuste']),reverse=True)[:10]
    disc=[r for r in rows if r['estado_sugerido'] in ('Descartar','Archivo / baja prioridad')]
    bytema={}
    for r in rows: bytema.setdefault(r['id_tema'],[]).append(r['quality_score'])
    strong=[k for k,v in bytema.items() if sum(v)/len(v)>=4]
    weak=[k for k,v in bytema.items() if sum(v)/len(v)<3]
    lines=['# Paper Quality Report','',f"- total de papers encontrados: {len(rows)}",f"- total en inglés: {c.get('en',0)}",f"- total en español: {c.get('es',0)}",f"- total sin idioma identificado: {c.get('unknown',0)}",f"- total con DOI funcional: {doi}",f"- total con URL fuente: {url}",'','## top 10 papers recomendados']
    lines += [f"- {t['paper']} (Q{t['quality_score']}, ajuste {t['nivel_ajuste']})" for t in top]
    lines += ['', '## papers descartados y razón']
    lines += [f"- {d['paper']}: {d['motivo_calidad']}" for d in disc[:30]]
    lines += ['', f"## temas de malla con mejor evidencia\n- {', '.join(strong) if strong else 'ninguno'}", f"\n## temas de malla con evidencia débil\n- {', '.join(weak) if weak else 'ninguno'}"]
    Path('outputs/review/paper_quality_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--papers',default='outputs/papers/weekly_papers.json'); ap.add_argument('--malla',default='config/editorial_malla.yaml'); ap.add_argument('--output-json',default='outputs/papers/weekly_paper_classification.json'); ap.add_argument('--output-md',default='outputs/papers/weekly_paper_to_malla_mapping.md'); ap.add_argument('--max-papers',type=int,default=20); ap.add_argument('--mock',action='store_true'); ap.add_argument('--dry-run',action='store_true'); a=ap.parse_args()
    mode='mock' if a.mock else 'real'; log_line('logs/classify_papers.log', f"mode={mode} dry_run={a.dry_run}")
    temas=load_malla(Path(a.malla)); rows=[classify(p,temas) for p in load_papers(Path(a.papers))]
    rows=sorted(rows,key=lambda x:(x['quality_score'],x['nivel_ajuste']),reverse=True)[:a.max_papers]
    Path(a.output_json).parent.mkdir(parents=True,exist_ok=True); Path(a.output_json).write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    gen_md(rows,Path(a.output_md)); quality_report(rows)
    log_line('logs/classify_papers.log', f"papers_classified={len(rows)} high={sum(1 for r in rows if r['quality_score']>=4)} medium={sum(1 for r in rows if r['quality_score']==3)} low={sum(1 for r in rows if r['quality_score']<=2)}")

if __name__=='__main__': main()
