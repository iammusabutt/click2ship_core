import frappe

def get_context(context):
    context.title = "Tracking"
    context.items = ["Shipping", "Tracking", "Warehousing"]
