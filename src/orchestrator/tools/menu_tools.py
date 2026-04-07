from langchain_core.tools import tool
from src.infrastructure.repositories.menu_repository import MenuRepository

@tool
def get_menu() -> str:
    """
    Consulta la base de datos relacional y obten el catalogo completo del menu.
    Devuelve una lista formateada con los nombres, categorias y precios de los productos.
    usese siempre que el usuario pregunte qué hay disponible para comer o pedir.
    """
    repo = MenuRepository()
    
    # mandamos a llamer el metodo que creamos en menu repositories
    items = repo.get_full_catalog()
    
    if not items:
        return "Lo siento, actualmente no hay productos disponibles en el menu."
    
    # formateamos la salida para que el LLM lo entienda como texto
    menu_str = "--- MENU DISPONIBLE ---\n"
    for item in items:
        menu_str += f"- {item.Name} | Categoría: {item.Category} | Precio: ${float(item.Price):.2f}\n"
    
    return menu_str