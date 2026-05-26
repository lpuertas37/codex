# Configuración de Notion: base **Malla Editorial**

Si no hay integración API activa, crear manualmente la base de datos en Notion con nombre **Malla Editorial** y las siguientes propiedades:

1. **ID de tema** (Title)
2. **Línea editorial** (Select):
   - Marca personal Luis
   - Líderes / Skillia
   - Ambas
3. **Producto relacionado** (Select):
   - Clima laboral
   - Cultura organizacional
   - Riesgos psicosociales
   - Evaluación 360
   - Desempeño
   - People analytics
   - Liderazgo
   - Bienestar laboral
   - Psicometría aplicada
   - Inteligencia artificial en RRHH
   - Otro
4. **Título base** (Rich text)
5. **Keyword principal** (Rich text)
6. **Keywords secundarias** (Multi-select o Rich text)
7. **Intención del contenido** (Rich text)
8. **Formato principal** (Select):
   - Artículo SEO
   - Post LinkedIn
   - Newsletter
   - Infografía
   - Nota técnica
   - Resumen ejecutivo
9. **Estado** (Select):
   - Pendiente
   - En investigación
   - Con papers asignados
   - Borrador generado
   - En revisión
   - Publicado
   - Pausado
10. **Prioridad** (Number)
11. **Papers asignados** (Rich text)
12. **Paper principal** (Rich text)
13. **Resumen del enfoque** (Rich text)
14. **Fecha sugerida de publicación** (Date)
15. **URL del borrador** (URL)
16. **URL publicada** (URL)
17. **Notas de Luis** (Rich text)

## Carga sugerida

- Cargar filas base desde `config/editorial_malla.yaml`.
- Actualizar asignaciones usando `outputs/articles/notion_malla_editorial_payload.json` tras correr generación de borradores.
