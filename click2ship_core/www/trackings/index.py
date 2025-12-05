import frappe

def get_context(context):
    context.csrf_token = frappe.sessions.get_csrf_token()
    return context
