from STORE import db
from STORE.models import Product
import csv

def add_products_from_csv(csv_file):
    try:
        with open(csv_file, 'r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                product = Product(
                    code=row['code'],
                    item=row['item'],
                    category=row['category'],
                    type_material=row['type_material'],
                    size=row['size'],
                    color=row['color'],
                    description=row['description'],
                    buying_price=float(row['buying_price']),
                    selling_price=float(row['selling_price']),
                    quantity=int(row['quantity'])
                )
                db.session.add(product)
        db.session.commit()
        print('Data added to database successfully')
    except Exception as e:
        print('Error adding data to database:', str(e))

if __name__ == '__main__':
    csv_file = 'products.csv'  # Assuming your CSV file is named products.csv and is in the same directory
    add_products_from_csv(csv_file)
