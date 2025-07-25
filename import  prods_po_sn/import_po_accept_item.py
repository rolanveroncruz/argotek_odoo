import xmlrpc.client
from StageConfig import StageConfig as Config
from import_po_accept_fns import import_all_pos



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


def main():
    config = get_config()
    uid = get_rpc_info(config)
    models = xmlrpc.client.ServerProxy(f'{config.HOST}/xmlrpc/2/object')

    import_all_pos(models, uid, config)


if __name__ == "__main__":
    main()


