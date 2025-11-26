import frappe

def get_context(context):
    # Fetch bookings created by current session user
    user = frappe.session.user

    bookings = frappe.get_all(
        "Shipment Booking",
        filters={"owner": user},   # or {"owner_user": user} if you made a custom field
        fields=["name", "shipment_barcode", "creation"],
        order_by="creation desc"
    )

    # Attach file_url if exists
    for b in bookings:
        file_doc = frappe.db.get_value(
            "File",
            {"attached_to_doctype": "Shipment Booking", "attached_to_name": b.name},
            "file_url"
        )
        b.file_url = file_doc or None

    context.bookings = bookings
    return context