from scripts.create_notion_databases import papers_properties, malla_properties


def test_papers_schema_keys():
    p=papers_properties()
    assert 'Título' in p and 'DOI' in p and 'Título normalizado' in p


def test_malla_schema_keys():
    m=malla_properties()
    assert 'ID de tema' in m and 'Título base' in m and 'Estado' in m
