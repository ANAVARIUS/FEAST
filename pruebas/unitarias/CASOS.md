# Pruebas unitarias (STD 4.2)

Validacion **determinista** de componentes con mocks (sin BD ni APIs reales).

| ID | Para que sirve |
|----|----------------|
| CP-UNIT-TOOL-01 | `get_menu` formatea catalogo con encabezado `--- MENU DISPONIBLE ---` y precios correctos. |
| CP-UNIT-TOOL-02 | `get_menu` con catalogo vacio devuelve el mensaje acordado al usuario. |
| CP-UNIT-TOOL-03 | `get_menu` ante error del repositorio no oculta el fallo (propaga o control explicito). |
| CP-UNIT-GRAPH-01 | `route_intent` con `intent=MENU` enruta a `"MENU"`. |
| CP-UNIT-GRAPH-02 | `route_intent` sin intencion usa `"GENERAL"`. |
| CP-UNIT-GRAPH-03 | `router_node` con mensajes vacios no lanza (intencion coherente con mock LLM). |
| CP-UNIT-STATE-01 | Valores opcionales del estado al inicio del flujo (convencion FEAST / webhook). |
| CP-UNIT-STATE-02 | Timestamps `created_at` / `updated_at` en UTC con formato ISO 8601. |
| CP-UNIT-PAYMENT-01 / 02 | Totales e impuestos / limites de carrito (cuando exista tool de checkout en codigo). |

Las filas con tests automatizados estan cubiertas por `test_cp_menu.py`, `test_cp_graph_route.py` y `test_cp_state_time.py` en esta carpeta.
