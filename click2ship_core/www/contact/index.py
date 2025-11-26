import frappe

def get_context(context):
    context.title = "Contact Us"
    context.items = ["Shipping", "Tracking", "Warehousing"]
