import xmlrpc.client
import json
from ProdConfig import ProdConfig as Config


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


def confirm_po(models, uid: int, config: Config, purchase_order_id, purchase_order_name):
    try:
        # Confirm the purchase order

        purchase_order_model = 'purchase.order'
        models.execute_kw(config.DB, uid, config.API_KEY, purchase_order_model, 'button_confirm',
                          [purchase_order_id])
        print(f"Purchase Order {purchase_order_id} confirmed.")

    except xmlrpc.client.Fault as err:
        print(f"Error creating/confirming Purchase Order {purchase_order_name}: {err.faultCode} - {err.faultString}")


def main():
    config = get_config()
    uid = get_rpc_info(config)
    models = xmlrpc.client.ServerProxy(f'{config.HOST}/xmlrpc/2/object')

    file_name = "accepted_pos.json"
    with open(file_name, "r") as f:
        po_list = json.load(f)

    for po in po_list:
        confirm_po(models, uid, config, po['purchase_order_id'], po['name'])




if __name__ == "__main__":
    main()

