import frappe, random, string

@frappe.whitelist(allow_guest=True)
def guest_checkout(**kwargs):
    frappe.local.no_csrf = True  

    email = kwargs.get("Email")
    if not email:
        frappe.throw("Email is required for guest checkout")

    # Preserve session data from the old session
    old_session_key = frappe.session.sid
    session_data = frappe.cache().get_value(f"session_data:{old_session_key}")

    # If the user is already logged in with the same email, do nothing.
    if frappe.session.user == email:
        return {"message": "Already Logged In", "user": email}

    # If a user with this email already exists, prevent guest creation to avoid conflicts.
    if frappe.db.exists("User", email):
        frappe.throw("A user with this email address already exists. Please log in to continue.")

    # Create a new website user for the guest
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

    # Log in as the new user, which starts a new session
    frappe.local.login_manager.authenticate(user=email, pwd=password)
    frappe.local.login_manager.post_login()

    # Restore the original session data to the new session
    if session_data:
        new_session_key = frappe.session.sid
        frappe.cache().set_value(f"session_data:{new_session_key}", session_data, expires_in_sec=3600)

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

@frappe.whitelist()
def set_password(new_password):
    user_id = frappe.session.user
    if user_id == "Guest":
        frappe.throw("You must be logged in to change your password.")

    user = frappe.get_doc("User", user_id)
    user.new_password = new_password
    user.save(ignore_permissions=True)
    return {"message": "Password updated successfully"}

@frappe.whitelist()
def update_profile(first_name=None, last_name=None, phone=None):
    user_id = frappe.session.user
    if user_id == "Guest":
        frappe.throw("You must be logged in to update your profile.")

    user = frappe.get_doc("User", user_id)

    if first_name is not None:
        user.first_name = first_name
    if last_name is not None:
        user.last_name = last_name
    if phone is not None:
        user.phone = phone

    user.save(ignore_permissions=True)
    return {"message": "Profile updated successfully"}
