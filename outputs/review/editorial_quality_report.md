# Editorial Quality Report

## A. Resumen ejecutivo

- cuántos papers mock fueron procesados: 5
- cuántos fueron asignados a la malla: 5
- cuántos generaron borrador: 2
- si el resultado es coherente: Sí, pero restrictivo por estado + max-drafts + ajuste.

## B. Mapeo paper → tema

| título del paper | marca destino | producto relacionado | ID tema | nivel ajuste | justificación | decisión |
|---|---|---|---|---:|---|---|
| [MOCK] Workplace Climate and Team Performance | Líderes / Skillia | Clima laboral | LS-001 | 3 | Coincidencia temática con LS-001 en producto 'Clima laboral' y keywords prioritarias. | revisar |
| [MOCK] Organizational Culture Types in Hybrid Work | Líderes / Skillia | Cultura organizacional | LS-002 | 4 | Coincidencia temática con LS-002 en producto 'Cultura organizacional' y keywords prioritarias. | usar |
| [MOCK] Psychosocial Risk Signals and Burnout | Líderes / Skillia | Riesgos psicosociales | LS-007 | 4 | Coincidencia temática con LS-007 en producto 'Riesgos psicosociales' y keywords prioritarias. | usar |
| [MOCK] People Analytics for Retention Forecasting | Líderes / Skillia | Clima laboral | LS-001 | 2 | Coincidencia temática con LS-001 en producto 'Clima laboral' y keywords prioritarias. | descartar |
| [MOCK] Validity Evidence in Talent Assessment | Marca personal Luis | Psicometría aplicada | MP-001 | 4 | Coincidencia temática con MP-001 en producto 'Psicometría aplicada' y keywords prioritarias. | usar |

## C. Revisión de borradores

- título del archivo: `mp-001_cómo_usar_evidencia_de_validez_para_tomar_mejores_decisiones_de_talento.md`
  - evaluación de tono: adecuada base inicial
  - evaluación SEO: media
  - claridad empresarial: media
  - riesgo de tono académico: medio
  - recomendación: ajustar
- título del archivo: `ls-007_estrés_laboral__carga_mental_y_desgaste__señales_que_una_organización_no_debería_ignorar.md`
  - evaluación de tono: adecuada base inicial
  - evaluación SEO: media
  - claridad empresarial: media
  - riesgo de tono académico: medio
  - recomendación: ajustar

## D. Temas sin borrador
- LS-001, LS-002, LS-003, LS-004: estado publicado_o_borrador (regla actual no los genera).
- LS-005, LS-006: sin paper asignado con suficiente ajuste en esta corrida.

## E. Recomendaciones antes de conectar Notion real
- Ajustar criterio de selección de borradores y revisar `max-drafts`.
- Validar estructura de propiedades Notion con una base de staging primero.

## Mejora propuesta (no aplicada)
- Opción sugerida: generar borradores para temas con ajuste >=3 y permitir override `--force`.