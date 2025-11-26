import frappe, random, string

@frappe.whitelist(allow_guest=True)
def guest_checkout(**kwargs):
    frappe.local.no_csrf = True  

    email = kwargs.get("Email")
    if not email:
        frappe.throw("Email is required for guest checkout")

    # If user is already logged in
    if frappe.session.user != "Guest":
        return {"message": "Already Logged In", "user": frappe.session.user}

    # Check if user exists
    if frappe.db.exists("User", email):
        user = frappe.get_doc("User", email)
        password = None  # don't reset password
    else:
        # create a new website user
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": "Guest",
            "send_welcome_email": 0,
            "enabled": 1,
            "user_type": "Website User",
            "new_password": password
        })
        user.insert(ignore_permissions=True)

    # Login
    if password:  
        frappe.local.login_manager.authenticate(user=email, pwd=password)
        frappe.local.login_manager.post_login()
    else:
        frappe.set_user(email)

    # Only return success, no redirect here
    return {"message": "Logged In", "user": email}


@frappe.whitelist(allow_guest=True)
def signup(email, first_name, last_name, password):
    frappe.local.no_csrf = True  

    if not email or not password:
        frappe.throw("Email and password are required")

    if frappe.db.exists("User", email):
        return {"message": "User already exists. Please log in."}

    user = frappe.get_doc({
        "doctype": "User",
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "enabled": 1,
        "user_type": "Website User",
        "new_password": password,
        "send_welcome_email": 0
    })
    user.insert(ignore_permissions=True)

    return {"message": "Account created successfully"}
