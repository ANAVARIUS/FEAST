# Pruebas estaticas (STD 4.1)

Analisis de codigo **sin ejecutar** la logica de negocio dinamica.

| ID | Para que sirve |
|----|----------------|
| CP-STATIC-01 | Comprobar estilo PEP 8 y ausencia de errores sintacticos fatales (`ruff` / pylint / flake8 sobre `src/`). |
| CP-STATIC-02 | Verificar consistencia de tipos (`mypy --strict` sobre `src/`). |
| CP-STATIC-03 | Limitar complejidad ciclomatica (McCabe, p. ej. `radon cc src/ -a`). |
| CP-STATIC-04 | Detectar patrones inseguros (`bandit -r src/`). |
| CP-STATIC-05 | Docstrings obligatorios en modulos publicos criticos (pylint C0114-C0116). |
| CP-STATIC-06 | Regla de inmutabilidad del estado LangGraph (script AST / revision). |

**Ejecucion tipica (CI):** `ruff check .` segun `.github/workflows/CI.yaml`.
