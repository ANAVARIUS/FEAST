from src.models.schemas.db import get_session, Item, BranchItem, IngredientItem, Ingredient
from typing import List, Optional, Dict, Any
import uuid

class MenuRepository:
    """
    Repositorio encargado de interactuar con las tablas de Menú (Item, BranchItem) en RDS.
    """

    @staticmethod
    def get_full_catalog() -> List[Item]:
        """Obtiene todos los productos del menú sin filtro de sucursal."""
        with get_session() as session:
            return session.query(Item).all()

    @staticmethod
    def get_menu_by_branch(branch_id: uuid.UUID) -> List[Dict[str, Any]]:
        """
        Obtiene el menú disponible para una sucursal específica.
        Devuelve una lista de diccionarios con los detalles del producto para que 
        el futuro worker/LLM pueda leerlo fácilmente.
        """
        with get_session() as session:
            menu_items = (
                session.query(BranchItem, Item)
                .join(Item, BranchItem.ItemID == Item.ItemID)
                .filter(
                    BranchItem.BranchID == branch_id,
                    BranchItem.IsAvalible == True
                )
                .all()
            )
            
            result: List[Dict[str, Any]] = []
            for _branch_item, item in menu_items:
                result.append({
                    "item_id": str(item.ItemID),
                    "name": item.Name,
                    "price": float(item.Price),
                    "category": item.Category
                })
            return result

    @staticmethod
    def get_item_details(item_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Obtiene los detalles de un producto específico, incluyendo su receta (ingredientes).
        Útil si el usuario pregunta "¿Qué lleva la hamburguesa?".
        """
        with get_session() as session:
            item = session.get(Item, item_id)
            if not item:
                return None

            recipe = (
                session.query(IngredientItem, Ingredient)
                .join(Ingredient, IngredientItem.IngredientID == Ingredient.IngredientID)
                .filter(IngredientItem.ItemID == item_id)
                .all()
            )

            ingredients_list = [f"{ing.Name} (x{rec.Quantity})" for rec, ing in recipe]

            return {
                "item_id": str(item.ItemID),
                "name": item.Name,
                "price": float(item.Price),
                "category": item.Category,
                "ingredients": ingredients_list
            }

    @staticmethod
    def get_menu_by_category(branch_id: uuid.UUID, category: str) -> List[Dict[str, Any]]:
        """Filtra el menú de una sucursal por una categoría específica (ej. 'Hamburguesas')."""
        with get_session() as session:
            menu_items = (
                session.query(BranchItem, Item)
                .join(Item, BranchItem.ItemID == Item.ItemID)
                .filter(
                    BranchItem.BranchID == branch_id,
                    BranchItem.IsAvalible == True,
                    Item.Category.ilike(f"%{category}%")
                )
                .all()
            )
            
            result: List[Dict[str, Any]] = []
            for _branch_item, item in menu_items:
                result.append({
                    "item_id": str(item.ItemID),
                    "name": item.Name,
                    "price": float(item.Price),
                    "category": item.Category
                })
            return result