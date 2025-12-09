import frappe, random, string
from frappe.website.utils import is_signup_disabled
from frappe import _
from frappe.utils import escape_html

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
        "first_name": escape_html("Guest"), # Added escape_html
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


@frappe.whitelist(allow_guest=True, methods=["POST"])
def signup(email, first_name, last_name, password, redirect_to=None):
    frappe.local.no_csrf = True

    if is_signup_disabled():
        frappe.throw(_("Sign Up is disabled"), title=_("Not Allowed"))

    if not email or not password:
        frappe.throw(_("Email and password are required"))

    user_exists = frappe.db.get("User", {"email": email})
    if user_exists:
        if user_exists.enabled:
            return {"status": "error", "message": _("Already Registered")}
        else:
            return {"status": "error", "message": _("Registered but disabled")}

    if frappe.db.get_creation_count("User", 60) > 300: # Rate limiting
        frappe.respond_as_web_page(
            _("Temporarily Disabled"),
            _(
                "Too many users signed up recently, so the registration is disabled. Please try back in an hour"
            ),
            http_status_code=429,
        )
        return {"status": "error", "message": _("Temporarily Disabled")} # Added return for consistency

    user = frappe.get_doc({
        "doctype": "User",
        "email": email,
        "first_name": escape_html(first_name),
        "last_name": escape_html(last_name),
        "enabled": 1,
        "user_type": "Website User",
        "new_password": password,
        "send_welcome_email": 0 # Keep this as 0 for direct password signup
    })
    user.flags.ignore_permissions = True
    user.flags.ignore_password_policy = True
    user.insert()

    # set default signup role as per Portal Settings
    default_role = frappe.get_single_value("Portal Settings", "default_role")
    if default_role:
        user.add_roles(default_role)

    if redirect_to:
        frappe.cache.hset("redirect_after_login", user.name, redirect_to)

    # Directly log in the user after successful signup
    try:
        frappe.local.login_manager.authenticate(user=email, pwd=password)
        frappe.local.login_manager.post_login()
        return {"status": "success", "message": _("Account created successfully and logged in.")}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Signup: Auto-login failed")
        return {"status": "error", "message": _("Account created, but automatic login failed: {0}").format(e)}

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
