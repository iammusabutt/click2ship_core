import frappe

def get_context(context):
    context.csrf_token = frappe.sessions.get_csrf_token()
    # Get all currencies and their symbols
    currencies = frappe.get_all("Currency", fields=["name", "symbol"])
    symbols = {c["name"]: c["symbol"] for c in currencies}
    context.currency_symbols = symbols  # available in the Jinja template
