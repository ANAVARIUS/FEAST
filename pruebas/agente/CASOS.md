# Pruebas de agente - LLM as a Judge (STD 4.4)

Evaluacion **no determinista** del comportamiento del agente (DeepEval, golden dataset, metricas faithfulness / relevancy / tool correctness).

| ID | Para que sirve |
|----|----------------|
| CP-LLM-MENU-01 | No alucinar productos fuera del catalogo RAG. |
| CP-LLM-MENU-02 | Precios exactos segun contexto. |
| CP-LLM-MENU-03 | Tono y estilo (revision manual o criterio DeepEval). |
| CP-LLM-MENU-04 | Invocacion correcta de `get_menu` antes de hablar del menu. |
| CP-LLM-MENU-05 | Producto agotado + sugerencia alternativa. |
| CP-LLM-CART-01 / 02 | Carrito: extraccion y correcciones en dialogo. |
| CP-LLM-MSPEC-01 / 02 | Promociones vigentes y disponibilidad multi-item. |

**Nota:** Los tests automatizados con modelo real se omiten por defecto (coste y variabilidad). Para ejecutarlos, define `RUN_LLM_AGENT_TESTS=1` y configura las claves del STD (`.env.test`).
