# Pruebas de integracion (STD 4.3)

Flujo **LangGraph** + tools con **Redis opcional** y dependencias externas **mockeadas**.

| ID | Para que sirve |
|----|----------------|
| CP-INT-FLOW-01 | Intencion MENU: router -> `menu_specialist` -> `llm`, con menu simulado. |
| CP-INT-FLOW-02 | Menu vacio: respuesta final no inventa productos (mock catalogo vacio). |
| CP-INT-FLOW-03 | Intencion GENERAL: no pasa por `menu_specialist`. |
| CP-INT-FLOW-04 | Persistencia Redis checkpointer (requiere Redis o mock de checkpointer). |
| CP-INT-FLOW-05 | Timeout / reintentos del LLM (mock de excepcion). |
| CP-INT-FLOW-06 | Multi-turno mismo `thread_id` (mensajes acumulados). |

En esta carpeta, **FLOW-01 a 03 y 06** tienen automatizacion con `FakeLLM` y mock de `get_menu`. **FLOW-04/05** siguen en backlog o entorno dedicado; documenta fallos en `fallos.json` si el entorno real falla.
