import uuid
from datetime import datetime
from sqlalchemy import String, UUID, ForeignKey, Integer, Numeric, DateTime, Boolean, MetaData, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from typing import List
from src.infrastructure.repositories.connnect import db, SessionLocal, Base

class User(Base):
    __tablename__ = "User"
    UserID: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    AppID: Mapped[str] = mapped_column(String(100), unique=True)
    Name: Mapped[str] = mapped_column(String(100))
    LastName: Mapped[str] = mapped_column(String(100))
    PhoneNumber: Mapped[str] = mapped_column(String(30))
    Email: Mapped[str] = mapped_column(String(100))

    addresses: Mapped[list["UserAddress"]] = relationship(back_populates="owner")
    orders: Mapped[list["Order"]] = relationship(back_populates="user")

class UserAddress(Base):
    __tablename__ = "UserAddress"
    UserAddressID: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    UserID: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("User.UserID"))
    Country: Mapped[str] = mapped_column(String(100))
    State: Mapped[str] = mapped_column(String(100))
    City: Mapped[str] = mapped_column(String(100))
    Neighborhood: Mapped[str] = mapped_column(String(100))
    ZipCode: Mapped[str] = mapped_column(String(30))
    ExtNum: Mapped[str] = mapped_column(String(100))
    IntNum: Mapped[str] = mapped_column(String(100), nullable=True)

    owner: Mapped["User"] = relationship(back_populates="addresses")

class Order(Base):
    __tablename__ = "Order"
    OrderID: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    UserID: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("User.UserID"))
    StatusID: Mapped[int] = mapped_column(Integer, ForeignKey("Status.StatusID"))
    BranchID: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("Branch.BranchID"))
    TotalAmount: Mapped[float] = mapped_column(Numeric(10, 2))
    CreateAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="orders")
    status: Mapped["Status"] = relationship(back_populates="orderStatus")
    branch: Mapped["Branch"] = relationship(back_populates="orderBranch")
    orderToDeliver: Mapped["Delivery"] = relationship(back_populates="deliveryOrder")
    itemsInOrder: Mapped[list["OrderItem"]] = relationship(back_populates="orderItem")

class Status(Base):
    __tablename__ = "Status"
    StatusID: Mapped[int] = mapped_column(Integer, primary_key=True)
    Status: Mapped[str] = mapped_column(String(50))

    orderStatus: Mapped[list["Order"]] = relationship(back_populates="status")
    deliveryStatus: Mapped[list["Delivery"]] = relationship(back_populates="statusOfDelivery")

class Branch(Base):
    __tablename__ = "Branch"
    BranchID: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    Name: Mapped[str] = mapped_column(String(100))
    Address: Mapped[str] = mapped_column(String(100))
    PhoneNumber: Mapped[str] = mapped_column(String(100))

    orderBranch: Mapped[list["Order"]] = relationship(back_populates="branch")
    branchHasItem: Mapped[list["BranchItem"]] = relationship(back_populates="branchItem")
    ingredientsForBranch: Mapped[list["IngredientBranch"]] = relationship(back_populates="ingredientBranch")

class Delivery(Base):
    __tablename__ = "Delivery"
    DeliveryID: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    OrderID: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("Order.OrderID"))
    DeliveryPersonID: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("DeliveryPerson.DeliveryPersonID"))
    StatusID: Mapped[int] = mapped_column(Integer, ForeignKey("Status.StatusID"))
    EstimatedDeliveryTime: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    ActualDeliveryTime: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    deliveryOrder: Mapped["Order"] = relationship(back_populates="orderToDeliver")
    deliveryPerson: Mapped["DeliveryPerson"] = relationship(back_populates="orderDelivery")
    statusOfDelivery: Mapped["Status"] = relationship(back_populates="deliveryStatus")

class DeliveryPerson(Base):
    __tablename__ = "DeliveryPerson"
    DeliveryPersonID: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    Name: Mapped[str] = mapped_column(String(100))
    LastName: Mapped[str] = mapped_column(String(100))
    PhoneNumber: Mapped[str] = mapped_column(String(30))

    orderDelivery: Mapped[list["Delivery"]] = relationship(back_populates="deliveryPerson")

class Ingredient(Base):
    __tablename__ = "Ingredient"
    IngredientID: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    Name: Mapped[str] = mapped_column(String(100))

    ingredientsInItem: Mapped[list["IngredientItem"]] = relationship(back_populates="ingredient")
    branchHasIngredient: Mapped[list["IngredientBranch"]] = relationship(back_populates="ingredientsInBranch")

class Item(Base):
    __tablename__ = "Item"
    ItemID: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    Name: Mapped[str] = mapped_column(String(100))
    Price: Mapped[float] = mapped_column(Numeric(10, 2))
    Category: Mapped[str] = mapped_column(String(100))

    itemIngredients: Mapped[list["IngredientItem"]] = relationship(back_populates="item")
    itemsList: Mapped[list["OrderItem"]] = relationship(back_populates="itemToOrder")
    itemsForBranch: Mapped[list["BranchItem"]] = relationship(back_populates="itemInBranch")

