import openpyxl as xl
import xmlrpc.client
from StageConfig import StageConfig as Config


def get_config() -> Config:
    config = Config()
    print(config)
    return config

def get_rpc_info(config:Config)-> int:
    info = xmlrpc.client.ServerProxy(f"{config.HOST}/xmlrpc/2/common")
    print(f"version:{info.version()}")
    print(f"authenticating...")
    print(f"user:{config.USER_EMAIL}, api_key:{config.API_KEY}")
    uid = info.authenticate(config.DB, config.USER_EMAIL, config.API_KEY, {})
    return uid

def upload_lead(config:Config, uid:int, lead: object) -> int:
    model = 'crm.lead'
    conn = xmlrpc.client.ServerProxy(f"{config.HOST}/xmlrpc/2/object")
    lead_id = conn.execute_kw(config.DB, uid, config.API_KEY, model, 'create',
                         [lead]
    )
    return lead_id





def main():
    config = get_config()
    uid = get_rpc_info(config)
    lead_data = {
        'name': 'Anoter New Lead from XML-RPC to Noel Picaso',
        'email_from': 'test@example.com',
        'phone': '123-456-7890',
        'contact_name': 'Jane Doe',
        'description': 'This is a test lead created from XML-RPC.',
        # Add other relevant fields
        'user_id': 6, # Noel Picaso
    }

    lead_id = upload_lead(config, uid ,lead_data)
    print(f"lead_id:{lead_id}")



if __name__ == "__main__":
    main()