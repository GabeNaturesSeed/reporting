import os
import json
import csv
import argparse
import requests
import gspread
from datetime import datetime

DEFAULT_CONFIG = 'wc_credentials.json'

WC_BASE_URL = 'https://naturesseed.com/wp-json/wc/v3'
CONSUMER_KEY = os.getenv('WC_CONSUMER_KEY')
CONSUMER_SECRET = os.getenv('WC_CONSUMER_SECRET')

START_DATE = '2025-01-01T00:00:00'

# Google Sheet configuration
GSHEET_URL = 'https://docs.google.com/spreadsheets/d/1kJH3Gk9IVJoLp6MqDj7lit_iqsMdYWYvEpsUz4pVDxc'
SHEET_NAME = 'order_data'

CSV_HEADERS = [
    'order_id',
    'order_date',
    'customer_id',
    'line_item_sku',
    'line_item_quantity',
    'line_item_total',
    'product_cost',
    'line_COGS',
    'order_status',
    'shipping_paid',
    'taxes_paid'
]


def load_config(path: str):
    """Load WooCommerce credentials from a JSON file.

    If the file does not exist, prompt the user for credentials and
    save them for future runs.
    """
    if os.path.exists(path):
        with open(path, 'r') as f:
            data = json.load(f)
        return data.get('WC_BASE_URL'), data.get('CONSUMER_KEY'), data.get('CONSUMER_SECRET')

    print('WooCommerce credentials not found. Please enter them now:')
    base_url = input('WooCommerce base URL: ').strip() or WC_BASE_URL
    key = input('Consumer key: ').strip()
    secret = input('Consumer secret: ').strip()

    creds = {
        'WC_BASE_URL': base_url,
        'CONSUMER_KEY': key,
        'CONSUMER_SECRET': secret,
    }
    with open(path, 'w') as f:
        json.dump(creds, f)
    return base_url, key, secret

def fetch_orders():
    orders = []
    page = 1
    while True:
        params = {
            'per_page': 100,
            'page': page,
            'after': START_DATE,
            'status': 'any',
            'orderby': 'date',
            'order': 'asc'
        }
        resp = requests.get(
            f"{WC_BASE_URL}/orders",
            params=params,
            auth=(CONSUMER_KEY, CONSUMER_SECRET)
        )
        if resp.status_code != 200:
            raise Exception(f"API request failed: {resp.status_code} {resp.text}")
        data = resp.json()
        if not data:
            break
        orders.extend(data)
        page += 1
    return orders

def extract_line_items(order):
    shipping = order.get('shipping_total') or '0'
    taxes = order.get('total_tax') or '0'
    order_id = order.get('id')
    order_date = order.get('date_created')
    customer_id = order.get('customer_id')
    order_status = order.get('status')

    rows = []
    for item in order.get('line_items', []):
        quantity = item.get('quantity', 0)
        line_total = item.get('total', '0')
        sku = item.get('sku')
        product_cost = 0
        for meta in item.get('meta_data', []):
            if str(meta.get('key')).lower() in {'product_cost', 'cost_of_goods', '_wc_cog_cost', 'cogs'}:
                try:
                    product_cost = float(meta.get('value'))
                except (TypeError, ValueError):
                    product_cost = 0
                break
        line_cogs = product_cost * quantity
        rows.append([
            order_id,
            order_date,
            customer_id,
            sku,
            quantity,
            line_total,
            product_cost,
            line_cogs,
            order_status,
            shipping,
            taxes
        ])
    return rows

def main():
    parser = argparse.ArgumentParser(
        description='Fetch WooCommerce orders and save to CSV'
    )
    parser.add_argument(
        '--config',
        default=DEFAULT_CONFIG,
        help='Path to JSON config file for WooCommerce credentials'
    )
    parser.add_argument(
        '--auth-file',
        help='Path to additional auth JSON file if required'
    )
    args = parser.parse_args()

    global WC_BASE_URL, CONSUMER_KEY, CONSUMER_SECRET
    WC_BASE_URL, CONSUMER_KEY, CONSUMER_SECRET = load_config(args.config)

    if args.auth_file:
        if not os.path.exists(args.auth_file):
            raise FileNotFoundError(f'Auth file {args.auth_file} not found')
        print(f'Using auth file: {args.auth_file}')

    orders = fetch_orders()
    with open('orders.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS)
        for order in orders:
            rows = extract_line_items(order)
            writer.writerows(rows)
    print(f"Wrote {len(orders)} orders to orders.csv")

    if args.auth_file:
        gc = gspread.service_account(filename=args.auth_file)
        sh = gc.open_by_url(GSHEET_URL)
        try:
            ws = sh.worksheet(SHEET_NAME)
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet(title=SHEET_NAME, rows="100", cols="20")
        with open('orders.csv', 'r', newline='') as f:
            reader = list(csv.reader(f))
        ws.clear()
        ws.update('A1', reader)
        print(f"Uploaded {len(reader)-1} rows to Google Sheet {SHEET_NAME}")

if __name__ == '__main__':
    main()
