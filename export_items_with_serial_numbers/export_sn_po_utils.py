import xmlrpc.client
from ProdConfig import ProdConfig as Config
import csv
import json


def export_serial_number_products(models, uid:int, config:Config):
    """
    this returns exported_data associate d with products with serial numbers. But why do different products have the same serial numbers?
    :param models:
    :param uid:
    :param config:
    """
    lots_data = []
    try:
        # Example: Get all serial numbers
        lot_ids = models.execute_kw(config.DB, uid, config.API_KEY,
                                    'stock.lot', 'search',
                                    [[]])  # No specific domain, fetches all
        # Get the object proxy for models
        lots_data = models.execute_kw(config.DB, uid, config.API_KEY,
                                      'stock.lot', 'read',
                                      [lot_ids],
                                      {'fields': ['name', 'product_id', 'id']})
    except xmlrpc.client.Fault as err:
        print(f"XML-RPC Fault: {err.faultCode} - {err.faultString}")
        lots_data = []
    except Exception as e:
        lots_data = []
        print(f"An error occurred: {e}")

    return lots_data

def export_po_data(models, uid, config:Config, lots_data):
    """
    This takes lots_data, from the export_serial_numbers_products and returns an array of serial numbers with associated purchase order exported_data.
    It does this mainly in the following steps.
    1. For each lot in lots_data,
        a. Get the move_line_ids associated with this lot. This is done with the get_move_line_info_from_lot() function.
        b. Get po exported_data from move_line_info and lot info using the get_serial_data_from_lot_and_move_line () function.

    :param models:
    :param uid:
    :param config:
    :param lots_data:
    :return: an array of {'serial_number': 'XX',
                          'product_name':'YY',
                          'product_id': 123,
                          'purchase_order_name': 'ZZ',
                          'purchase_order_id': 456,
                          'picking_type': 'AA',
                          'quantity': 1 }
    """
    serial_data_with_po = []
    try:
        for lot in lots_data:
            # Find stock.move.line records associated with this lot/serial
            move_lines_info = get_move_line_info_from_lot(lot, models, uid, config)

            for ml in move_lines_info:
                serial_data =  get_serial_data_from_lot_and_move_line(lot, ml, models, uid, config)
                if serial_data:
                    serial_data_with_po.append(serial_data)
                else:
                    print(f"No serial exported_data found for lot {lot['name']}.")

    except xmlrpc.client.Fault as err:
        print(f"XML-RPC Fault: {err.faultCode} - {err.faultString}")
        serial_data_with_po= []
    except Exception as e:
        serial_data_with_po= []
        print(f"An error occurred: {e}")

    return serial_data_with_po



def get_move_line_info_from_lot(lot, models, uid, config):
    """

    :param lot:
    :param models:
    :param uid:
    :param config:
    :return: an array of [{'id': (int) 131, 'name': (str)''APSIGeoS_2023-003-001'', 'product_id': list[(int), (str)]}]
    """
    move_line_ids = models.execute_kw(config.DB, uid, config.API_KEY,
                                      'stock.move.line', 'search',
                                      [[('lot_id', '=', lot['id'])]])
    if move_line_ids:
        move_lines_info = models.execute_kw(config.DB, uid, config.API_KEY,
                                            'stock.move.line', 'read',
                                            [move_line_ids],
                                            {'fields': ['picking_id', 'product_id', 'qty_done']})
        return move_lines_info
    else:
        return False



def get_serial_data_from_lot_and_move_line(lot, ml, models, uid, config):
    picking_id = ml['picking_id'][0]  # picking_id is a many2one field (id, name)

    # Get picking details
    picking_info = models.execute_kw(config.DB, uid, config.API_KEY,
                                 'stock.picking', 'read',
                                 [[picking_id]],
                                 {'fields': ['origin',
                                             'purchase_id']})  # 'origin' often holds the PO name, 'purchase_id' links to PO

    result = {}
    if picking_info and picking_info[0]['purchase_id']:
        po_id = picking_info[0]['purchase_id'][0]
        po_name = picking_info[0]['purchase_id'][1]  # (id, name) for purchase_id

        # Optionally, fetch more PO details if needed
        # po_details = models.execute_kw(db, uid, password,
        # 'purchase.order', 'read',
        #     [[po_id]],
        #       {'fields': ['name', 'partner_id', 'date_order']})

        result = {
            'serial_number': lot['name'],
            'product_name': lot['product_id'][1],  # (id, name)
            'product_id': lot['product_id'][0],
            'purchase_order_name': po_name,
            'purchase_order_id': po_id,
            'picking_type': picking_info[0]['origin'],  # This often contains the PO reference
            'quantity': ml['qty_done']
        }
    return result


def export_to_csv_json(data):
    """

    :param data: an array of {'serial_number': 'XX',
                              'product_name':'YY',
                              'product_id': 123,
                              'purchase_order_name': 'ZZ',
                              'purchase_order_id': 456,
                              'picking_type': 'AA',
                              'quantity': 1 }
    :return:Nothing.
    """
    OUTPUT_CSV_FILE = 'product_sn_po.csv'
    OUTPUT_JSON_FILE = 'product_sn_po.json'

    if len(data) == 0:
        print("No inventory items with serial numbers found in stock.")
        return

    print(f"Found {len(data)} serialized inventory items in stock.")

    # --- 4. Export to CSV ---
    csv_headers = [
        'serial_number', 'product_name', 'product_id', 'purchase_order_name',
        'purchase_order_id', 'picking_type', 'quantity'
    ]

    with open(OUTPUT_CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_headers, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)
    print(f"Data successfully exported to {OUTPUT_CSV_FILE}")

    # --- 5. Export to JSON ---
    with open(OUTPUT_JSON_FILE, 'w', encoding='utf-8') as jsonfile:
        json.dump(data, jsonfile, indent=4, ensure_ascii=False)
    print(f"Data successfully exported to {OUTPUT_JSON_FILE}")
