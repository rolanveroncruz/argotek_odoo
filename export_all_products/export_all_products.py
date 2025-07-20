import xmlrpc.client
from ProdConfig import ProdConfig as Config
import csv
import json
import os

# --- Odoo Connection Details ---
# Replace with your Odoo instance details

# --- Output File Names ---
OUTPUT_CSV_FILE = 'all_products.csv'
OUTPUT_JSON_FILE = 'all_products.json'

def get_config() -> Config:
    config = Config()
    print(config)
    return config

def export_all_products(config:Config,):
    """
    Connects to Odoo, fetches all product variants, and exports their details.
    """
    print(f"Connecting to Odoo at {config.HOST} (Database: {config.DB})...")
    try:
        # Authenticate and get UID
        common = xmlrpc.client.ServerProxy(f'{config.HOST}/xmlrpc/2/common')
        uid = common.authenticate(config.DB, config.USER_EMAIL, config.API_KEY, {})
        if not uid:
            print("Authentication failed. Check your Odoo URL, DB, username, and password.")
            return

        print(f"Authentication successful. User ID: {uid}")

        # Get the object proxy for models
        models = xmlrpc.client.ServerProxy(f'{config.HOST}/xmlrpc/2/object')

        # --- 1. Search for all product.product records ---
        # No domain needed to get all products.
        print("Searching for all product variants (product.product records)...")
        product_ids = models.execute_kw(
            config.DB, uid, config.API_KEY,
            'product.product', 'search',
            [[]] # Empty domain means search all records
        )

        if not product_ids:
            print("No products found in Odoo.")
            return

        print(f"Found {len(product_ids)} product variants. Reading details...")

        # --- 2. Define Fields to Read ---
        # Include common fields and relevant relational fields.
        # For many2one fields, get the name by appending '.name'.
        # For many2many/one2many, you might need separate queries or custom logic.
        fields_to_read = [
            'default_code',        # Internal Reference / SKU
            'name',                # Product Name (for variants, includes attributes)
            'display_name',        # Full display name (e.g., "Customizable Desk (White)")
            'product_tmpl_id',     # Product Template (will return [ID, Name])
            'list_price',          # Sales Price (Public Price)
            'standard_price',      # Cost
            'categ_id',            # Product Category (will return [ID, Name])
            'type',                # Product Type (e.g., 'consu', 'service', 'product')
            'uom_id',              # Sales Unit of Measure (will return [ID, Name])
            'uom_po_id',           # Purchase Unit of Measure (will return [ID, Name])
            'active',              # Is product active? (boolean)
            'barcode',             # Barcode
            'description_sale',    # Sales Description
            'description_purchase',# Purchase Description
            'tracking',            # Tracking (no_tracking, lot, serial)
            'qty_available',       # Quantity On Hand (computed field)
            'virtual_available',   # Forecasted Quantity (computed field)
            'weight',              # Weight
            'volume',              # Volume
            # Add more fields as needed, e.g., for custom fields: 'x_my_custom_field'
        ]

        # --- 3. Read Product Data ---
        products_data = models.execute_kw(
            config.DB, uid, config.API_KEY,
            'product.product', 'read',
            [product_ids],
            {'fields': fields_to_read}
        )

        # --- 4. Process and Prepare Data for Export ---
        processed_products = []
        for product in products_data:
            processed_product = {
                'Internal_Reference': product.get('default_code', ''),
                'Product_Name': product.get('name', ''),
                'Display_Name': product.get('display_name', ''),
                'Product_Template': product['product_tmpl_id'][1] if product['product_tmpl_id'] else '',
                'Sales_Price': product.get('list_price', 0.0),
                'Cost': product.get('standard_price', 0.0),
                'Category': product['categ_id'][1] if product['categ_id'] else '',
                'Product_Type': product.get('type', ''),
                'Sales_UoM': product['uom_id'][1] if product['uom_id'] else '',
                'Purchase_UoM': product['uom_po_id'][1] if product['uom_po_id'] else '',
                'Active': product.get('active', False),
                'Barcode': product.get('barcode', ''),
                'Sales_Description': product.get('description_sale', ''),
                'Purchase_Description': product.get('description_purchase', ''),
                'Tracking': product.get('tracking', 'no_tracking'),
                'Quantity_On_Hand': product.get('qty_available', 0.0),
                'Forecasted_Quantity': product.get('virtual_available', 0.0),
                'Weight': product.get('weight', 0.0),
                'Volume': product.get('volume', 0.0),
                # Add more processed fields here
            }
            processed_products.append(processed_product)

        # --- 5. Export to CSV ---
        if processed_products:
            csv_headers = list(processed_products[0].keys()) # Use keys from the first processed product as headers

            with open(OUTPUT_CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
                writer.writeheader()
                writer.writerows(processed_products)
            print(f"Data successfully exported to {OUTPUT_CSV_FILE}")
        else:
            print("No products to export to CSV.")

        # --- 6. Export to JSON ---
        with open(OUTPUT_JSON_FILE, 'w', encoding='utf-8') as jsonfile:
            json.dump(processed_products, jsonfile, indent=4, ensure_ascii=False)
        print(f"Data successfully exported to {OUTPUT_JSON_FILE}")

    except xmlrpc.client.Fault as err:
        print(f"XML-RPC Fault: {err.faultCode} - {err.faultString}")
    except Exception as e:
        print(f"An error occurred: {e}")

    print("Export complete.")


if __name__ == "__main__":
    config = get_config()
    export_all_products(config)