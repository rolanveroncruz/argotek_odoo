import xmlrpc.client
from ProdConfig import ProdConfig as Config
import csv
import json

def get_config() -> Config:
    config = Config()
    print(config)
    return config

def get_rpc_info(config:Config)-> int:
    info = xmlrpc.client.ServerProxy(f"{config.HOST}/xmlrpc/2/common")
    print(f"version:{info.version()}")
    print(f"authenticating...")
    print(f"user:{config.USER_EMAIL}, api_key:{config.API_KEY}")
    uid = info.authenticate(config.DB, config.USER_EMAIL, config.API_KEY, {})
    return uid

def import_purchase_orders(config:Config):
    """
    Connects to Odoo and creates a Purchase Order with its lines.

    Args:
        po_data (dict): A dictionary containing PO header and line details.
                        Example structure:
                        {
                            'vendor_name': 'Azure Interior',
                            'order_date': '2025-07-18',
                            'currency_name': 'USD',
                            'state': 'purchase', # 'draft', 'sent', 'purchase', 'done', 'cancel'
                            'order_lines': [
                                {
                                    'product_name': 'Customizable Desk (Custom, White)',
                                    'product_qty': 2.0,
                                    'price_unit': 750.0,
                                    'product_uom_name': 'Units' # Optional, will use product's default if not provided
                                },
                                {
                                    'product_name': 'Office Chair',
                                    'product_qty': 5.0,
                                    'price_unit': 120.0,
                                    'product_uom_name': 'Units'
                                }
                            ]
                        }
    """
    print(f"Connecting to Odoo at {config.HOST} (Database: {config.DB})...")
    try:
        # Authenticate and get UID
        common = xmlrpc.client.ServerProxy(f'{config.HOST}/xmlrpc/2/common')
        uid = common.authenticate(config.DB, config.USER_EMAIL, config.API_KEY, {})
        if not uid:
            print("Authentication failed. Check your Odoo URL, DB, username, and password.")
            return None

        print(f"Authentication successful. User ID: {uid}")

        # Get the object proxy for models
        models = xmlrpc.client.ServerProxy(f'{config.HOST}/xmlrpc/2/object')

        # --- 1. Get IDs for related records (Vendor, Currency, Products, UoM) ---

        # Get Vendor ID
        vendor_id = models.execute_kw(
            config.DB, uid, config.API_KEY,
            'res.partner', 'search',
            [[('name', '=', po_data['vendor_name'])]]
        )
        if not vendor_id:
            print(f"Error: Vendor '{po_data['vendor_name']}' not found in Odoo.")
            return None
        vendor_id = vendor_id[0]  # Get the first ID if multiple found

        # Get Currency ID
        currency_id = models.execute_kw(
            config.DB, uid, config.API_KEY,
            'res.currency', 'search',
            [[('name', '=', po_data['currency_name'])]]
        )
        if not currency_id:
            print(f"Error: Currency '{po_data['currency_name']}' not found or not active in Odoo.")
            return None
        currency_id = currency_id[0]

        # --- 2. Prepare Purchase Order Header Data ---
        po_header_vals = {
            'partner_id': vendor_id,
            'date_order': po_data.get('order_date', xmlrpc.client.DateTime(xmlrpc.client.datetime.now())),
            'currency_id': currency_id,
            'state': po_data.get('state', 'draft'),  # Default to 'draft' if not specified
        }

        print(f"Creating Purchase Order for vendor '{po_data['vendor_name']}'...")
        # --- 3. Create the Purchase Order Header ---
        po_id = models.execute_kw(
            config.DB, uid, config.API_KEY,
            'purchase.order', 'create',
            [po_header_vals]
        )

        if not po_id:
            print("Failed to create Purchase Order header.")
            return None

        print(f"Purchase Order header created with ID: {po_id}")

        # --- 4. Prepare and Create Purchase Order Lines ---
        order_line_commands = []
        for line_data in po_data['order_lines']:
            product_id = models.execute_kw(
                config.DB, uid, config.API_KEY,
                'product.product', 'search',
                [[('name', '=', line_data['product_name'])]]
            )
            if not product_id:
                print(f"Warning: Product '{line_data['product_name']}' not found. Skipping this line.")
                continue
            product_id = product_id[0]

            # Get default Unit of Measure for the product
            product_uom_id = models.execute_kw(
                config.DB, uid, config.API_KEY,
                'product.product', 'read',
                [product_id],
                {'fields': ['uom_po_id']}  # uom_po_id is the purchase UoM
            )[0]['uom_po_id'][0]  # [0] for the first record, [0] for the ID in the tuple

            # If a specific UoM name is provided in line_data, try to find it
            if 'product_uom_name' in line_data and line_data['product_uom_name']:
                custom_uom_id = models.execute_kw(
                    config.DB, uid, config.API_KEY,
                    'uom.uom', 'search',
                    [[('name', '=', line_data['product_uom_name'])]]
                )
                if custom_uom_id:
                    product_uom_id = custom_uom_id[0]
                else:
                    print(
                        f"Warning: Unit of Measure '{line_data['product_uom_name']}' not found. Using product's default.")

            # Create command for adding a new line
            # (0, 0, {values}) creates a new record linked to the parent
            order_line_commands.append(
                (0, 0, {
                    'product_id': product_id,
                    'name': line_data.get('description', line_data['product_name']),
                    # Use product name as default description
                    'product_qty': line_data['product_qty'],
                    'price_unit': line_data['price_unit'],
                    'product_uom': product_uom_id,  # Use the determined UoM ID
                    'order_id': po_id,  # Link to the created PO
                })
            )

        if order_line_commands:
            # Update the purchase order with its lines
            models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'purchase.order', 'write',
                [[po_id], {'order_line': order_line_commands}]
            )
            print(f"Purchase Order {po_id} lines added successfully.")
        else:
            print(f"No valid lines to add for Purchase Order {po_id}.")

        print(f"Successfully created Purchase Order: {po_id} (Ref: {po_header_vals['name']})")
        return po_id

    except xmlrpc.client.Fault as err:
        print(f"XML-RPC Fault: {err.faultCode} - {err.faultString}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None





def main():
    config = get_config()
    uid = get_rpc_info(config)
    print(f"uid:{uid}")
    import_purchase_orders(config)

if __name__ == "__main__":
    main()