import xmlrpc.client
from StageConfig import StageConfig as Config


def create_purchase_order(models, uid: int, config:Config, vendor_id, product_data):
    """
    Creates a purchase order in Odoo.

    Args:
        vendor_id (int): The Odoo ID of the vendor (res.partner).
        product_data (list of dict): List of dictionaries, each containing:
                                    - 'product_id': Odoo ID of the product
                                    - 'product_qty': Quantity to order
                                    - 'price_unit': Price per unit
    Returns:
        int: The ID of the created purchase order, or None if failed.
    """
    order_lines = []
    for product in product_data:
        order_lines.append((0, 0, {
            'product_id': product['product_id'],
            'product_qty': product['product_qty'],
            'price_unit': product['price_unit'],
            'name': models.execute_kw(config.DB, uid, config.API_KEY,
                                     'product.product', 'read',
                                     [product['product_id']], {'fields': ['name']})[0]['name'],
        }))

    try:
        purchase_order_id = models.execute_kw(config.DB, uid, config.API_KEY,
                                              'purchase.order', 'create', [{
                                                  'partner_id': vendor_id,
                                                  'order_line': order_lines,
                                                  'state': 'draft', # Start in draft, then confirm
                                              }])
        print(f"Purchase Order created with ID: {purchase_order_id}")

        # Confirm the purchase order
        models.execute_kw(config.DB, uid, config.API_KEY,
                          'purchase.order', 'button_confirm',
                          [purchase_order_id])
        print(f"Purchase Order {purchase_order_id} confirmed.")
        return purchase_order_id
    except xmlrpc.client.Fault as err:
        print(f"Error creating/confirming Purchase Order: {err.faultCode} - {err.faultString}")
        return None

# Example Usage:
# Find a vendor and product IDs first (replace with actual IDs from your Odoo)
# You can use models.execute_kw with 'search_read' to find existing records.
# For example:
# vendor_id = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'res.partner', 'search',
#                               [['name', '=', 'Your Vendor Name']], limit=1)[0]
# product_id = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'product.product', 'search',
#                                [['name', '=', 'Your Product Name']], limit=1)[0]

# For this example, let's assume you have these IDs:
# EXAMPLE_VENDOR_ID = 1 # Replace with an actual vendor ID
# EXAMPLE_PRODUCT_ID_SERIAL = 2 # Replace with a product ID tracked by serial numbers

# Data for the purchase order
# po_products = [
#     {'product_id': EXAMPLE_PRODUCT_ID_SERIAL, 'product_qty': 3, 'price_unit': 100.00},
# ]

# created_po_id = create_purchase_order(EXAMPLE_VENDOR_ID, po_products)
# if created_po_id:
#     print(f"Successfully created and confirmed Purchase Order {created_po_id}")






