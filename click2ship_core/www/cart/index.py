import frappe
import json
from frappe.utils import now_datetime
import pytz

def get_context(context):
    context.csrf_token = frappe.sessions.get_csrf_token()
    # Get session key
    session_key = frappe.session.sid

    # Retrieve selected quote from cache
    selected_quote = frappe.cache().get_value(f"selected_quote:{session_key}")
    booking_details = frappe.cache().get_value(f"booking_details:{session_key}")

    # Convert to dict if it's a JSON string
    if isinstance(selected_quote, str):
        try:
            selected_quote = json.loads(selected_quote)
        except json.JSONDecodeError:
            pass  # Keep as string if not JSON

    # Convert to dict if it's a JSON string
    if isinstance(booking_details, str):
        try:
            booking_details = json.loads(booking_details)
        except json.JSONDecodeError:
            pass  # Keep as string if not JSON

    # Get server datetime in GMT/UTC
    gmt_datetime = now_datetime().astimezone(pytz.UTC)
    gmt_iso = gmt_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")  # ISO 8601 format

    # Add variables to Jinja context
    context.selected_quote = selected_quote
    context.booking_details = booking_details
    context.server_date_gmt = gmt_iso

    return context

