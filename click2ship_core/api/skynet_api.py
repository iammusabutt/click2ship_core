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
def rates():
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

def store_shipment_details(doc, session_data):
    
    # 1. Safely retrieve the booking details. Assumes booking is a list 
    # and we want the first item, as per the provided JSON structure.
    booking_list = session_data.get("booking", [])
    if not booking_list:
        # Handle case where booking list is empty or missing
        print("Warning: 'booking' list is empty or missing in session_data.")
        return doc
        
    booking_details = booking_list[0]
    quote = session_data.get("quote", {})

    # --- Map shipper details (from 'SenderDetails' in your JSON) ---
    shipper = booking_details.get("SenderDetails", {})
    doc.shipper_name = shipper.get("SenderName")
    doc.shipper_company = shipper.get("SenderCompanyName")
    doc.country_code = shipper.get("SenderCountryCode")
    doc.shipper_address1 = shipper.get("SenderAdd1")
    doc.shipper_address2 = shipper.get("SenderAdd2")
    doc.shipper_address3 = shipper.get("SenderAdd3")
    doc.shipper_city = shipper.get("SenderAddCity")
    doc.shipper_state = shipper.get("SenderAddState")
    doc.shipper_postal_code = shipper.get("SenderAddPostcode")
    doc.shipper_phone_number = shipper.get("SenderPhone")
    doc.shipper_email = shipper.get("SenderEmail")
    doc.shipper_fax = shipper.get("SenderFax")

    # --- Map receiver details (from 'ReceiverDetails' in your JSON) ---
    receiver = booking_details.get("ReceiverDetails", {})
    doc.receiver_name = receiver.get("ReceiverName")
    doc.receiver_company = receiver.get("ReceiverCompanyName")
    doc.receiver_country = receiver.get("ReceiverCountryCode")
    doc.receiver_address1 = receiver.get("ReceiverAdd1")
    doc.receiver_address2 = receiver.get("ReceiverAdd2")
    doc.receiver_address3 = receiver.get("ReceiverAdd3")
    doc.receiver_city = receiver.get("ReceiverAddCity")
    doc.receiver_state = receiver.get("ReceiverAddState")
    doc.receiver_postal_code = receiver.get("ReceiverAddPostcode")
    doc.receiver_phone_number = receiver.get("ReceiverPhone") # Using ReceiverPhone as it's typically primary
    doc.receiver_email = receiver.get("ReceiverEmail")
    doc.receiver_fax = receiver.get("ReceiverFax")

    # --- Map financial and service details (from 'quote' in session_data) ---
    # NOTE: These fields rely on the 'quote' key being present in session_data.
    doc.base_cost = quote.get("BaseCost") or ""
    doc.fuel_cost = quote.get("FuelCost") or ""
    doc.insurance_cost = ""  # This appears to be a hardcoded empty string
    doc.air_freight_cost = quote.get("ExtraCosts", {}).get("AirFreightCost")
    doc.local_processing_cost = quote.get("ExtraCosts", {}).get("LocalProcessingCost")
    doc.local_custom_charges = quote.get("ExtraCosts", {}).get("LocalCustomCharges")
    doc.transhipping_clearance = quote.get("ExtraCosts", {}).get("DestinationTranshippingClearance")
    doc.total_extra_cost = quote.get("ExtraCosts", {}).get("ExtraTotal")
    doc.total_cost_without_additional_cost = quote.get("TotalCost")
    doc.grand_total_including_additional_cost = quote.get("AdjustedTotalCost")

    doc.shipping_service_name = quote.get("ServiceName")
    doc.shipping_service_code = quote.get("ServiceCode")

    # --- Map products to child table (from 'ShipmentResponseItem' in your JSON) ---
    doc.set("items", [])  # Clear existing items
    
    # The products are nested under PackageDetails -> ShipmentResponseItem -> Pieces
    shipment_items = booking_details.get("PackageDetails", {}).get("ShipmentResponseItem", [])
    
    for shipment_item in shipment_items:
        # Each "item" may contain one or more "Pieces" (i.e., Products)
        pieces = shipment_item.get("Pieces", []) 
        
        for product in pieces:
            doc.append("items", {
                # Note: Mapping from your provided JSON keys here:
                "item_name": product.get("GoodsDescription"),
                "item_description": product.get("GoodsDescription"),
                "item_quantity": product.get("Quantity"),
                "item_value": product.get("CustomsValue"), # Your JSON uses 'CustomsValue'
                "item_weight": product.get("Weight"),
                "item_currency": product.get("CurrencyCode"),
                "item_country_of_manufacture": product.get("ManufactureCountryCode"),
                "item_hscode": product.get("HarmonisedCode")
            })
    return doc
        
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
        
        # Get session data
        session_key = frappe.session.sid
        session_data = frappe.cache().get_value(f"session_data:{session_key}") or {}

        # Download the label from the URL
        label_response = requests.get(label_url)
        label_response.raise_for_status()
        label_content = label_response.content

        # Store into ERPNext Doctype
        doc = frappe.new_doc("Shipment Booking")
        doc = store_shipment_details(doc, session_data)
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
            "shipment_booked_with": "Skynet",
            "booking_type": "Via UK",
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