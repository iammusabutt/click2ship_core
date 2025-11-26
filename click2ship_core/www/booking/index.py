import frappe
import json
from frappe.utils import now_datetime
import pytz

def get_context(context):
    # CSRF token for forms
    context.csrf_token = frappe.sessions.get_csrf_token()

    # Get session key
    session_key = frappe.session.sid

    # Retrieve selected quote from cache
    selected_quote = frappe.cache().get_value(f"session_data:{session_key}")

    # If no quote, redirect to home
    if not selected_quote:
        frappe.local.flags.redirect_location = "/"
        raise frappe.Redirect

    # Convert JSON string to dict if necessary
    if isinstance(selected_quote, str):
        try:
            selected_quote = json.loads(selected_quote)
        except json.JSONDecodeError:
            selected_quote = {}

    # Server datetime in GMT
    gmt_datetime = now_datetime().astimezone(pytz.UTC)
    gmt_iso = gmt_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Pass variables to Jinja template
    context.selected_quote = selected_quote
    context.server_date_gmt = gmt_iso

    return context
