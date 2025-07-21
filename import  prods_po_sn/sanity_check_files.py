"""
We've exported data into 3 files:
1. all_products.json - for the products in Inventory->Products->Products. Important Info:Products.
2. purchase_orders.json - for the purchase orders in Purchase->Purchase Order. Important Info: PO and Items in PO.
3. inventory_prod_sn_po.csv - for the serial numbers and purchase order exported_data. Important Info: Products and PO.

We want to do a sanity check that these are consistent.
Specifically:
1. Check that every item in a purchase order is a product.(#2 & #1)
2. Every purchase order in the inventory_prod_sn_po.csv file should have a purchase order
in the purchase_orders.json file.(#3 and #2)
3. Every product in the inventory_prod_sn_po.json file has its product in the all_products.json file. (#3 and #1)


All 3 tests passed.
"""
import json
PRODUCTS_FILE = "exported_data/all_products.json"
PO_FILE = "exported_data/purchase_orders.json"
SN_PO_FILE = "exported_data/product_sn_po.json"


def load_json_file(file_name, key_field):
    temp_list = []
    result_dict = {}
    with open(file_name, "r") as f:
        temp_list = json.load(f)
    for item in temp_list:
        result_dict[item[key_field]] = item
    return result_dict


def check_po_items_are_products():
    po_dict = load_json_file(PO_FILE, "PO_Reference")
    products_dict = load_json_file(PRODUCTS_FILE, "Product_Template")
    total = len(po_dict.items())
    for i, (po_ref,  po_data) in enumerate(po_dict.items()):
        for item in po_data["Order_Lines"]:
            prod_name = item["product_name"]
            if prod_name not in products_dict.keys():
                print(f"Error: Product '{item['product_pame']}' not found in all_products.json.")
                raise Exception(f"Error: Product '{item['product_pame']}' not found in all_products.json.")
            else:
                print(f"found {i+1}/{total} '{prod_name}'")
    print(f"All PO items in {PO_FILE} are in {PRODUCTS_FILE}.")



def check_po_in_sn_po_file_is_in_po_file():
    po_dict = load_json_file(PO_FILE, "PO_Reference")
    sn_po_dict = load_json_file(SN_PO_FILE, "picking_type")
    for i, (sn_po_ref,  sn_po_data) in enumerate(sn_po_dict.items()):
        if sn_po_ref not in po_dict.keys():
            print(f"Error: PO '{sn_po_ref}' not found in purchase_orders.json.")
            raise Exception(f"Error: PO '{sn_po_ref}' not found in purchase_orders.json.")
        else:
            print(f"found {i+1}/{len(sn_po_dict.items())} '{sn_po_ref}'")
    print(f"All POs {SN_PO_FILE} are in {PO_FILE}")


def check_product_in_sn_po_file_is_in_prod_file():
    po_dict = load_json_file(PRODUCTS_FILE, "Product_Template")
    sn_po_dict = load_json_file(SN_PO_FILE, "product_name")
    i=0
    cnt = 0
    for product_name in sn_po_dict.keys():
        i+=1
        if product_name not in po_dict.keys():
            print(f"Error: Product '{product_name}' not found in all_products.json.")
            raise Exception(f"Error: Product '{product_name}' not found in all_products.json.")
        else:
            cnt+=1
            print(f"found {cnt}/{i} '{product_name}'")
    print(f"All products {SN_PO_FILE} are in {PRODUCTS_FILE}")

def main():
    # check_po_items_are_products()
    # check_po_in_sn_po_file_is_in_po_file()
    check_product_in_sn_po_file_is_in_prod_file()



if __name__ == "__main__":
    main()



