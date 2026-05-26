#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, re
from pathlib import Path
from config_loader import load_editorial_malla
from logger_utils import log_line

NOTION_VERSION='2022-06-28'
PAPERS_PROPS=['Título','Autores','Año','Revista / Fuente','DOI','DOI normalizado','DOI URL','URL','URL fuente','OpenAlex URL','Semantic Scholar URL','Abstract','Keywords','Idioma','Tema principal','Marca destino','Producto relacionado','ID de tema de malla','Artículo sugerido','Nivel de ajuste','Quality Score','Motivo de calidad','Estado sugerido','Justificación del ajuste','Relevancia 1-5','Aplicabilidad comercial 1-5','Potencial SEO 1-5','Potencial LinkedIn 1-5','Resumen ejecutivo','Implicación práctica','Estado','Fecha de búsqueda','Notas','Título normalizado']
MALLA_PROPS=['ID de tema','Línea editorial','Producto relacionado','Título base','Keyword principal','Keywords secundarias','Intención del contenido','Formato principal','Estado','Prioridad','Papers asignados','Paper principal','Resumen del enfoque','Fecha sugerida de publicación','URL del borrador','URL publicada','Notas']




def map_estado_malla(estado:str)->str:
    e=(estado or '').strip().lower()
    if e in ('pendiente','en investigación','en investigacion','con papers asignados','borrador generado','en revisión','en revision','publicado','pausado'):
        return e.replace('investigacion','investigación').replace('revision','revisión').title()
    if e=='publicado_o_borrador':
        return 'Publicado'
    return 'Pendiente'

def normalize_title(title:str)->str:
    t=(title or '').lower(); t=re.sub(r'^\s*\[mock\]\s*','',t); t=re.sub(r'[^\w\s]',' ',t)
    return ' '.join(t.split())

def _requests_or_error():
    try:
        import requests
        return requests
    except ModuleNotFoundError:
        raise SystemExit('Falta requests. Instala dependencias con pip install -r requirements.txt para usar búsqueda real o sincronización real.')

def notion_request(method,url,token,payload=None):
    requests=_requests_or_error()
    return requests.request(method,url,headers={'Authorization':f'Bearer {token}','Notion-Version':NOTION_VERSION,'Content-Type':'application/json'},json=payload,timeout=25)

def get_db_schema(token,db_id):
    r=notion_request('GET',f'https://api.notion.com/v1/databases/{db_id}',token)
    if r.status_code>=300: return {}, f'{r.status_code} {r.text[:200]}'
    return r.json().get('properties',{}), None

def validate_schema(token,papers_db,malla_db):
    miss=[]; errs=[]
    p_props,e1=get_db_schema(token,papers_db); m_props,e2=get_db_schema(token,malla_db)
    if e1: errs.append(f'papers_db:{e1}')
    if e2: errs.append(f'malla_db:{e2}')
    for n in PAPERS_PROPS:
        if n not in p_props: miss.append(f'Papers::{n}')
    for n in MALLA_PROPS:
        if n not in m_props: miss.append(f'Malla::{n}')
    Path('outputs/notion').mkdir(parents=True,exist_ok=True)
    Path('outputs/notion/notion_schema_validation_report.md').write_text('# Notion Schema Validation\n\n## Missing\n'+('\n'.join(f'- {m}' for m in miss) if miss else '- Ninguna')+'\n\n## Errors\n'+('\n'.join(f'- {e}' for e in errs) if errs else '- Sin errores')+'\n',encoding='utf-8')
    return p_props,m_props,miss,errs

def query_first(token,db_id,flt):
    r=notion_request('POST',f'https://api.notion.com/v1/databases/{db_id}/query',token,{'filter':flt,'page_size':1})
    if r.status_code>=300: return None
    rs=r.json().get('results',[])
    return rs[0] if rs else None

def sanitize_props(props, allowed, missing):
    out={}
    for k,v in props.items():
        if k in allowed: out[k]=v
        else: missing.append(k)
    return out

def upsert(token,db_id,props,uid_prop=None,uid_val=None,title_norm=None):
    page=None
    if uid_prop and uid_val and uid_prop=='DOI':
        page=query_first(token,db_id,{'property':'DOI','rich_text':{'equals':str(uid_val)}})
    elif uid_prop and uid_val:
        page=query_first(token,db_id,{'property':uid_prop,'title':{'equals':str(uid_val)}})
    if (not page) and title_norm:
        page=query_first(token,db_id,{'property':'Título normalizado','rich_text':{'equals':title_norm}})
    if page:
        r=notion_request('PATCH',f"https://api.notion.com/v1/pages/{page['id']}",token,{'properties':props}); return 'updated' if r.status_code<300 else 'skipped'
    r=notion_request('POST','https://api.notion.com/v1/pages',token,{'parent':{'database_id':db_id},'properties':props}); return 'created' if r.status_code<300 else 'skipped'