class IngredientItem(Base):
    __tablename__ = "IngredientItem"
    IngredientID: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("Ingredient.IngredientID"), primary_key=True)
    ItemID: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("Item.ItemID"), primary_key=True)
    Quantity: Mapped[int] = mapped_column(Integer)

    ingredient: Mapped["Ingredient"] = relationship(back_populates="ingredientsInItem")
    item: Mapped["Item"] = relationship(back_populates="itemIngredients")

class OrderItem(Base):
    __tablename__ = "OrderItem"
    OrderID: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("Order.OrderID"), primary_key=True)
    ItemID: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("Item.ItemID"), primary_key=True)
    Quantity: Mapped[int] = mapped_column(Integer)

    orderItem: Mapped["Order"] = relationship(back_populates="itemsInOrder") 
    itemToOrder: Mapped["Item"] = relationship(back_populates="itemsList")

class BranchItem(Base):
    __tablename__ = "BranchItem"
    BranchID: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("Branch.BranchID"), primary_key=True)
    ItemID: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("Item.ItemID"), primary_key=True)
    IsAvalible: Mapped[bool] = mapped_column(Boolean, server_default="1")

    branchItem: Mapped["Branch"] = relationship(back_populates="branchHasItem")
    itemInBranch: Mapped["Item"] = relationship(back_populates="itemsForBranch")

class IngredientBranch(Base):
    __tablename__ = "IngredientBranch"
    BranchID: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("Branch.BranchID"), primary_key=True)
    IngredientID: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("Ingredient.IngredientID"), primary_key=True)
    IsAvalible: Mapped[bool] = mapped_column(Boolean, server_default="1")

    ingredientBranch: Mapped["Branch"] = relationship(back_populates="ingredientsForBranch")
    ingredientsInBranch: Mapped["Ingredient"] = relationship(back_populates="branchHasIngredient")

####################
# Entidades fuertes
####################

def get_session():
    return Session(db)

