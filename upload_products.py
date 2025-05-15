import openpyxl as xl
import xmlrpc.client
from Config import Config


def get_config() -> Config:
    config = Config("prod.env")
    return config

def get_rpc_info(config:Config)-> int:
    info = xmlrpc.client.ServerProxy(f"{config.HOST}/xmlrpc/2/common")
    print(f"version:{info.version()}")
    uid = info.authenticate(config.DB, config.USER_EMAIL, config.API_KEY, {})
    print(f"uid:{uid}")
    return uid



def read_products() -> dict:
    file = "data/SampleInventory_forSirRolan_05092025.xlsx"
    wb = xl.load_workbook(file)
    sheet = wb.active
    product_map = {}

    for idx,row in enumerate(sheet.iter_rows()):
        if idx == 0:
            continue
        part_number = row[0].value
        item_name = row[1].value
        if part_number not in product_map.keys():
            product_map[part_number] = item_name

    return product_map

def upload_products(config:Config, product_map:dict, uid:int) -> list[int]:
    model = 'product.template'
    ids = []
    for  part_number, item_name in product_map.items():
        conn = xmlrpc.client.ServerProxy(f"{config.HOST}/xmlrpc/2/object")
        print(f"uploading {part_number}-{item_name}")
        id = conn.execute_kw(config.DB, uid, config.API_KEY, 'product.template', 'create',
                                 [{'name': item_name,
                                   "type": "consu",
                                   "default_code": f"{part_number}"
                                 }])
        ids.append(id)
    return ids



def main():
    config = get_config()
    uid = get_rpc_info(config)
    product_map = read_products()
    ids= upload_products(config,product_map, uid)
    print(f"uploaded {len(ids)} items.")


if __name__ == "__main__":
    main()