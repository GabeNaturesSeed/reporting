# reporting

This repository is connected to codex by OpenAI and is used to create https://naturesseed.com 's dashboard and reporting.

## WooCommerce Order Export

Run `fetch_orders.py` to download order data and save it to `orders.csv`.

The script requires WooCommerce API credentials. On the first run, it will
prompt for the base URL, consumer key, and consumer secret and store them in
`wc_credentials.json` for future use. You can override the location of this
file with the `--config` option.

If an additional auth JSON file is required (for example
`naturesseed-automation-16f8b4735fb5.json`), provide it with the `--auth-file`
option.
