import xmlrpc.client
from StageConfig import StageConfig as Config
from import_prod_utils import get_product_name, get_product_default_code, get_product_type, get_product_uom_id
import json

PRODUCTS_FILE = "exported_data/all_products.json"


def get_config() -> Config:
    config = Config()
    print(config)
    return config


def get_rpc_info(config: Config) -> int:
    info = xmlrpc.client.ServerProxy(f"{config.HOST}/xmlrpc/2/common")
    print(f"version:{info.version()}")
    print(f"authenticating...")
    print(f"user:{config.USER_EMAIL}, api_key:{config.API_KEY}")
    uid = info.authenticate(config.DB, config.USER_EMAIL, config.API_KEY, {})
    return uid


def convert_product_fields(models, uid: int, config: Config, item):
    """
    Convert the item (exported by export_all_products.py, hence 'wrong' field names) into a proper product
    :param models: for odoo
    :param uid: for odoo
    :param config:Config - configuration object
    :param item: item to be converted
    :return:
    """
    uom_id = get_product_uom_id(models=models, uid=uid, config=config, item=item)
    product = {
        'name': get_product_name(item),
        'default_code': get_product_default_code(item),
        'type': get_product_type(item),
        'uom_id': uom_id,
        'po_uom_id': uom_id,


    }
    return product


def import_prods_list(product_list):
    pass


def import_all_prods(uid: int, config: Config, models):
    with open(PRODUCTS_FILE, "r") as f:
        temp_list = json.load(f)
    product_list = []
    for item in temp_list:
        product = convert_product_fields(models, uid, config, item)
        product_list.append(product)
    import_prods_list(product_list)


def main():
    config = get_config()
    uid = get_rpc_info(config)
    models = xmlrpc.client.ServerProxy(f'{config.HOST}/xmlrpc/2/object')
    import_all_prods(uid, config, models)


if __name__ == '__main__':
    main()
