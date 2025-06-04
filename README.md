# reporting

This repository is connected to codex by OpenAI and is used to create https://naturesseed.com 's dashboard and reporting.

## WooCommerce Order Export

Run `fetch_orders.py` to download order data and save it to `orders.csv`.

Install dependencies first:

```bash
pip install -r requirements.txt
```

The script requires WooCommerce API credentials. On the first run, it will
prompt for the base URL, consumer key, and consumer secret and store them in
`wc_credentials.json` for future use. You can override the location of this
file with the `--config` option.

If you provide a Google service account JSON file (for example
`naturesseed-automation-16f8b4735fb5.json`) with the `--auth-file` option,
the script will also upload `orders.csv` to the Google Sheet at
`https://docs.google.com/spreadsheets/d/1kJH3Gk9IVJoLp6MqDj7lit_iqsMdYWYvEpsUz4pVDxc`.
Data is written to the `order_data` worksheet and replaces any existing
content.

Example usage:

```bash
python fetch_orders.py --auth-file naturesseed-automation-16f8b4735fb5.json
```
