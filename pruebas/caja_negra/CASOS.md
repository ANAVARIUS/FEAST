# Pruebas de caja negra (STD 4.5)

Particion de **equivalencia** y **valores limite** sobre reglas de negocio (stock, precios, promos, carrito, limites Telegram).

| ID | Para que sirve |
|----|----------------|
| CP-STOCK-EQ-01 | Clases de equivalencia cantidad vs stock (`check_stock_by_id` cuando exista en codigo). |
| CP-PRICE-EQ-01 | Formato y validez de precios en salida de menu. |
| CP-PROMO-EQ-01 | Elegibilidad y vigencia de promociones. |
| CP-CART-EQ-01 | Cantidades en carrito: actualizar / eliminar / error / stock. |
| CP-INT-LIMIT-01 / 02 / 03 | Limites de items por pedido/dia, longitud de mensaje, rate limit Telegram. |

Los tests en `test_cp_particiones.py` codifican las **reglas documentadas** del STD como funciones puras (sin BD), para tener senal verde hasta que existan las tools reales.
