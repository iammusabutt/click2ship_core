import frappe

def get_context(context):
    context.title = "About Us"
    context.items = ["Shipping", "Tracking", "Warehousing"]
    context.csrf_token = frappe.sessions.get_csrf_token()
