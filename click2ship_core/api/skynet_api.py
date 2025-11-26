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
        frappe.log_error(f"Skynet API HTTP Error (/rates): {str(e)}", "Skynet API")
        return {"error": "HTTPError", "message": str(e), "response": getattr(response, "text", None)}

    except requests.exceptions.RequestException as e:
        frappe.log_error(f"Skynet API Request Error (/rates): {str(e)}", "Skynet API")
        return {"error": "RequestException", "message": str(e)}

    except Exception as e:
        frappe.log_error(f"Unexpected Error (/rates): {frappe.get_traceback()}", "Skynet API")
        return {"error": "Exception", "message": str(e)}
    
    