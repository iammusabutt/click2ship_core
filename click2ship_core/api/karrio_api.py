import requests
import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime, cstr
import json
import base64
KARRIO_BASE_URL = "https://api.click2ship.net"

#KARRIO_BASE_URL = "https://noninterpretational-madelene-geminally.ngrok-free.dev"

def _get_settings():
    """Get Karrio Settings Doc"""
    return frappe.get_single("Karrio Settings")

def _save_tokens(access_token, refresh_token, expires_in=3600):
    """Save new tokens in settings"""
    settings = _get_settings()
    settings.access_token = access_token
    settings.refresh_token = refresh_token
    settings.token_expiry = now_datetime()
    settings.save(ignore_permissions=True)
    frappe.db.commit()

def get_auth_token(username, password):
    """
    Get authentication token from Karrio API and save into Karrio Settings
    """
    url = f"{KARRIO_BASE_URL}/api/token"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    data = {
        "email": username,   # Karrio expects email field
        "password": password
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            tokens = response.json()   # { "access": "...", "refresh": "..." }

            # Save into Karrio Settings
            _save_tokens(tokens.get("access"), tokens.get("refresh"))
            return tokens
        else:
            frappe.throw(f"Karrio Authentication failed: {response.status_code} {response.text}")
            
    except requests.exceptions.RequestException as e:
        frappe.throw(f"Karrio Authentication request failed: {str(e)}")


def refresh_token(refresh_token):
    """
    Refresh access token using Karrio refresh token endpoint
    """
    url = f"{KARRIO_BASE_URL}/api/token/refresh"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    data = {
        "refresh": refresh_token
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()  # Expected: { "access": "new_token" }
        else:
            frappe.throw(f"Karrio Token refresh failed: {response.status_code} {response.text}")
            
    except requests.exceptions.RequestException as e:
        frappe.throw(f"Karrio Token refresh request failed: {str(e)}")


def _get_valid_token():
    """Ensure a valid access token (refresh if expired or fallback to re-authenticate)"""
    settings = _get_settings()

    # No token at all — get fresh
    if not settings.access_token:
        auth = get_auth_token(settings.username, settings.password)
        _save_tokens(auth["access"], auth["refresh"])
        return auth["access"]

    # Token expired — try to refresh
    if settings.token_expiry and get_datetime(settings.token_expiry) < now_datetime():
        try:
            refreshed = refresh_token(settings.refresh_token)
            _save_tokens(refreshed["access"], settings.refresh_token)
            return refreshed["access"]
        except Exception as e:
            # Refresh token invalid — fallback to full login
            auth = get_auth_token(settings.username, settings.password)
            _save_tokens(auth["access"], auth["refresh"])
            return auth["access"]

    # Token still valid
    return settings.access_token



@frappe.whitelist(allow_guest=True)
def rates():
    # -----------------------------------------------
    # STEP 1 — Parse incoming request
    # -----------------------------------------------
    try:
        raw_data = frappe.request.get_data(as_text=True)
        if not raw_data:
            return {
                "success": False,
                "error_type": "invalid_request",
                "message": "No quote input data received."
            }
        quote_input = json.loads(raw_data)

    except Exception as e:
        return {
            "success": False,
            "error_type": "json_parse_error",
            "message": f"Error parsing request data: {str(e)}"
        }

    # -----------------------------------------------
    # STEP 2 — Build payload (you can map quote_input later)
    # -----------------------------------------------
    payload = {
        "shipper": {
            "postal_code": "SW1A1AA",
            "country_code": "GB"
        },
        "recipient": {
            "postal_code": "4008",
            "country_code": "AU"
        },
        "parcels": [
            {
                "weight": 2,
                "width": 1,
                "height": 1,
                "length": 1,
                "weight_unit": "KG",
                "dimension_unit": "CM",
                "items": [
                    {
                        "weight": 1,
                        "weight_unit": "KG",
                        "value_amount": 25.00,
                        "value_currency": "USD",
                        "origin_country": "GB",
                    },
                    {
                        "weight": 1,
                        "weight_unit": "KG",
                        "value_amount": 15.00,
                        "value_currency": "USD",
                        "origin_country": "GB",
                    },
                ],
                "reference_number": "INV-1001",
                "options": {},
            }
        ],
        "services": [],
        "options": {
            "currency": "USD",
            "insurance": 10.00,
            "dangerous_good": False,
            "declared_value": 50.00,
        },
        "reference": "TEST-FEDEX-GB-US",
    }

    # -----------------------------------------------
    # STEP 3 — Send request to Karrio
    # -----------------------------------------------
    access_token = _get_valid_token()
    url = f"{KARRIO_BASE_URL}/v1/proxy/rates"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-test-mode": "true",
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)

    except requests.exceptions.RequestException as e:
        # Network error, timeout → return clean error
        return {
            "success": False,
            "error_type": "network_error",
            "message": f"Karrio API request failed: {str(e)}"
        }

    # -----------------------------------------------
    # STEP 4 — Handle HTTP responses
    # -----------------------------------------------
    if response.status_code in [200, 207]:
        data = response.json()

        # Log partial success warnings quietly
        if response.status_code == 207:
            frappe.log_error(
                title="Karrio API partial success",
                message=f"Warnings: {data.get('messages')}"
            )

        return {
            "success": True,
            "rates": data.get("rates", []),
            "messages": data.get("messages", [])
        }

    # Token expired → reset & retry
    if response.status_code == 401:
        settings = _get_settings()
        settings.access_token = None
        settings.save(ignore_permissions=True)
        frappe.db.commit()
        return rates()

    # Karrio returns structured error JSON → return parsed error
    try:
        err = response.json()
    except:
        err = {"message": response.text}

    return {
        "success": False,
        "error_type": "carrier_error",
        "carrier": err.get("messages", [{}])[0].get("carrier_name", "unknown"),
        "carrier_code": err.get("messages", [{}])[0].get("code"),
        "message": err.get("messages", [{}])[0].get("message") or "Carrier service unavailable",
        "raw": err
    }

@frappe.whitelist(allow_guest=True)
def shipment():
    """
    Create a shipment booking with Karrio API
    """
    try:
        # Get the access token
        access_token = _get_valid_token()
        url = f"{KARRIO_BASE_URL}/v1/shipments"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-test-mode": "true"
        }

        # Get data from the request
        shipment_data = frappe.request.get_json()

        response = requests.post(url, json=shipment_data, headers=headers, timeout=15)

        if response.status_code not in [200, 201]:
            frappe.throw(f"Shipment API Error {response.status_code}: {response.text}")

        # Parse the response JSON
        resp_json = response.json()

        # Extract fields
        barcode = resp_json.get("Barcode", {})
        label_base64 = resp_json.get("Label", {})

        # Store into ERPNext Doctype
        doc = frappe.new_doc("Shipment Booking")
        doc.shipment_barcode = barcode
        doc.user = frappe.session.user
        doc.insert(ignore_permissions=True)
        
        file_name = f"Shipment_Label_{barcode}.pdf"
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": file_name,
            "attached_to_doctype": "Shipment Booking",
            "attached_to_name": doc.name,   # Link to THIS booking record
            "is_private": 1,
            "content": base64.b64decode(label_base64)  # decode PDF
        })
        file_doc.insert(ignore_permissions=True)

        return {
            "success": True,
            "shipment_id": doc.name,
            "barcode": barcode,
            "label_url": file_doc.file_url   # ERPNext file URL
        }

    except requests.exceptions.RequestException as req_err:
        frappe.log_error(frappe.get_traceback(), "Karrio Shipment API Request Error")
        frappe.throw(f"Network error while contacting Karrio Shipment API: {str(req_err)}")

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Unexpected Error in Shipment Booking")
        frappe.throw(f"An unexpected error occurred during shipment booking: {str(e)}")