from sqlalchemy.orm import Session
from app.database.connection import db
from app.models.menu import MenuItem, MenuSize
from app.database.base import Base


def seed_menu():
    # ✅ Ensure tables exist before seeding
    # Base.metadata.create_all(bind=engine)

    session: Session = db.get_session()

    try:
        # Prevent duplicate seeding
        existing = session.query(MenuItem).first()
        if existing:
            print("Menu already seeded.")
            return

        # 🔥 PIZZAS
        pizzas = [
            ("Margherita Pizza", [("S", 83), ("M", 100), ("L", 140)]),
            ("Vegetables Pizza", [("S", 85), ("M", 105), ("L", 145)]),
            ("Mushroom Pizza", [("S", 90), ("M", 120), ("L", 160)]),
            ("Cheese Lovers Pizza", [("S", 100), ("M", 125), ("L", 170)]),
            ("Hot Dog Pizza", [("S", 100), ("M", 125), ("L", 170)]),
            ("Salami Pizza", [("S", 105), ("M", 135), ("L", 180)]),
            ("Pastrami Pizza", [("S", 105), ("M", 135), ("L", 180)]),
            ("Double Pepperoni Pizza", [("S", 110), ("M", 145), ("L", 195)]),
            ("Super Supreme Pizza", [("S", 125), ("M", 165), ("L", 215)]),
        ]

        items_to_add = []
        sizes_to_add = []

        for name, sizes in pizzas:
            item = MenuItem(name=name, category="pizza",is_available=True)
            items_to_add.append(item)
            session.flush()  # Assign ID without committing
            session.add(item)
            session.flush()  # Make sure item.id exists

            for size, price in sizes:
                sizes_to_add.append(MenuSize(
                    menu_item_id=item.id,
                    size=size,
                    price=price,
                    is_available=True
                ))

        # 🔥 ADDITIONS
        additions = [
            ("Fries", 50),
            ("Mango Juice", 40),
            ("Cola", 20),
            ("Water", 10),
        ]

        for name, price in additions:
            item = MenuItem(name=name, category="addition",is_available=True)
            items_to_add.append(item)
            session.add(item)
            session.flush()

            sizes_to_add.append(MenuSize(
                menu_item_id=item.id,
                size="REG",
                price=price,
                is_available=True
            ))

        # Commit all at once
        session.add_all(items_to_add)
        session.add_all(sizes_to_add)
        session.commit()

        print("Menu seeded successfully ✅")

    except Exception as e:
        session.rollback()
        print(f"Error seeding menu: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    seed_menu()
