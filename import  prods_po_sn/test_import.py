import xmlrpc.client
from StageConfig import StageConfig as Config


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


def import_po(models, uid: int, config: Config, po):
    purchase_order_id = models.execute_kw(config.DB, uid, config.API_KEY,
                                          'purchase.order', 'create', [po])
    print(f"Purchase Order created with ID: {purchase_order_id}")
    po['purchase_order_id'] = purchase_order_id
    return po


def get_user_id_from_temp_po(models, uid: int, config: Config, temp_po):
    user = temp_po['Purchase_Representative']
    partner_model = 'res.users'
    user_ids = models.execute_kw(config.DB, uid, config.API_KEY, partner_model, 'search',
                                 [[('name', '=', user)]], {'limit': 1})
    user_id = user_ids[0]
    print(f"User: {user} has ID: {user_id}")
    return user_id


def main():
    # po = {'currency_id': 1,
    #       'date_order': '2025-07-15 07:37:24',
    #       'name': 'P00032',
    #       'order_line': [
    #           (0, 0, {'date_planned': '2025-07-15 07:37:24', 'price_unit': 696.5, 'product_id': 152, 'product_qty': 1.0}),
    #           (0, 0, {'date_planned': '2025-07-15 07:37:24', 'price_unit': 626.5, 'product_id': 167, 'product_qty': 1.0}),
    #           (0, 0, {'date_planned': '2025-07-15 07:37:24', 'price_unit': 976.5, 'product_id': 156, 'product_qty': 1.0})],
    #       'partner_id': 9,
    #       'user_id': 7
    #       }
    config = get_config()
    uid = get_rpc_info(config)
    models = xmlrpc.client.ServerProxy(f'{config.HOST}/xmlrpc/2/object')
#    result = import_po(models, uid, config, po)
    result = get_user_id_from_temp_po(models, uid, config, {'Purchase_Representative': 'Catherine Castillo'})
    print(result)




if __name__ == '__main__':
    main()
