import frappe
import random
import string
from frappe import _
from frappe.utils.password import update_password

@frappe.whitelist(allow_guest=True)
def signup_user(**kwargs):
    """
    Create a new user with the provided details
    """
    # Disable CSRF for frontend calls
    frappe.local.no_csrf = True
    
    try:
        # Get parameters from kwargs or direct args
        email = kwargs.get("email") or kwargs.get("Email")
        first_name = kwargs.get("first_name") or kwargs.get("First Name")
        last_name = kwargs.get("last_name") or kwargs.get("Last Name")
        password = kwargs.get("password") or kwargs.get("Password")
        
        # Validate inputs
        if not all([email, first_name, last_name, password]):
            frappe.throw(_("All fields are required"))
        
        # Validate email format
        if not frappe.utils.validate_email_address(email):
            frappe.throw(_("Please enter a valid email address"))
        
        # Check if user already exists
        if frappe.db.exists("User", email):
            frappe.throw(_("User with this email already exists. Please login instead."))
        
        # Create new user
        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "enabled": 1,
            "user_type": "Website User",
            "send_welcome_email": 0
        })
        
        user.insert(ignore_permissions=True)
        
        # Set password using your preferred method
        update_password(user.name, password)
        
        # Add user to specific role
        add_user_to_role(user.name, "Customer")
        
        frappe.db.commit()
        
        # Optional: Auto-login after signup
        # frappe.local.login_manager.authenticate(user=email, pwd=password)
        # frappe.local.login_manager.post_login()
        
        return {
            "success": True,
            "message": _("Account created successfully!"),
            "user_id": user.name,
            "email": email
        }
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "User Signup Error")
        frappe.throw(_(str(e)))

def add_user_to_role(user, role):
    """
    Add user to a specific role
    """
    if not frappe.db.exists("Role", role):
        frappe.log_error(f"Role {role} does not exist")
        return
    
    if not frappe.db.exists("Has Role", {"parent": user, "role": role}):
        user_doc = frappe.get_doc("User", user)
        user_doc.append("roles", {
            "role": role
        })
        user_doc.save(ignore_permissions=True)

@frappe.whitelist(allow_guest=True)
def check_email_availability(email):
    """
    Check if email is available for registration
    """
    frappe.local.no_csrf = True
    
    if frappe.db.exists("User", email):
        return {"available": False, "message": "Email already registered"}
    else:
        return {"available": True, "message": "Email available"}

@frappe.whitelist(allow_guest=True)
def login_after_signup(email, password):
    """
    Optional: Login user immediately after signup
    """
    frappe.local.no_csrf = True
    
    try:
        frappe.local.login_manager.authenticate(user=email, pwd=password)
        frappe.local.login_manager.post_login()
        
        return {
            "success": True,
            "message": "Logged in successfully",
            "user": email
        }
    except Exception as e:
        frappe.throw(_("Login failed: {0}").format(str(e)))