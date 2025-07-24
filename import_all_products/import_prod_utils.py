from ProdConfig import ProdConfig as Config


def get_product_name(item):
    """
    The export_all_products.py code converted 'name' to 'Product_Name'.
    :param item:
    :return:
    """
    return item.get("Product_Name")


def get_product_default_code(item):
    """

    :param item:
    :return:
    """
    return item.get("Internal_Reference")


def get_product_type(item):
    """

    :param item:
    :return:
    """
    return item.get("Product_Type")


def get_product_uom_id(models, uid: int, config: Config, item):
    uom_model = 'uom.uom'
    uom_name = item.get("Sales_UoM", "Units")
    uom_ids = models.execute_kw(
        config.DB, uid, config.API_KEY,
        uom_model, 'search',
        [[['name', '=', uom_name]]]
    )
    uom_id = uom_ids[0]
    print(f"Found UoM '{uom_name}' with ID: {uom_id}")
    return uom_id
