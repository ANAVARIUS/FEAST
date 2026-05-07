import uuid
from datetime import datetime
from src.models.schemas.db import (
    create_status, 
    create_branch, 
    create_user, 
    create_address,
    create_delivery_person,
    create_ingredient,
    create_item,
    add_ingredient_to_item,
    add_item_to_branch,
    create_order,
    add_item_to_order,
    create_delivery,
    add_ingredient_to_branch
)
from src.infrastructure.repositories.vector_repository import VectorRepository

def seed_database():
    try:
        st_pend = create_status("Pendiente", 1)
        st_prep = create_status("Preparando", 2)
        st_env  = create_status("Enviado", 3)
        st_ent  = create_status("Entregado", 4)
        print("✅ Estados creados.")

        sucursal = create_branch(
            name="Pizza Planeta Centro", 
            address="Av. Galaxia 42", 
            phone="555-0123"
        )
        print(f"✅ Sucursal creada: {sucursal.Name}")

        usuario = create_user(
            name="Arturo", 
            last_name="Reyes", 
            email="arturo@ejemplo.com", 
            phone="3312345678", 
            app_id="auth0|789abc"
        )
        direccion = create_address(
            user_id=usuario.UserID,
            country="México",
            state="Jalisco",
            city="Guadalajara",
            neighborhood="Americana",
            zip_code="44160",
            ext_num="500"
        )
        print(f"✅ Usuario {usuario.Name} y dirección registrados.")

        repartidor = create_delivery_person("Carlos", "Veloz", "3398765432")
        print(f"✅ Repartidor {repartidor.Name} registrado.")

        ing_queso  = create_ingredient("Extra Queso")
        ing_masa   = create_ingredient("Orilla de Queso")
        ing_pep    = create_ingredient("Pepperoni Premium")
        ing_piña   = create_ingredient("Piña Asada")
        ing_champi = create_ingredient("Champiñones Frescos")
        
        items_menu = [
            create_item("Pizza Pepperoni",          189.00, "Pizzas"),
            create_item("Pizza Hawaiana Galáctica", 199.00, "Pizzas"),
            create_item("Pizza Vegetariana",         175.00, "Pizzas"),
            create_item("Pizza de Carnes Frías",     220.00, "Pizzas"),
            create_item("Palitroques de Ajo",         85.00, "Entradas"),
            create_item("Alitas BBQ (10 pzas)",      160.00, "Entradas"),
        ]

        bebidas = [
            create_item("Coca Cola 600ml",               35.00, "Bebidas"),
            create_item("Agua Mineral 500ml",            28.00, "Bebidas"),
            create_item("Té Frío de Limón",              32.00, "Bebidas"),
            create_item("Cerveza Artesanal 'Andrómeda'", 75.00, "Bebidas"),
        ]

        todos_los_productos = items_menu + bebidas

        add_ingredient_to_item(ing_pep.IngredientID,   items_menu[0].ItemID, 1)
        add_ingredient_to_item(ing_queso.IngredientID, items_menu[0].ItemID, 1)
        add_ingredient_to_item(ing_piña.IngredientID,  items_menu[1].ItemID, 1)

        for producto in todos_los_productos:
            add_item_to_branch(sucursal.BranchID, producto.ItemID, True)
        print(f"✅ Menú expandido: {len(todos_los_productos)} productos registrados.")

        for ingrediente in [ing_queso, ing_masa, ing_pep, ing_piña, ing_champi]:
            add_ingredient_to_branch(
                branch_id=sucursal.BranchID, 
                ingredient_id=ingrediente.IngredientID, 
                available=True
            )

        items_a_ordenar = [items_menu[0], bebidas[0]]
        total_orden = sum(item.Price for item in items_a_ordenar)

        orden = create_order(
            user_id=usuario.UserID,
            branch_id=sucursal.BranchID,
            total=total_orden,
            status_id=st_pend.StatusID
        )
        for item in items_a_ordenar:
            add_item_to_order(orden.OrderID, item.ItemID, 1)
        print(f"✅ Orden {orden.OrderID} creada con {len(items_a_ordenar)} productos. Total: ${total_orden}")

        entrega = create_delivery(
            order_id=orden.OrderID,
            delivery_person_id=repartidor.DeliveryPersonID,
            status_id=st_env.StatusID,
            estimated_time=datetime.utcnow()
        )
        print(f"✅ Entrega asignada a {repartidor.Name}.")

        # -------- VECTOR DB --------
        vector_repo = VectorRepository()
        platillos_vectoriales = [
            (todos_los_productos[0].ItemID,  "Pizza Pepperoni",                "Pizza clásica con pepperoni premium y extra queso"),
            (todos_los_productos[1].ItemID,  "Pizza Hawaiana Galáctica",       "Pizza con piña asada y jamón"),
            (todos_los_productos[2].ItemID,  "Pizza Vegetariana",              "Pizza con champiñones frescos y verduras"),
            (todos_los_productos[3].ItemID,  "Pizza de Carnes Frías",          "Pizza con variedad de carnes frías"),
            (todos_los_productos[4].ItemID,  "Palitroques de Ajo",             "Palitroques crujientes con mantequilla de ajo"),
            (todos_los_productos[5].ItemID,  "Alitas BBQ (10 pzas)",           "Alitas de pollo bañadas en salsa BBQ"),
            (todos_los_productos[6].ItemID,  "Coca Cola 600ml",                "Refresco de cola 600ml bien frío"),
            (todos_los_productos[7].ItemID,  "Agua Mineral 500ml",             "Agua mineral natural 500ml"),
            (todos_los_productos[8].ItemID,  "Té Frío de Limón",               "Té helado con limón natural"),
            (todos_los_productos[9].ItemID,  "Cerveza Artesanal 'Andrómeda'",  "Cerveza artesanal estilo lager con notas cítricas"),
        ]

        for id, nombre, descripcion in platillos_vectoriales:
            vector_repo.crear(id, nombre, descripcion)
            print(f"✅ Vector indexado: {nombre}")

        print("¡Poblado completado con éxito!")
        
    except Exception as e:
        print(f"❌ Error durante el poblado: {e}")

if __name__ == "__main__":
    seed_database()