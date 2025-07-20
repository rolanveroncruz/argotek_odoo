import xmlrpc.client
from ProdConfig import ProdConfig as Config
import csv
import json
import time
from export_sn_po_utils import  export_serial_number_products,  export_po_data, export_to_csv_json
from typing import IO
import os

# --- Output File Names ---
OUTPUT_CSV_FILE = 'inventory_prod_sn_po.csv'
OUTPUT_JSON_FILE = 'inventory_prod_sn_po.json'

def get_config() -> Config:
    the_config = Config()
    print(the_config)
    return the_config










def print_message(message, time_start):
    time_now = time.time()
    interval = time_now - time_start
    if interval < 60:
        print(f" {message}: {interval:.2f} seconds after start.")
    elif interval < 3600:
        print(f" {message}: {interval/60:.2f} minutes after start.")
    else:
        print(f" {message}: {interval / 3600:.2f} hours after start.")
    return


def export_inv_prod_sn_po(config:Config)->None:
    """
    This is the make export function. It does this using the following steps:
    1. Calls export_serial_number_products() to get a list of serial numbers and their associated products. This data
    is stored in lots_data.
    2. Calls export_po_data(), passing in lots_data to get a list of serial numbers and associated purchase order data.
    3. Saves the results to a CSV file and a JSON file.
    :param config: Configuration
    :return: NONE
    """
    start_time = time.time()
    print(f"Connecting to Odoo at {config.HOST} (Database: {config.DB})...")
    try:
        # Authenticate and get UID
        common = xmlrpc.client.ServerProxy(f'{config.HOST}/xmlrpc/2/common')
        uid = common.authenticate(config.DB, config.USER_EMAIL, config.API_KEY, {})
        if not uid:
            print("Authentication failed. Check your Odoo URL, DB, username, and password.")
            return

        print(f"Authentication successful. User ID: {uid}")
        models = xmlrpc.client.ServerProxy(f'{config.HOST}/xmlrpc/2/object')
        print_message("Completed authentication. Starting export of serial numbers. ", start_time)

        lots_data = export_serial_number_products(models, uid, config)
        print_message("Completed export of sn products. Starting export of purchase order data. ", start_time)
        serial_data_with_po = export_po_data(models, uid, config, lots_data)

        print_message("Completed export of purchase order data. Starting export to CSV and JSON. ", start_time)

        export_to_csv_json(serial_data_with_po)
        print_message("Completed export to CSV and JSON. ", start_time)
    except xmlrpc.client.Fault as err:
        print(f"XML-RPC Fault: {err.faultCode} - {err.faultString}")
    except Exception as e:
        print(f"An error occurred: {e}")

    print("Export complete.")


def main():
    config = get_config()
    export_inv_prod_sn_po(config)


if __name__ == "__main__":
    main()