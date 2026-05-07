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
    def find_items_by_query(query: str, limit: int = 5) -> List[Item]:
        """
        Busca productos por nombre (subcadena, coincidencia exacta o solapamiento de palabras).
        Usado por el cart manager para mapear lenguaje natural a ItemID.
        """
        q = (query or "").strip().lower()
        if not q:
            return []
        items = MenuRepository.get_full_catalog()
        if not items:
            return []
        exact = [it for it in items if it.Name.lower() == q]
        if exact:
            return exact[:limit]
        substr = [it for it in items if q in it.Name.lower()]
        if substr:
            return substr[:limit]
        q_words = set(q.split())
        scored: List[tuple[int, Item]] = []
        for it in items:
            name_words = set(it.Name.lower().split())
            overlap = len(q_words & name_words)
            if overlap:
                scored.append((overlap, it))
        scored.sort(key=lambda t: t[0], reverse=True)
        return [it for _, it in scored[:limit]]

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
        Útil si el usuario pregunta por ingredientes o composición de un platillo concreto.
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
        """Filtra el menú de una sucursal por una categoría específica (ej. bebidas, postres)."""
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