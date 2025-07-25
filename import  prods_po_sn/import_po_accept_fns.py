import xmlrpc.client
from typing import List,Dict
from StageConfig import StageConfig as Config
import json


PRODUCTS_FILE = "exported_data/all_products.json"
PO_FILE = "exported_data/purchase_orders.json"
SN_PO_FILE = "exported_data/product_sn_po.json"


def load_json_file(filename, key_field) -> Dict:
    """
    This opens the json file,filename, and creates a Dict with the key being key_field.
    :param filename: the filename of the json file
    :param key_field: the field of the objects that will be used as the key of the Dict.
    :return: A Dict with the key being key_field, and values the objects in the file.
    """
    temp_list = []
    result_dict = {}
    with open(filename, "r") as f:
        temp_list = json.load(f)
    for item in temp_list:
        result_dict[item[key_field]] = item
    return result_dict


def get_partner_id_from_temp_po(models, uid: int, config: Config, temp_po):
    vendor = temp_po['Vendor']
    partner_model = 'res.partner'
    vendor_ids = models.execute_kw(config.DB, uid, config.API_KEY, partner_model, 'search',
                                   [[('name', '=', vendor)]], {'limit': 1})
    vendor_id = vendor_ids[0]
    print(f"Vendor: {vendor} has ID: {vendor_id}")
    return vendor_id


def get_user_id_from_temp_po(models, uid: int, config: Config, temp_po):
    user = temp_po['Purchase_Representative']
    user_model = 'res.users'
    user_ids = models.execute_kw(config.DB, uid, config.API_KEY, user_model, 'search',
                                   [[('name', '=', user)]], {'limit': 1})
    user_id = user_ids[0]
    print(f"User: {user} has ID: {user_id}")
    return user_id


def get_currency_id_from_temp_po(models, uid: int, config: Config, temp_po):
    currency = temp_po['Currency']
    currency_model = 'res.currency'
    currency_id = models.execute_kw(config.DB, uid, config.API_KEY, 'res.currency', 'search',
                                  [[('name', '=', currency)]], {'limit': 1})[0]
    print(f"Currency: {currency} has ID: {currency_id}")
    return currency_id


def get_product_name_from_template(product_template):
    products_dict = load_json_file(PRODUCTS_FILE, "Product_Template")
    product_name = products_dict.get(product_template)['Product_Name']
    # print(f"Product Template: {product_template} has name: {product_name}")
    return product_name



def get_product_id_from_order_line(models, uid: int, config: Config, temp_po):
    product_template = temp_po['product_name']
    product_name = get_product_name_from_template(product_template)

    product_model = 'product.product'
    product_ids = models.execute_kw(config.DB, uid, config.API_KEY, product_model, 'search',
                                    [[('name', '=', product_name)]], {'limit': 1})
    if product_ids:
        product_id = product_ids[0]
        # print(f"Product: {product_name} has ID: {product_id}")
        return product_id
    else:
        raise Exception(f"Product {product_name} not found")


def convert_to_po(models, uid: int, config: Config, temp_po):

    # Create order_lines from temp_po first.
    order_lines = []
    temp_po_order_lines = temp_po['Order_Lines']
    for item in temp_po_order_lines:
        order_lines.append((0, 0, {
            'product_id': get_product_id_from_order_line(models, uid, config, item),
            'product_qty': item['quantity'],
            'price_unit': item['unit_price'],
            'date_planned': temp_po['Order_Date'],
        }))

    po = {
        'name': temp_po['PO_Reference'],
        'date_order': temp_po['Order_Date'],
        'partner_id': get_partner_id_from_temp_po(models, uid, config, temp_po),
        'currency_id': get_currency_id_from_temp_po(models, uid, config, temp_po),
        'order_line': order_lines,
        'user_id': get_user_id_from_temp_po(models, uid, config, temp_po),
        'state': 'draft'
    }
    return po


def import_po(models, uid: int, config: Config, po):
    purchase_order_id = models.execute_kw(config.DB, uid, config.API_KEY,
                                          'purchase.order', 'create', [po])
    print(f"Purchase Order created with ID: {purchase_order_id}")
    po['purchase_order_id'] = purchase_order_id
    return po


def import_all_pos(models, uid, config: Config):
    OUTPUT_JSON_FILE = f'accepted_pos.json'
    po_dict = load_json_file(PO_FILE, "PO_Reference")
    imported_pos = []
    for i, temp_po_key in enumerate(po_dict.keys()):
        temp_po = po_dict[temp_po_key]
        po = convert_to_po(models, uid, config,temp_po)
        accepted_po = import_po(models, uid, config, po)
        print(f"Imported PO #{i}: {accepted_po['purchase_order_id']}")
        imported_pos.append(accepted_po)
    with open(OUTPUT_JSON_FILE, 'w', encoding='utf-8') as jsonfile:
        json.dump(imported_pos, jsonfile, indent=4, ensure_ascii=False)
    print( 'Done')





def create_purchase_order(models, uid: int, config: Config, vendor_id, po):
    pass


