#!/usr/bin/env python3
from __future__ import annotations
import os
from pathlib import Path


def _requests_or_error():
    try:
        import requests
        return requests
    except ModuleNotFoundError:
        raise SystemExit('Falta requests. Instala dependencias con pip install -r requirements.txt para usar este script.')


def notion_headers(token:str)->dict:
    return {
        'Authorization': f'Bearer {token}',
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json',
    }


def search_database_by_title(requests, token:str, title:str):
    url='https://api.notion.com/v1/search'
    payload={'query': title, 'filter': {'value':'database','property':'object'}, 'page_size': 20}
    r=requests.post(url,headers=notion_headers(token),json=payload,timeout=30)
    r.raise_for_status()
    for obj in r.json().get('results',[]):
        t=''.join(x.get('plain_text','') for x in obj.get('title',[])).strip()
        if t==title:
            return obj['id']
    return None


def create_database(requests, token:str, parent_page_id:str, title:str, properties:dict)->str:
    existing=search_database_by_title(requests, token, title)
    if existing:
        return existing
    payload={
        'parent': {'type':'page_id','page_id': parent_page_id},
        'title': [{'type':'text','text':{'content': title}}],
        'properties': properties,
    }
    r=requests.post('https://api.notion.com/v1/databases',headers=notion_headers(token),json=payload,timeout=30)
    r.raise_for_status()
    return r.json()['id']


def papers_properties()->dict:
    return {
      'Título': {'title': {}}, 'Autores': {'rich_text': {}}, 'Año': {'number': {'format':'number'}},
      'Revista / Fuente': {'rich_text': {}}, 'DOI': {'rich_text': {}}, 'URL': {'url': {}},
      'Abstract': {'rich_text': {}}, 'Keywords': {'rich_text': {}}, 'Tema principal': {'rich_text': {}},
      'Marca destino': {'select': {'options':[{'name':'Marca personal Luis'},{'name':'Líderes / Skillia'},{'name':'Ambas'}]}},
      'Producto relacionado': {'rich_text': {}}, 'ID de tema de malla': {'rich_text': {}}, 'Artículo sugerido': {'rich_text': {}},
      'Nivel de ajuste': {'number': {'format':'number'}}, 'Justificación del ajuste': {'rich_text': {}},
      'Relevancia 1-5': {'number': {'format':'number'}}, 'Aplicabilidad comercial 1-5': {'number': {'format':'number'}},
      'Potencial SEO 1-5': {'number': {'format':'number'}}, 'Potencial LinkedIn 1-5': {'number': {'format':'number'}},
      'Resumen ejecutivo': {'rich_text': {}}, 'Implicación práctica': {'rich_text': {}},
      'Estado': {'select': {'options':[{'name':'Pendiente'},{'name':'En investigación'},{'name':'Con papers asignados'},{'name':'Borrador generado'},{'name':'En revisión'},{'name':'Publicado'},{'name':'Pausado'}]}},
      'Fecha de búsqueda': {'date': {}}, 'Notas': {'rich_text': {}}, 'Título normalizado': {'rich_text': {}},
    }


def malla_properties()->dict:
    return {
      'ID de tema': {'title': {}}, 'Línea editorial': {'select': {'options':[{'name':'Marca personal Luis'},{'name':'Líderes / Skillia'},{'name':'Ambas'}]}},
      'Producto relacionado': {'select': {'options':[{'name':'Clima laboral'},{'name':'Cultura organizacional'},{'name':'Riesgos psicosociales'},{'name':'Evaluación 360'},{'name':'Desempeño'},{'name':'People analytics'},{'name':'Liderazgo'},{'name':'Bienestar laboral'},{'name':'Psicometría aplicada'},{'name':'Inteligencia artificial en RRHH'},{'name':'Otro'}]}},
      'Título base': {'rich_text': {}}, 'Keyword principal': {'rich_text': {}}, 'Keywords secundarias': {'rich_text': {}},
      'Intención del contenido': {'rich_text': {}},
      'Formato principal': {'select': {'options':[{'name':'Artículo SEO'},{'name':'Post LinkedIn'},{'name':'Newsletter'},{'name':'Infografía'},{'name':'Nota técnica'},{'name':'Resumen ejecutivo'}]}},
      'Estado': {'select': {'options':[{'name':'Pendiente'},{'name':'En investigación'},{'name':'Con papers asignados'},{'name':'Borrador generado'},{'name':'En revisión'},{'name':'Publicado'},{'name':'Pausado'}]}},
      'Prioridad': {'number': {'format':'number'}}, 'Papers asignados': {'rich_text': {}}, 'Paper principal': {'rich_text': {}},
      'Resumen del enfoque': {'rich_text': {}}, 'Fecha sugerida de publicación': {'date': {}}, 'URL del borrador': {'url': {}},
      'URL publicada': {'url': {}}, 'Notas': {'rich_text': {}},
    }


def main():
    token=os.getenv('NOTION_TOKEN')
    parent=os.getenv('NOTION_PARENT_PAGE_ID')
    if not token or not parent:
        raise SystemExit('Faltan NOTION_TOKEN o NOTION_PARENT_PAGE_ID en el entorno.')
    requests=_requests_or_error()
    papers_id=create_database(requests, token, parent, 'Papers', papers_properties())
    malla_id=create_database(requests, token, parent, 'Malla Editorial', malla_properties())
    Path('.env.generated').write_text(f'NOTION_PAPERS_DATABASE_ID={papers_id}\nNOTION_MALLA_DATABASE_ID={malla_id}\n',encoding='utf-8')
    print(f'NOTION_PAPERS_DATABASE_ID={papers_id}')
    print(f'NOTION_MALLA_DATABASE_ID={malla_id}')


if __name__=='__main__':
    main()
