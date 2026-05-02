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
        ing_queso = create_ingredient("Extra Queso")
        ing_masa = create_ingredient("Orilla de Queso")
        
        platillo = create_item("Pizza Pepperoni", 189.00, "Pizzas")
        refresco = create_item("Coca Cola 600ml", 35.00, "Bebidas")
        
        add_ingredient_to_item(ing_queso.IngredientID, platillo.ItemID, 1)
        add_item_to_branch(sucursal.BranchID, platillo.ItemID, True)
        add_item_to_branch(sucursal.BranchID, refresco.ItemID, True)
        print("✅ Menú e ingredientes configurados.")

        orden = create_order(
            user_id=usuario.UserID,
            branch_id=sucursal.BranchID,
            total=224.00,
            status_id=st_pend.StatusID
        )
        
        add_item_to_order(orden.OrderID, platillo.ItemID, 1)
        add_item_to_order(orden.OrderID, refresco.ItemID, 1)
        print(f"✅ Orden {orden.OrderID} creada con productos.")

        entrega = create_delivery(
            order_id=orden.OrderID,
            delivery_person_id=repartidor.DeliveryPersonID,
            status_id=st_env.StatusID,
            estimated_time=datetime.utcnow()
        )
        print(f"✅ Entrega asignada a {repartidor.Name}.")

        add_ingredient_to_branch(
            branch_id=sucursal.BranchID, 
            ingredient_id=ing_queso.IngredientID, 
            available=True
        )
        add_ingredient_to_branch(
            branch_id=sucursal.BranchID, 
            ingredient_id=ing_masa.IngredientID, 
            available=True
        )
        print(f"✅ Inventario de ingredientes vinculado a {sucursal.Name}.")

        print("¡Poblado completado con éxito!")
        
    except Exception as e:
        print(f"❌ Error durante el poblado: {e}")

if __name__ == "__main__":
    seed_database()