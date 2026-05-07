# Pruebas (STD / IEEE 829)

Estructura alineada al **Documento de Pruebas de Software (STD)** del proyecto FEAST: seccion 4 *Especificaciones de Casos de Prueba*.

## Carpetas

| Carpeta | Seccion STD | Contenido |
|---------|-------------|-----------|
| `estaticas/` | 4.1 | Analisis estatico (lint, tipos, McCabe, bandit, docstrings, scripts). |
| `unitarias/` | 4.2 | Componentes aislados con mocks (tools, router, estado). |
| `integracion/` | 4.3 | Flujo LangGraph + tools con dependencias simuladas. |
| `agente/` | 4.4 | LLM as a Judge / DeepEval (manual o con API; ver `CASOS.md`). |
| `caja_negra/` | 4.5 | Particiones de equivalencia y valores limite (reglas de dominio). |
| `modelos_probabilisticos/` | 4.6 | Red de Petri y teoria de colas (validacion conceptual / rutas). |

## Registro de fallos (solo fallos)

En **cada** subcarpeta hay:

- **`CASOS.md`**: tabla de referencia con ID del STD, nombre y **para que sirve** cada caso (no hace falta tocarla cuando todo pasa).
- **`fallos.json`**: lista JSON. **Solo debes anadir entradas cuando algo falle** (ejecucion manual, CI o pytest). Si la suite esta verde, el archivo permanece `[]`.

Formato sugerido para una entrada en `fallos.json`:

```json
{
  "id": "CP-UNIT-TOOL-01",
  "fecha": "2026-05-03T12:00:00Z",
  "que_falla": "Descripcion breve del sintoma o asercion.",
  "como_reproducir": "Comando o pasos (opcional)."
}
```

## Ejecutar pruebas dinamicas

Desde la raiz del repo (con dependencias instaladas):

```bash
pip install -r requirements.txt
pytest pruebas -q
```

`pruebas/conftest.py` define `URL_CONEXION` por defecto a SQLite en memoria si no existe en el entorno, para que la importacion de modelos SQLAlchemy no falle en maquinas sin `.env`.

Las pruebas automaticas priorizan **mocks** y rutas deterministas para reducir fallos intermitentes; las de agente con LLM real quedan documentadas en `agente/CASOS.md` y no se ejecutan salvo que definas `RUN_LLM_AGENT_TESTS=1`.
