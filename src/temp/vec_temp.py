from src.infrastructure.repositories.vector_repository import VectorRepository
from src.infrastructure.repositories.menu_repository import MenuRepository
import uuid

dbV = VectorRepository()
dbS = MenuRepository()
resultV = dbV.buscar("palitos")
#resultV[0]["_id"]
result = dbS.find_items_by_query(resultV[0]["_source"]["nombre"])
print("hola")
print(resultV)
print("adios")
print(result[0].Name)
