import xmlrpc.client
from ProdConfig import ProdConfig as Config
import csv
import json
import os

# --- Odoo Connection Details ---
# Replace with your Odoo instance details

# --- Output File Names ---
OUTPUT_CSV_FILE = 'inventory_serials.csv'
OUTPUT_JSON_FILE = 'inventory_serials.json'

def get_config() -> Config:
    the_config = Config()
    print(the_config)
    return the_config



def export_inventory_with_serials(cfg:Config):
    """
    Connects to Odoo, fetches inventory items tracked by serial numbers,
    and exports their details including product, serial, quantity, and location.
    """
    print(f"Connecting to Odoo at {cfg.HOST} (Database: {cfg.DB})...")
    try:
        # Authenticate and get UID
        common = xmlrpc.client.ServerProxy(f'{cfg.HOST}/xmlrpc/2/common')
        uid = common.authenticate(cfg.DB, cfg.USER_EMAIL, cfg.API_KEY, {})
        if not uid:
            print("Authentication failed. Check your Odoo URL, DB, username, and password.")
            return

        print(f"Authentication successful. User ID: {uid}")

        # Get the object proxy for models
        models = xmlrpc.client.ServerProxy(f'{cfg.HOST}/xmlrpc/2/object')

        # --- 1. Find all serial numbers (stock.production.lot records) ---
        # We filter for serial numbers that are currently 'available' (not consumed)
        # and ideally linked to products tracked by unique serial number.
        # The 'product_id.tracking' field is not directly accessible in search for stock.production.lot,
        # so we'll filter by product tracking type after reading.
        print("Searching for all active serial numbers...")
        serial_lot_ids = models.execute_kw(
            cfg.DB, uid, cfg.API_KEY,
            'stock.production.lot', 'search',
            [[('active', '=', True)]]  # Get all active lots/serials
        )

        if not serial_lot_ids:
            print("No active serial numbers found in Odoo.")
            return

        print(f"Found {len(serial_lot_ids)} active serial numbers. Reading details...")

        # --- 2. Read details of the serial numbers ---
        # Include fields to get product, quantity, and location information.
        # 'product_id': The product linked to this serial.
        # 'product_qty': The quantity of this lot/serial (should be 1 for serials).
        # 'quant_ids': One2many field linking to stock.quant records (actual inventory quantities).
        fields_to_read = [
            'name',  # The serial number itself
            'product_id',  # Product (will return [ID, Name])
            'product_qty',  # Quantity (should be 1 for serials)
            'quant_ids',  # Link to actual stock quantities for location info
            'display_name',  # Full display name of the lot/serial
        ]

        serials_data = models.execute_kw(
            cfg.DB, uid, cfg.API_KEY,
            'stock.production.lot', 'read',
            [serial_lot_ids],
            {'fields': fields_to_read}
        )

        processed_inventory_data = []

        # --- 3. Process and Filter for Serialized Products and their Quants ---
        print("Processing serial number data and associated inventory quants...")
        for serial_lot in serials_data:
            product_id = serial_lot['product_id'][0]
            product_name = serial_lot['product_id'][1]
            serial_number = serial_lot['name']

            # Verify product is tracked by serial number (important filter)
            product_tracking = models.execute_kw(
                cfg.DB, uid, cfg.API_KEY,
                'product.product', 'read',
                [product_id],
                {'fields': ['tracking']}
            )[0]['tracking']

            if product_tracking != 'serial':
                # print(f"  Skipping '{product_name}' (Serial: {serial_number}) as it's not tracked by unique serial number.")
                continue  # Skip if not a serial-tracked product

            # Get the actual inventory quantities (quants) for this serial number
            if serial_lot['quant_ids']:
                quant_fields = ['quantity', 'location_id', 'product_id', 'lot_id']
                quants_data = models.execute_kw(
                    cfg.DB, uid, cfg.API_KEY,
                    'stock.quant', 'read',
                    [serial_lot['quant_ids']],
                    {'fields': quant_fields}
                )

                for quant in quants_data:
                    # Filter for positive quantities in internal locations
                    if quant['quantity'] > 0 and models.execute_kw(
                            cfg.DB, uid, cfg.API_KEY,
                            'stock.location', 'read',
                            [quant['location_id'][0]],
                            {'fields': ['usage']}
                    )[0]['usage'] == 'internal':
                        processed_inventory_data.append({
                            'Product_Name': product_name,
                            'Product_ID': product_id,
                            'Serial_Number': serial_number,
                            'Quantity_On_Hand': quant['quantity'],  # Should be 1 for serials
                            'Location': quant['location_id'][1],  # Location name
                            'Location_ID': quant['location_id'][0],
                            'Lot_ID': serial_lot['id']  # Odoo's internal ID for the serial
                        })
            else:
                # If a serial number exists but has no quants, it might be out of stock or in a virtual location
                # You might choose to include these with 0 quantity or skip them.
                # For this script, we only include if there's a positive quantity in an internal location.
                pass

        if not processed_inventory_data:
            print("No inventory items with serial numbers found in stock.")
            return

        print(f"Found {len(processed_inventory_data)} serialized inventory items in stock.")

        # --- 4. Export to CSV ---
        csv_headers = [
            'Product_Name', 'Product_ID', 'Serial_Number',
            'Quantity_On_Hand', 'Location', 'Location_ID', 'Lot_ID'
        ]

        with open(OUTPUT_CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
            writer.writeheader()
            writer.writerows(processed_inventory_data)
        print(f"Data successfully exported to {OUTPUT_CSV_FILE}")

        # --- 5. Export to JSON ---
        with open(OUTPUT_JSON_FILE, 'w', encoding='utf-8') as jsonfile:
            json.dump(processed_inventory_data, jsonfile, indent=4, ensure_ascii=False)
        print(f"Data successfully exported to {OUTPUT_JSON_FILE}")

    except xmlrpc.client.Fault as err:
        print(f"XML-RPC Fault: {err.faultCode} - {err.faultString}")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    config = get_config()
    export_inventory_with_serials(config)