def create_user(name: str, last_name: str, email: str, phone: str, app_id: str):
    with get_session() as session:
        new_user = User(
            Name=name,
            LastName=last_name,
            Email=email,
            PhoneNumber=phone,
            AppID=app_id
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        return new_user

def get_user_by_id(user_id: uuid.UUID):
    with get_session() as session:
        return session.get(User, user_id)

def get_all_users():
    with get_session() as session:
        return session.query(User).all()

def update_user(user_id: uuid.UUID, **kwargs):
    with get_session() as session:
        user = session.get(User, user_id)
        if not user:
            return None
        for key, value in kwargs.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        session.commit()
        session.refresh(user)
        return user

def delete_user(user_id: uuid.UUID):
    with get_session() as session:
        user = session.get(User, user_id)
        if user:
            session.delete(user)
            session.commit()
            return True
        return False

def create_address(user_id: uuid.UUID, country: str, state: str, city: str, neighborhood: str, zip_code: str, ext_num: str, int_num: str = None):
    with get_session() as session:
        new_address = UserAddress(
            UserID=user_id,
            Country=country,
            State=state,
            City=city,
            Neighborhood=neighborhood,
            ZipCode=zip_code,
            ExtNum=ext_num,
            IntNum=int_num
        )
        session.add(new_address)
        session.commit()
        session.refresh(new_address)
        return new_address

def get_address_by_id(address_id: uuid.UUID):
    with get_session() as session:
        return session.get(UserAddress, address_id)

def get_user_addresses():
    with get_session() as session:
        return session.query(UserAddress).all()

def delete_address(address_id: uuid.UUID):
    with get_session() as session:
        address = session.get(UserAddress, address_id)
        if address:
            session.delete(address)
            session.commit()
            return True
        return False

def create_order(user_id: uuid.UUID, branch_id: uuid.UUID, total: float, status_id: int):
    with get_session() as session:
        new_order = Order(
            UserID=user_id,
            BranchID=branch_id,
            TotalAmount=total,
            StatusID=status_id
        )
        session.add(new_order)
        session.commit()
        session.refresh(new_order)
        return new_order

def get_order_by_id(order_id: uuid.UUID):
    with get_session() as session:
        return session.get(Order, order_id)

def get_orders():
    with get_session() as session:
        return session.query(Order).all()

def create_status(status_name: str, status_id: int = None):
    with get_session() as session:
        new_status = Status(
            StatusID=status_id,
            Status=status_name
        )
        session.add(new_status)
        session.commit()
        session.refresh(new_status)
        return new_status

def get_all_statuses():
    with get_session() as session:
        return session.query(Status).all()

def get_status_by_id(status_id: int):
    with get_session() as session:
        return session.get(Status, status_id)

def create_branch(name: str, address: str, phone: str):
    with get_session() as session:
        new_branch = Branch(
            Name=name,
            Address=address,
            PhoneNumber=phone
        )
        session.add(new_branch)
        session.commit()
        session.refresh(new_branch)
        return new_branch

def get_all_branches():
    with get_session() as session:
        return session.query(Branch).all()

def get_branch_by_id(branch_id: uuid.UUID):
    with get_session() as session:
        return session.get(Branch, branch_id)

def create_delivery(order_id: uuid.UUID, delivery_person_id: uuid.UUID, status_id: int, estimated_time: datetime = None):
    with get_session() as session:
        new_delivery = Delivery(
            OrderID=order_id,
            DeliveryPersonID=delivery_person_id,
            StatusID=status_id,
            EstimatedDeliveryTime=estimated_time
        )
        session.add(new_delivery)
        session.commit()
        session.refresh(new_delivery)
        return new_delivery

def get_all_deliveries():
    with get_session() as session:
        return session.query(Delivery).all()

def get_delivery_by_id(delivery_id: uuid.UUID):
    with get_session() as session:
        return session.get(Delivery, delivery_id)

def create_delivery_person(name: str, last_name: str, phone_number: str):
    with get_session() as session:
        new_person = DeliveryPerson(
            Name=name,
            LastName=last_name,
            PhoneNumber=phone_number
        )
        session.add(new_person)
        session.commit()
        session.refresh(new_person)
        return new_person

def get_all_delivery_persons():
    with get_session() as session:
        return session.query(DeliveryPerson).all()

def get_delivery_person_by_id(person_id: uuid.UUID):
    with get_session() as session:
        return session.get(DeliveryPerson, person_id)

def create_ingredient(name: str):
    with get_session() as session:
        new_ingredient = Ingredient(
            Name=name
        )
        session.add(new_ingredient)
        session.commit()
        session.refresh(new_ingredient)
        return new_ingredient

def get_all_ingredients():
    with get_session() as session:
        return session.query(Ingredient).all()

def get_ingredient_by_id(ingredient_id: uuid.UUID):
    with get_session() as session:
        return session.get(Ingredient, ingredient_id)

def create_item(name: str, price: float, category: str):
    with get_session() as session:
        new_item = Item(
            Name=name,
            Price=price,
            Category=category
        )
        session.add(new_item)
        session.commit()
        session.refresh(new_item)
        return new_item

def get_all_items():
    with get_session() as session:
        return session.query(Item).all()

def get_item_by_id(item_id: uuid.UUID):
    with get_session() as session:
        return session.get(Item, item_id)

####################
# Entidades debiles
####################

def add_ingredient_to_item(ingredient_id: uuid.UUID, item_id: uuid.UUID, quantity: int):
    with get_session() as session:
        new_link = IngredientItem(
            IngredientID=ingredient_id,
            ItemID=item_id,
            Quantity=quantity
        )
        session.add(new_link)
        session.commit()
        session.refresh(new_link)
        return new_link

def get_ingredient_item(ingredient_id: uuid.UUID, item_id: uuid.UUID):
    with get_session() as session:
        return session.get(IngredientItem, (ingredient_id, item_id))

def get_recipe_by_item(item_id: uuid.UUID):
    with get_session() as session:
        return session.query(IngredientItem).filter(IngredientItem.ItemID == item_id).all()

def add_item_to_order(order_id: uuid.UUID, item_id: uuid.UUID, quantity: int):
    with get_session() as session:
        new_order_item = OrderItem(
            OrderID=order_id,
            ItemID=item_id,
            Quantity=quantity
        )
        session.add(new_order_item)
        session.commit()
        session.refresh(new_order_item)
        return new_order_item

def get_order_item_detail(order_id: uuid.UUID, item_id: uuid.UUID):
    with get_session() as session:
        return session.get(OrderItem, (order_id, item_id))

def get_items_by_order(order_id: uuid.UUID):
    with get_session() as session:
        return session.query(OrderItem).filter(OrderItem.OrderID == order_id).all()

def add_item_to_branch(branch_id: uuid.UUID, item_id: uuid.UUID, is_available: bool = True):
    with get_session() as session:
        new_branch_item = BranchItem(
            BranchID=branch_id,
            ItemID=item_id,
            IsAvalible=is_available
        )
        session.add(new_branch_item)
        session.commit()
        session.refresh(new_branch_item)
        return new_branch_item

def get_menu_by_branch(branch_id: uuid.UUID):
    with get_session() as session:
        return session.query(BranchItem).filter(BranchItem.BranchID == branch_id).all()

def get_branch_item_detail(branch_id: uuid.UUID, item_id: uuid.UUID):
    with get_session() as session:
        return session.get(BranchItem, (branch_id, item_id))

def add_ingredient_to_branch(branch_id: uuid.UUID, ingredient_id: uuid.UUID, available: bool = True):
    with get_session() as session:
        new_entry = IngredientBranch(
            BranchID=branch_id,
            IngredientID=ingredient_id,
            IsAvalible=available
        )
        session.add(new_entry)
        session.commit()
        session.refresh(new_entry)
        return new_entry

def get_ingredient_branch_detail(branch_id: uuid.UUID, ingredient_id: uuid.UUID):
    with get_session() as session:
        return session.get(IngredientBranch, (branch_id, ingredient_id))

def get_ingredients_by_branch(branch_id: uuid.UUID):
    with get_session() as session:
        return session.query(IngredientBranch).filter(IngredientBranch.BranchID == branch_id).all()