def write_report(rep):
    Path('outputs/notion').mkdir(parents=True,exist_ok=True)
    Path('outputs/notion/notion_sync_report.md').write_text(
f"# Notion Sync Report\n\n- papers creados: {rep['papers_created']}\n- papers actualizados: {rep['papers_updated']}\n- malla creados: {rep['malla_created']}\n- malla actualizados: {rep['malla_updated']}\n- registros omitidos: {rep['skipped']}\n\n## propiedades faltantes\n" + ('\n'.join(f'- {x}' for x in sorted(set(rep['missing']))) if rep['missing'] else '- ninguna') + "\n\n## errores\n" + ('\n'.join(f'- {x}' for x in rep['errors']) if rep['errors'] else '- sin errores') + "\n\n## recomendación final\n- Si no hay faltantes críticos, proceder con sync real en mock.\n",encoding='utf-8')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--dry-run',action='store_true'); ap.add_argument('--validate-schema',action='store_true'); a=ap.parse_args()
    rep={'papers_created':0,'papers_updated':0,'malla_created':0,'malla_updated':0,'skipped':0,'missing':[],'errors':[]}
    token=os.getenv('NOTION_TOKEN'); p_db=os.getenv('NOTION_PAPERS_DATABASE_ID'); m_db=os.getenv('NOTION_MALLA_DATABASE_ID')
    log_line('logs/notion_sync.log', f'dry_run={a.dry_run} validate_schema={a.validate_schema}')
    if a.dry_run and not (token and p_db and m_db):
        write_report(rep); return
    if not token or not p_db or not m_db:
        rep['errors'].append('Notion env vars missing; skipping sync safely.'); write_report(rep); return
    p_schema,m_schema,miss,errs=validate_schema(token,p_db,m_db)
    rep['missing'].extend(miss); rep['errors'].extend(errs)
    if a.validate_schema:
        write_report(rep); return
    p_allowed=set(p_schema.keys()); m_allowed=set(m_schema.keys())
    malla=load_editorial_malla()
    for line,ld in malla.get('lineas_editoriales',{}).items():
        for t in ld.get('temas',[]):
            keywords=t.get('keywords',[])
            props=sanitize_props({
                'ID de tema':{'title':[{'text':{'content':t['id']}}]},
                'Línea editorial':{'select':{'name':'Marca personal Luis' if 'marca_personal' in line else 'Líderes / Skillia'}},
                'Producto relacionado':{'select':{'name':t.get('producto_relacionado','Otro')}},
                'Título base':{'rich_text':[{'text':{'content':t.get('titulo_base','')}}]},
                'Keyword principal':{'rich_text':[{'text':{'content':(keywords[0] if keywords else '')}}]},
                'Keywords secundarias':{'rich_text':[{'text':{'content':', '.join(keywords[1:])}}]},
                'Intención del contenido':{'rich_text':[{'text':{'content':t.get('intencion','')}}]},
                'Formato principal':{'select':{'name':(ld.get('formatos') or ['Artículo SEO'])[0].replace('Nota técnica breve','Nota técnica')}},
                'Estado':{'select':{'name':map_estado_malla(t.get('estado','pendiente'))}},
                'Prioridad':{'number':int(t.get('prioridad',3))},
                'Papers asignados':{'rich_text':[{'text':{'content':''}}]},
                'Paper principal':{'rich_text':[{'text':{'content':''}}]},
                'Resumen del enfoque':{'rich_text':[{'text':{'content':t.get('titulo_base','')}}]},
                'Notas':{'rich_text':[{'text':{'content':''}}]}
            },m_allowed,rep['missing'])
            if a.dry_run: rep['skipped']+=1; continue
            r=upsert(token,m_db,props,'ID de tema',t['id']); rep['malla_created']+= (r=='created'); rep['malla_updated']+=(r=='updated'); rep['skipped']+=(r=='skipped')
    cls_path=Path('outputs/papers/weekly_paper_classification.json')
    raw=json.loads(cls_path.read_text(encoding='utf-8')) if cls_path.exists() else []
    for c in raw:
        norm=normalize_title(c.get('paper',''))
        props=sanitize_props({'Título':{'title':[{'text':{'content':c.get('paper','Sin título')}}]},'Título normalizado':{'rich_text':[{'text':{'content':norm}}]},'DOI':{'rich_text':[{'text':{'content':c.get('doi','N/A')}}]},'DOI normalizado':{'rich_text':[{'text':{'content':c.get('doi_normalizado','')}}]},'DOI URL':{'url':c.get('doi_url','') or None},'URL fuente':{'url':c.get('url_fuente','') or None},'OpenAlex URL':{'url':c.get('openalex_url','') or None},'Semantic Scholar URL':{'url':c.get('semantic_scholar_url','') or None},'Idioma':{'select':{'name':c.get('language','unknown')}},'Tema principal':{'rich_text':[{'text':{'content':c.get('linea_editorial_sugerida','')}}]},'Marca destino':{'select':{'name':c.get('marca_destino','Líderes / Skillia')}},'Producto relacionado':{'rich_text':[{'text':{'content':c.get('producto_relacionado','')}}]},'ID de tema de malla':{'rich_text':[{'text':{'content':c.get('id_tema','')}}]},'Artículo sugerido':{'rich_text':[{'text':{'content':c.get('articulo_sugerido','')}}]},'Nivel de ajuste':{'number':c.get('nivel_ajuste',0)},'Quality Score':{'number':c.get('quality_score',0)},'Motivo de calidad':{'rich_text':[{'text':{'content':c.get('motivo_calidad','')}}]},'Estado sugerido':{'select':{'name':c.get('estado_sugerido','Revisar')}},'Justificación del ajuste':{'rich_text':[{'text':{'content':c.get('justificacion','')}}]},'Estado':{'select':{'name':'En investigación'}}},p_allowed,rep['missing'])
        if a.dry_run: rep['skipped']+=1; continue
        doi=c.get('doi') if c.get('doi') not in ('',None,'N/A') else None
        r=upsert(token,p_db,props,'DOI',doi,title_norm=norm); rep['papers_created']+=(r=='created'); rep['papers_updated']+=(r=='updated'); rep['skipped']+=(r=='skipped')
    write_report(rep)

if __name__=='__main__': main()
