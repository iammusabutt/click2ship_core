import frappe

def get_context(context):
    # force reload
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/signin"
        raise frappe.Redirect

    user_doc = frappe.get_doc("User", frappe.session.user)
    context.email = user_doc.email
    context.full_name = user_doc.full_name
    context.first_name = user_doc.first_name
    context.last_name = user_doc.last_name
    context.phone = user_doc.phone
    context.csrf_token = frappe.sessions.get_csrf_token()
