
import xmlrpc.client
from StageConfig import StageConfig as Config
from import_po_accept_fns import import_all_pos


def receive_purchase_order_items(purchase_order_id, serial_numbers_by_product):
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
        picking_ids = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                                        'stock.picking', 'search',
                                        [[('purchase_id', '=', purchase_order_id),
                                          ('state', 'in', ['assigned', 'waiting', 'confirmed'])]])
        if not picking_ids:
            print(f"No incoming picking found for Purchase Order {purchase_order_id}")
            return False

        picking_id = picking_ids[0]
        print(f"Found incoming picking ID: {picking_id} for PO {purchase_order_id}")

        # Get the move lines of the picking
        picking_data = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                                         'stock.picking', 'read',
                                         [picking_id], {'fields': ['move_ids_without_package']})[0]
        move_ids = picking_data['move_ids_without_package']

        if not move_ids:
            print(f"No stock moves found for picking {picking_id}")
            return False

        # Get the move line details for each product in the picking
        move_lines = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
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
                models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                                  'stock.move.line', 'unlink',
                                  [move_line['id']])

                # Create new move lines, one for each serial number
                for sn in serial_numbers:
                    updated_move_line_vals.append((0, 0, {
                        'picking_id': picking_id,
                        'product_id': product_id,
                        'product_uom_id': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                                                            'product.product', 'read',
                                                            [product_id], {'fields': ['uom_id']})[0]['uom_id'][0],
                        'qty_done': 1,  # Each serial number is 1 unit
                        'lot_name': sn,  # Assign the serial number
                        'location_id': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                                                         'stock.picking', 'read',
                                                         [picking_id], {'fields': ['location_id']})[0]['location_id'][
                            0],
                        'location_dest_id': models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                                                              'stock.picking', 'read',
                                                              [picking_id], {'fields': ['location_dest_id']})[0][
                            'location_dest_id'][0],
                    }))
            else:
                # For non-serialized products or products not provided with serial numbers
                # simply set qty_done for the existing move line
                updated_move_line_vals.append((1, move_line['id'], {'qty_done': required_qty}))

        # Update the picking to include the new/updated move lines
        models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                          'stock.picking', 'write',
                          [[picking_id], {'move_line_ids_without_package': updated_move_line_vals}])

        print(f"Updated picking {picking_id} with quantities and serial numbers.")

        # Validate the picking (mark as done)
        models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
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