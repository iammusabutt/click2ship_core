# File: click2ship_core/api/norsk_api.py

import frappe
import requests
import hmac
import hashlib
import base64
import json
import datetime
from email.utils import formatdate

def get_norsk_settings():
    settings = frappe.get_single("Norsk Settings")
    return {
        "api_url": settings.default_api_url.strip(),
        "access_key": settings.access_key.strip(),
        "secret_access_key": settings.secret_access_key.strip(),
        "api_endpoint_quote": settings.api_endpoint_quote.strip()
    }
    
def get_auth_headers(payload, resource):
    settings = get_norsk_settings()

    # Step 4: Prepare Norsk headers and signature
    date = formatdate(timeval=None, localtime=False, usegmt=True)
    content_type = "application/json"
    body_md5 = hashlib.md5(payload).hexdigest()
    string_to_sign = f"POST\n{body_md5}\n{content_type}\n{date}\n{resource}"
    signature = base64.b64encode(
        hmac.new(
            key=settings['secret_access_key'].encode('utf-8'),
            msg=string_to_sign.encode('utf-8'),
            digestmod=hashlib.sha1
        ).digest()
    ).decode('utf-8')

    headers = {
        "Authorization": f"{settings['access_key']}:{signature}",
        "Date": date,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    return headers
    
# === Norsk API credentials ===
NORSK_ACCESS_KEY_ID = "26IPAFUH3UR3WA6L"
NORSK_SECRET_ACCESS_KEY = "Y3CX7TS7BPMJRMAEFYDJ6XJQ4TQTS65GEVRQNZ2WLUHHA2RX"

# -------------------------------------------------------------
# Fetch quotes from Norsk API
# -------------------------------------------------------------
@frappe.whitelist(allow_guest=True)
def get_norsk_shipping_quote():
    settings = get_norsk_settings()
    try:
        # Step 1: Get user input (quoteInput)
        raw_data = frappe.request.get_data(as_text=True)
        if not raw_data:
            frappe.throw("No quote input data received.")
        quote_input = json.loads(raw_data)

        # Step 2: Build Norsk quoteData using input
        quote_data = {
            "Zipcode": quote_input.get("destinationZipcode") or quote_input.get("receiverZipcode") or "33409",
            "Town": quote_input.get("destinationTown") or quote_input.get("receiverTown") or "West Palm Beach",
            "CountryCode": quote_input.get("destinationCountry") or quote_input.get("receiverCountry") or "US",
            "Dutiable": {
                "Value": 1,
                "Currency": "USD"
            },
            "Pieces": [
                {
                    "Length": float(quote_input.get("boxlength", 1)),
                    "Width": float(quote_input.get("boxwidth", 1)),
                    "Height": float(quote_input.get("boxheight", 1)),
                    "Weight": float(quote_input.get("boxweight", 1)),
                    "NumberOfPieces": int(quote_input.get("quantity", 1))
                }
            ]
        }

        # Step 3: Add dynamic shipping date
        shipping_date = (datetime.datetime.utcnow() + datetime.timedelta(minutes=30)).isoformat() + "Z"
        quote_data["ShippingDate"] = shipping_date

        updated_payload = json.dumps(quote_data).encode('utf-8')
        resource = settings['api_endpoint_quote']

        url = f"{settings['api_url']}quote"
        # Step 5: Make Norsk API call
        response = requests.post(
            url,
            headers=get_auth_headers(updated_payload, resource),
            data=updated_payload
        )

        if response.status_code >= 400:
            try:
                error_details = response.json()
            except Exception:
                error_details = response.text
            frappe.throw(f"Quote API Error {response.status_code}: {error_details}")

        return response.json()

    except requests.exceptions.RequestException as req_err:
        frappe.log_error(frappe.get_traceback(), "Norsk Quote API Request Error")
        frappe.throw(f"Network error while contacting Norsk Quote API: {str(req_err)}")

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Unexpected Error in Quote Request")
        frappe.throw(f"Unexpected error during quote request: {str(e)}")


# -------------------------------------------------------------
# Get booking details from cache
# -------------------------------------------------------------
@frappe.whitelist(allow_guest=True)
def get_booking_details_from_cache():
    try:
        session_key = frappe.session.sid
        session_data = frappe.cache().get_value(f"session_data:{session_key}") or {}
        booking_details = session_data.get("booking", {})

        if not booking_details:
            frappe.throw("No booking data found in cache for this session.")

        return {"status": "success", "data": booking_details}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Booking Cache Fetch Failed")
        return {"status": "error", "message": str(e)}

@frappe.whitelist(allow_guest=True)
def get_session_data():
    return dict(frappe.session.data)

# -------------------------------------------------------------
# Book shipment and store Norsk response
# -------------------------------------------------------------
@frappe.whitelist(allow_guest=True)
def book_norsk_shipment():
    try:
        shipment_data = frappe.request.get_data()
    
        if not shipment_data:
            frappe.throw("Shipment data is missing or invalid.")

        date = formatdate(timeval=None, localtime=False, usegmt=True)
        resource = "/api/shipment"
        content_type = "application/json"

        body_md5 = hashlib.md5(shipment_data).hexdigest()
        string_to_sign = f"POST\n{body_md5}\n{content_type}\n{date}\n{resource}"
        signature = base64.b64encode(
            hmac.new(
                key=NORSK_SECRET_ACCESS_KEY.encode('utf-8'),
                msg=string_to_sign.encode('utf-8'),
                digestmod=hashlib.sha1
            ).digest()
        ).decode('utf-8')

        auth_header = f"{NORSK_ACCESS_KEY_ID}:{signature}"

        headers = {
            "Authorization": auth_header,
            "Date": date,
            "Accept": "application/json",
            "Content-Type": content_type
        }

        response = requests.post(
            "http://dev-api.norsk-global.com/api/shipment",
            headers=headers,
            data=shipment_data
        )

        if response.status_code >= 400:
            try:
                error_details = response.json()
            except Exception:
                error_details = response.text
            frappe.throw(f"Shipment API Error {response.status_code}: {error_details}")

        # API JSON Response
        resp_json = response.json()
        #frappe.throw(f"RESPONSE: {json.dumps(barcode, indent=2)}")
        #return

        # Extract fields
        barcode = resp_json.get("Barcode", {})
        label_base64 = resp_json.get("Label", {})

        # Store into ERPNext Doctype
        doc = frappe.new_doc("Shipment Booking")
        doc.shipment_barcode = resp_json.get("Barcode", {})
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
        frappe.log_error(frappe.get_traceback(), "Norsk Shipment API Request Error")
        frappe.throw(f"Network error while contacting Norsk Shipment API: {str(req_err)}")

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Unexpected Error in Shipment Booking")
        frappe.throw(f"Unexpected error during shipment booking: {str(e)}")
        

@frappe.whitelist(allow_guest=True)
def get_cached_booking_details():
    """
    Fetch booking details from cache for current session
    """
    try:
        session_key = frappe.session.sid
        session_data = frappe.cache().get_value(f"session_data:{session_key}") or {}
        booking_details = session_data.get("booking", {})
        return booking_details
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Fetch Booking Cache Failed")
        return {"status": "error", "message": str(e)}

@frappe.whitelist(allow_guest=True)
def get_selected_quote():
    """
    Fetch the selected quote from cache for the current session
    """
    try:
        session_key = frappe.session.sid
        quote = frappe.cache().get_value(f"selected_quote:{session_key}") or {}
        return quote
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Fetch Selected Quote Failed")
        return {"status": "error", "message": str(e)}
