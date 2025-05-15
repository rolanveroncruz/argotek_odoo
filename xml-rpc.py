import xmlrpc.client

HOST = "https://rolanvc-gmail-argotek-odoo-main-20392861.dev.odoo.com/"
DB = "rolanvc-gmail-argotek-odoo-main-20392861"
USER = "rkveroncruz@argotek.com.ph"
PASS = "1Lap2aceArgotek"

API_KEY = "49ff6e0490e4408b633c81bbfd855bec51341aa9"

# authenticate
info = xmlrpc.client.ServerProxy(f"{HOST}/xmlrpc/2/common")
print(f"version:{info.version()}")
uid = info.authenticate(DB, USER, API_KEY, {})
print(f"uid:{uid}")

#  list products
model = 'product.template'
domain = [("type","=", "consu")]  # Get all consumable types.
fields = ['name', 'type']
conn = xmlrpc.client.ServerProxy(f"{HOST}/xmlrpc/2/object")
ids = conn.execute_kw(DB, uid, API_KEY, "product.template", "search", [domain],{} )
records = conn.execute_kw(DB, uid, API_KEY, 'product.template', 'read', [ids], {'fields':fields})
for r in records:
    print(r)

# create one new product
id = conn.execute_kw(DB, uid, API_KEY, 'product.template', 'create',
                     [{'name': "C3 Total Mechanical Station",
                       "type": "consu",
                       "default_code": "C3-TMS-0001"}])
print(f"id:{id}")