def receive_purchase_order_items(models, uid:int, config: Config, purchase_order_id, serial_numbers_by_product):
    """
    Receives items for a given purchase order and assigns serial numbers.

    Args:
        purchase_order_id (int): The ID of the purchase order.
        serial_numbers_by_product (dict): A dictionary where keys are product IDs
                                          and values are lists of serial numbers
                                          to assign for that product.
                                          Example: {product_id_1: ['SN001', 'SN002'], ...}
    Returns:
        bool: True if reception and serial number assignment were successful, False otherwise.
    """
    try:
        # Find the incoming picking related to the purchase order
        picking_ids = models.execute_kw(config.DB, uid, config.API_KEY,
                                        'stock.picking', 'search',
                                        [[('purchase_id', '=', purchase_order_id),
                                          ('state', 'in', ['assigned', 'waiting', 'confirmed'])]])
        if not picking_ids:
            print(f"No incoming picking found for Purchase Order {purchase_order_id}")
            return False

        picking_id = picking_ids[0]
        print(f"Found incoming picking ID: {picking_id} for PO {purchase_order_id}")

        # Get the move lines of the picking
        picking_data = models.execute_kw(config.DB, uid, config.API_KEY,
                                         'stock.picking', 'read',
                                         [picking_id], {'fields': ['move_ids_without_package']})[0]
        move_ids = picking_data['move_ids_without_package']

        if not move_ids:
            print(f"No stock moves found for picking {picking_id}")
            return False

        # Get the move line details for each product in the picking
        move_lines = models.execute_kw(config.DB, uid, config.API_KEY,
                                       'stock.move.line', 'search_read',
                                       [[('picking_id', '=', picking_id)]],
                                       {'fields': ['product_id', 'qty_done', 'product_uom_qty', 'lot_id', 'lot_name']})

        # Prepare updates for move lines
        updated_move_line_vals = []
        for move_line in move_lines:
            product_id = move_line['product_id'][0]
            required_qty = move_line['product_uom_qty']

            if product_id in serial_numbers_by_product:
                serial_numbers = serial_numbers_by_product[product_id]
                if len(serial_numbers) != required_qty:
                    print(
                        f"Warning: Number of serial numbers provided for product {product_id} ({len(serial_numbers)}) "
                        f"does not match required quantity ({required_qty}).")

                # Odoo 18 allows assigning serial numbers directly on move lines during reception.
                # For each unit of a serialized product, you create a separate stock.move.line
                # and assign a serial number to it.

                # First, unlink existing move lines for this product on this picking (if any)
                # to allow creating new ones with serial numbers. This is a common pattern for serialized products.
                models.execute_kw(config.DB, uid, config.API_KEY,
                                  'stock.move.line', 'unlink',
                                  [move_line['id']])

                # Create new move lines, one for each serial number
                for sn in serial_numbers:
                    updated_move_line_vals.append((0, 0, {
                        'picking_id': picking_id,
                        'product_id': product_id,
                        'product_uom_id': models.execute_kw(config.DB, uid, config.API_KEY,
                                                            'product.product', 'read',
                                                            [product_id], {'fields': ['uom_id']})[0]['uom_id'][0],
                        'qty_done': 1,  # Each serial number is 1 unit
                        'lot_name': sn,  # Assign the serial number
                        'location_id': models.execute_kw(config.DB, uid, config.API_KEY,
                                                         'stock.picking', 'read',
                                                         [picking_id], {'fields': ['location_id']})[0]['location_id'][
                            0],
                        'location_dest_id': models.execute_kw(config.DB, uid, config.API_KEY,
                                                              'stock.picking', 'read',
                                                              [picking_id], {'fields': ['location_dest_id']})[0][
                            'location_dest_id'][0],
                    }))
            else:
                # For non-serialized products or products not provided with serial numbers
                # simply set qty_done for the existing move line
                updated_move_line_vals.append((1, move_line['id'], {'qty_done': required_qty}))

        # Update the picking to include the new/updated move lines
        models.execute_kw(config.DB, uid, config.API_KEY,
                          'stock.picking', 'write',
                          [[picking_id], {'move_line_ids_without_package': updated_move_line_vals}])

        print(f"Updated picking {picking_id} with quantities and serial numbers.")

        # Validate the picking (mark as done)
        models.execute_kw(config.DB, uid, config.API_KEY,
                          'stock.picking', 'button_validate',
                          [picking_id])
        print(f"Picking {picking_id} validated successfully. Items received.")
        return True

    except xmlrpc.client.Fault as err:
        print(f"Error receiving items or assigning serial numbers: {err.faultCode} - {err.faultString}")
        return False

# Example Usage:
# if created_po_id:
#     # Assuming EXAMPLE_PRODUCT_ID_SERIAL needs 3 serial numbers
#     serial_numbers_for_po = {
#         EXAMPLE_PRODUCT_ID_SERIAL: ['SN-PO-001', 'SN-PO-002', 'SN-PO-003']
#     }
#     receive_purchase_order_items(created_po_id, serial_numbers_for_po)

