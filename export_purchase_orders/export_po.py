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

OUTPUT_CSV_FILE = 'purchase_orders.csv'
OUTPUT_JSON_FILE = 'purchase_orders.json'
def export_purchase_orders(config:Config):
    """
    Connects to Odoo, fetches purchase orders, and exports them to CSV and JSON.
    """
    print(f"Connecting to Odoo at {config.HOST} (Database: {config.DB}, Username:)...")
    try:
        # Authenticate and get UID
        common = xmlrpc.client.ServerProxy(f'{config.HOST}/xmlrpc/2/common')
        uid = common.authenticate(config.DB, config.USER_EMAIL, config.API_KEY, {})
        if not uid:
            print("Authentication failed. Check your Odoo URL, DB, username, and password.")
            return

        print(f"Authentication successful. User ID: {uid}")

        # Get the object proxy for the 'purchase.order' model
        models = xmlrpc.client.ServerProxy(f'{config.HOST}/xmlrpc/2/object')

        # --- 1. Define Search Domain (Filters) ---
        # Example: Fetch all confirmed purchase orders
        # For more filters, refer to Odoo's domain syntax:
        #   [('field_name', 'operator', value)]
        # Examples:
        #   [('state', '=', 'purchase')]  # Only confirmed POs
        #   [('create_date', '>=', '2024-01-01')] # POs created after a specific date
        #   [('partner_id.name', 'ilike', 'Acme')] # POs from partners with 'Acme' in their name
        domain = [('state', '=', 'purchase')]

        # --- 2. Define Fields to Read ---
        # Specify the fields you want to export.
        # For many2one fields (like partner_id), you can append '.name' to get the name,
        # or just 'partner_id' to get the ID and name as a tuple (ID, Name).
        # For one2many/many2many fields (like order_line), you'll typically need to
        # make a separate read call or specify sub-fields.
        fields_to_read = [
            'name',             # Purchase Order Reference
            'date_order',       # Order Date
            'partner_id',       # Vendor (will return [ID, Name])
            'amount_total',     # Total Amount
            'currency_id',      # Currency (will return [ID, Name])
            'state',            # State of the PO (e.g., 'draft', 'sent', 'purchase', 'done')
            'user_id',          # Purchase Representative (will return [ID, Name])
            'order_line',       # Purchase Order Lines (one2many field)
        ]

        print(f"Searching for Purchase Orders with domain: {domain}...")
        # --- 3. Search for Purchase Orders ---
        # 'execute_kw' is used for calling methods on models.
        # Arguments: db_name, uid, password, model_name, method_name, args, kwargs
        po_ids = models.execute_kw(
            config.DB, uid, config.API_KEY,
            'purchase.order', 'search',
            [domain]
        )

        if not po_ids:
            print("No Purchase Orders found matching the criteria.")
            return

        print(f"Found {len(po_ids)} Purchase Orders. Reading details...")

        # --- 4. Read Purchase Order Data ---
        # Read the specified fields for the found PO IDs
        purchase_orders_data = models.execute_kw(
            config.DB, uid, config.API_KEY,
            'purchase.order', 'read',
            [po_ids],
            {'fields': fields_to_read}
        )

        # --- Process and Prepare Data for Export ---
        processed_data = []
        for po in purchase_orders_data:
            # Extract names for many2one fields
            vendor_name = po['partner_id'][1] if po['partner_id'] else ''
            currency_name = po['currency_id'][1] if po['currency_id'] else ''
            representative_name = po['user_id'][1] if po['user_id'] else ''

            # Fetch details for order lines (one2many)
            order_lines_details = []
            if po['order_line']:
                line_ids = po['order_line']
                line_fields = ['product_id', 'name', 'product_qty', 'price_unit', 'price_subtotal']
                lines_data = models.execute_kw(
                    config.DB, uid, config.API_KEY,
                    'purchase.order.line', 'read',
                    [line_ids],
                    {'fields': line_fields}
                )
                for line in lines_data:
                    order_lines_details.append({
                        'product_name': line['product_id'][1] if line['product_id'] else '',
                        'description': line['name'],
                        'quantity': line['product_qty'],
                        'unit_price': line['price_unit'],
                        'subtotal': line['price_subtotal'],
                    })

            processed_po = {
                'PO_Reference': po['name'],
                'Order_Date': po['date_order'],
                'Vendor': vendor_name,
                'Total_Amount': po['amount_total'],
                'Currency': currency_name,
                'State': po['state'],
                'Purchase_Representative': representative_name,
                'Order_Lines': order_lines_details, # Nested data for JSON
            }
            processed_data.append(processed_po)

        # --- 5. Export to CSV ---
        if processed_data:
            # Define CSV headers. For simplicity, we'll flatten order lines for CSV.
            # You might need a more sophisticated flattening or separate CSVs for lines.
            csv_headers = [
                'PO_Reference', 'Order_Date', 'Vendor', 'Total_Amount',
                'Currency', 'State', 'Purchase_Representative',
                'Line_Product', 'Line_Description', 'Line_Quantity', 'Line_Unit_Price', 'Line_Subtotal'
            ]

            with open(OUTPUT_CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(csv_headers) # Write header row

                for po in processed_data:
                    if po['Order_Lines']:
                        for line in po['Order_Lines']:
                            writer.writerow([
                                po['PO_Reference'], po['Order_Date'], po['Vendor'], po['Total_Amount'],
                                po['Currency'], po['State'], po['Purchase_Representative'],
                                line['product_name'], line['description'], line['quantity'],
                                line['unit_price'], line['subtotal']
                            ])
                    else: # Handle POs with no lines (unlikely for POs, but good practice)
                        writer.writerow([
                            po['PO_Reference'], po['Order_Date'], po['Vendor'], po['Total_Amount'],
                            po['Currency'], po['State'], po['Purchase_Representative'],
                            '', '', '', '', '' # Empty columns for line details
                        ])
            print(f"Data successfully exported to {OUTPUT_CSV_FILE}")

        # --- 6. Export to JSON ---
        with open(OUTPUT_JSON_FILE, 'w', encoding='utf-8') as jsonfile:
            json.dump(processed_data, jsonfile, indent=4, ensure_ascii=False)
        print(f"Data successfully exported to {OUTPUT_JSON_FILE}")

    except xmlrpc.client.Fault as err:
        print(f"XML-RPC Fault: {err.faultCode} - {err.faultString}")
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    config = get_config()
    uid = get_rpc_info(config)
    print(f"uid:{uid}")
    export_purchase_orders(config)

if __name__ == "__main__":
    main()