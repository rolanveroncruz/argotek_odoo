import json
import random
import urllib.request


HOST = "https://argotek.odoo.com"
PORT = 8069
DB = "argotek"
USER = "rolanvc@gmail.com"
PASS = "y2T4)QysQ++;^xj"

def json_rpc(the_url, method, params):
    data = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": random.randint(0, 1000000000),
    }
    req = urllib.request.Request(url=the_url, data=json.dumps(data).encode(), headers={
        "Content-Type":"application/json",
    })
    reply = urllib.request.urlopen(req).read().decode('UTF-8')
    json_reply = json.loads(reply)
    if json_reply.get("error"):
        raise Exception(json_reply["error"])
    return json_reply["result"]

def call(the_url, service, method, *args):
    return json_rpc(the_url, "call", {"service": service, "method": method, "args": args})

# log in the given database
url = "http://%s:%s/jsonrpc" % (HOST, PORT)
uid = call(url, "common", "login", DB, USER, PASS)