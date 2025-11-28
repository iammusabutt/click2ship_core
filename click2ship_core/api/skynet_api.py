import requests
import json
import frappe

def get_skynet_settings():
    settings = frappe.get_single("Skynet Settings")
    return {
        "api_url": settings.default_api_url.strip(),
        "token": settings.account_token.strip()
    }
    
def get_auth_headers():
    settings = get_skynet_settings()
    return {
        "Token": settings["token"],
        "Content-Type": "application/json"
    }
    
@frappe.whitelist(allow_guest=True)
def get_shipping_rates():
    try:
        # Step 1: Get user input (quoteInput)
        raw_data = frappe.request.get_data(as_text=True)
        if not raw_data:
            frappe.throw("No quote input data received.")
        quote_input = json.loads(raw_data)

        # Step 2: Build Norsk quoteData using input
        quote_data = {
            "DepartureCountryCode": "GB",
            "ArrivalCountryCode": quote_input.get("destinationCountry") or quote_input.get("receiverCountry") or "AU",
            "ArrivalPostcode": quote_input.get("destinationZipcode") or quote_input.get("receiverZipcode") or "4825",
            "ArrivalLocation": quote_input.get("destinationTown") or quote_input.get("receiverTown") or "MOUNT ISA",
            "PaymentCurrencyCode": "USD",
            "WeightMeasure": "KG",
            "Weight": float(quote_input.get("boxweight", 1)),
            "NumofItem": 1,
            "ServiceType": "EN",
            "DimensionUnit": "CM",
            "CustomCurrencyCode": "USD",
            "CustomAmount": 50.00,
            "Items": [
                {
                    "Weight": float(quote_input.get("boxweight", 1)),
                    "Length": float(quote_input.get("boxlength", 1)),
                    "Width": float(quote_input.get("boxwidth", 1)),
                    "Height": float(quote_input.get("boxheight", 1)),
                    "CubicWeight": float(quote_input.get("boxweight", 1)),
                }
            ]
        }

        # Step 3: Prepare request
        settings = get_skynet_settings()
        url = f"{settings['api_url']}rates"
        headers = get_auth_headers()
        headers["Content-Type"] = "application/json"

        # Step 4: Send request
        response = requests.post(url, headers=headers, json=quote_data, timeout=30)
        response.raise_for_status()

        # Step 5: Return parsed response
        return response.json()

    except requests.exceptions.HTTPError as e:
        frappe.log_error("Skynet API HTTP Error (/rates)", f"{e}\nResponse: {getattr(response, 'text', None)}")
        return {"error": "HTTPError", "message": str(e), "response": getattr(response, "text", None)}

    except requests.exceptions.RequestException as e:
        frappe.log_error("Skynet API Request Error (/rates)", str(e))
        return {"error": "RequestException", "message": str(e)}

    except Exception as e:
        frappe.log_error("Unexpected Error (/rates)", frappe.get_traceback())
        return {"error": "Exception", "message": str(e)}
    
@frappe.whitelist(allow_guest=True)
def shipment():
    try:
        # Step 1: Get user input (shipmentInput)
        raw_data = frappe.request.get_data(as_text=True)
        if not raw_data:
            frappe.throw("No shipment input data received.")
        shipment_input = json.loads(raw_data)

        # Step 2: Prepare request
        settings = get_skynet_settings()
        url = f"{settings['api_url']}shipments"
        headers = get_auth_headers()
        headers["Content-Type"] = "application/json"

        # Step 3: Send request
        response = requests.post(url, headers=headers, json=shipment_input, timeout=30)
        response.raise_for_status()

        # Step 4: Process the response and store in ERPNext
        resp_json = response.json()
        
        # The API might return a list directly, or a dict with a "message" key.
        if isinstance(resp_json, dict):
            message = resp_json.get("message")
        else:
            message = resp_json
        
        if not message or not isinstance(message, list) or not message[0]:
            frappe.throw("Invalid response format from Skynet API.")
            
        shipment_details = message[0]
        shipment_number = shipment_details.get("ShipmentNumber")
        label_url = shipment_details.get("LabelURL")

        if not shipment_number or not label_url:
            frappe.throw("ShipmentNumber or LabelURL not found in Skynet response.")

        # Download the label from the URL
        label_response = requests.get(label_url)
        label_response.raise_for_status()
        label_content = label_response.content

        # Store into ERPNext Doctype
        doc = frappe.new_doc("Shipment Booking")
        doc.shipment_barcode = shipment_number
        doc.user = frappe.session.user
        doc.insert(ignore_permissions=True)
        
        # Create a file document for the label
        file_name = f"Shipment_Label_{shipment_number}.pdf"
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": file_name,
            "attached_to_doctype": "Shipment Booking",
            "attached_to_name": doc.name,
            "is_private": 1,
            "content": label_content
        })
        file_doc.insert(ignore_permissions=True)

        # Return success response
        return {
            "success": True,
            "shipment_id": doc.name,
            "barcode": shipment_number,
            "label_url": file_doc.file_url  # ERPNext file URL
        }

    except requests.exceptions.HTTPError as e:
        frappe.log_error("Skynet API HTTP Error (/shipments)", f"{e}\nResponse: {getattr(response, 'text', None)}")
        return {"error": "HTTPError", "message": str(e), "response": getattr(response, "text", None)}

    except requests.exceptions.RequestException as e:
        frappe.log_error("Skynet API Request Error (/shipments)", str(e))
        return {"error": "RequestException", "message": str(e)}

    except Exception as e:
        frappe.log_error("Unexpected Error (/shipments)", frappe.get_traceback())
        return {"error": "Exception", "message": str(e)}