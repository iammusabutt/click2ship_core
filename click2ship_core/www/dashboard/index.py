import frappe

def get_context(context):
    # Fetch bookings created by current session user
    user = frappe.session.user

    if user == "Guest":
        # Redirect guest users to login page
        frappe.local.flags.redirect_location = "/signin"
        raise frappe.Redirect

    bookings = frappe.get_all(
        "Shipment Booking",
        filters={"owner": user},
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