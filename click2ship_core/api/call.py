import frappe
import json
import concurrent.futures
import requests


# -------------------------------------------------------------
# Main Combined API Endpoint
# -------------------------------------------------------------
@frappe.whitelist(allow_guest=True)
def rates():
    """
    Fetch shipping quotes from Norsk and Skynet APIs in parallel
    using HTTP calls (thread-safe) and return a combined, normalized response.
    """
    try:
        # Step 1: Read frontend data
        raw_data = frappe.request.get_data(as_text=True)
        if not raw_data:
            frappe.throw("No quote input data received.")
        quote_input = json.loads(raw_data)

        # Step 2: Precompute base_url (must happen before threads)
        base_url = frappe.utils.get_url()

        # Step 3: Parallel API calls
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_norsk = executor.submit(
                call_internal_api,
                "click2ship_core.api.norsk_api.get_norsk_shipping_quote",
                quote_input,
                base_url
            )
            future_skynet = executor.submit(
                call_internal_api,
                "click2ship_core.api.skynet_api.get_shipping_rates",
                quote_input,
                base_url
            )
            future_karrio = executor.submit(
                call_internal_api,
                "click2ship_core.api.karrio_api.get_rates",
                quote_input,
                base_url
            )

            norsk_response = future_norsk.result()
            skynet_response = future_skynet.result()
            karrio_response = future_karrio.result()

        # Step 4: Normalize and merge
        route_type = quote_input.get("route_type", "uk")  # 'uk' or 'uae'
        norsk_quotes = normalize_quotes(norsk_response, "Norsk", route_type)
        skynet_quotes = normalize_quotes(skynet_response, "Skynet", route_type)
        karrio_quotes = normalize_quotes(karrio_response, "Karrio", route_type)
        combined_quotes = norsk_quotes + skynet_quotes + karrio_quotes

        # Step 5: Return unified response
        return {
            "Quotes": combined_quotes,
            "norsk_response": norsk_response,
            "skynet_response": skynet_response,
            "karrio_response": karrio_response
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "rates API Error")
        frappe.throw(str(e))


# -------------------------------------------------------------
# Helper: Call internal APIs via HTTP (thread-safe)
# -------------------------------------------------------------
def call_internal_api(api_path, quote_input, base_url):
    """
    Makes a POST request to another frappe API endpoint using the given base_url.
    Thread-safe, no frappe.local usage inside threads.
    """
    url = f"{base_url}/api/method/{api_path}"

    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, data=json.dumps(quote_input), headers=headers, timeout=60)

        if response.status_code >= 400:
            frappe.log_error(response.text, f"Error calling {api_path}")
            return {"error": f"Error calling {api_path}: {response.text}"}

        return response.json()
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Network error calling {api_path}")
        return {"error": f"Network error calling {api_path}: {str(e)}"}


# -------------------------------------------------------------
# Normalizer
# -------------------------------------------------------------
def normalize_quotes(raw_data, provider, via="uk"):
    quotes = []
    msg = raw_data.get("message", {})

    # Load cost configuration
    fm_settings = get_first_mile_settings(via)

    def apply_extra_costs(q):
        """Apply additional costs based on First Mile Settings."""
        weight = float(q.get("ChargeableWeight", 0.0) or 0.0)
        base_total = float(q.get("TotalCost", 0.0) or 0.0)

        # Use rates from settings
        air_freight_cost = float(fm_settings["air_freight_cost"]) * weight
        local_processing_cost = float(fm_settings["local_processing_cost"])
        local_custom_charges = float(fm_settings["local_custom_charges"])
        dest_tranship_clearance = float(fm_settings["transshipping_clearance"]) * weight

        extra_total = (
            air_freight_cost +
            local_processing_cost +
            local_custom_charges +
            dest_tranship_clearance
        )
        new_total = base_total + extra_total

        q["ExtraCosts"] = {
            "AirFreightCost": air_freight_cost,
            "LocalProcessingCost": local_processing_cost,
            "LocalCustomCharges": local_custom_charges,
            "DestinationTranshippingClearance": dest_tranship_clearance,
            "ExtraTotal": extra_total
        }
        q["AdjustedTotalCost"] = new_total
        return q

    # --- NORSK ---
    if "Quotes" in msg:
        for q in msg.get("Quotes", []):
            normalized = {
                "Provider": provider,
                "ServiceName": q.get("ServiceName"),
                "ServiceCode": q.get("ServiceCode"),
                "TransitTime": q.get("TransitTime"),
                "PrettyTransitTime": q.get("PrettyTransitTime"),
                "ChargeableWeight": q.get("ChargeableWeight"),
                "BaseCost": q.get("BaseCost"),
                "FuelCost": q.get("FuelCost"),
                "TotalCost": q.get("TotalCost"),
                "Currency": msg.get("Currency", "USD"),
                "Costs": q.get("Costs", []),
            }
            quotes.append(apply_extra_costs(normalized))

    # --- SKYNET ---
    elif "PricingResponseDetails" in msg:
        for item in msg.get("PricingResponseDetails", []):
            normalized = {
                "Provider": provider,
                "ServiceName": "Skynet Express",
                "ServiceCode": item.get("ProductCode", "SKY"),
                "TransitTime": item.get("TransitTime", "2–3 days"),
                "PrettyTransitTime": item.get("PrettyTransitTime", "2–3 days"),
                "ChargeableWeight": item.get("ChargeableWeight", 1.0),
                "BaseCost": item.get("BasicAmount", 0.0),
                "FuelCost": item.get("FSAmount", 0.0),
                "TotalCost": item.get("TotalAmount", 0.0),
                "Currency": item.get("CurrencyCode", "USD"),
                "Costs": [
                    {
                        "Reference": "Base + Fuel",
                        "BaseCost": item.get("BasicAmount", 0.0),
                        "FuelCost": item.get("FSAmount", 0.0),
                        "TotalCost": item.get("TotalAmount", 0.0)
                    }
                ]
            }
            quotes.append(apply_extra_costs(normalized))

    # --- KARRIO ---
    elif "rates" in msg:
        for rate in msg.get("rates", []):
            # Extract base and fuel cost from extra_charges if available
            base_charge = 0.0
            fuel_charge = 0.0
            for c in rate.get("extra_charges", []):
                name = c.get("name", "").lower()
                if "base" in name:
                    base_charge += float(c.get("amount", 0.0))
                elif "fuel" in name:
                    fuel_charge += float(c.get("amount", 0.0))

            normalized = {
                "Provider": provider,
                "ServiceName": rate.get("meta", {}).get("service_name") or rate.get("service"),
                "ServiceCode": rate.get("service"),
                "TransitTime": rate.get("transit_days", None),
                "PrettyTransitTime": f"{rate.get('transit_days', 'N/A')} days" if rate.get("transit_days") else "N/A",
                "ChargeableWeight": 1.0,  # Karrio response doesn’t include weight per rate
                "BaseCost": base_charge,
                "FuelCost": fuel_charge,
                "TotalCost": rate.get("total_charge", 0.0),
                "Currency": rate.get("currency", "USD"),
                "Costs": rate.get("extra_charges", []),
            }
            quotes.append(apply_extra_costs(normalized))

    return quotes




# -------------------------------------------------------------
# First Mile Settings
# -------------------------------------------------------------
def get_first_mile_settings(via="uk"):
    """Fetch First Mile Settings based on region type (uk or uae)."""
    settings = frappe.get_single("First Mile Settings")

    # Normalize key prefix
    suffix = "_via_uk" if via.lower() == "uk" else "_via_uae"

    return {
        "air_freight_cost": settings.get(f"air_freight_cost{suffix}") or 0,
        "local_processing_cost": settings.get(f"local_processing_cost{suffix}") or 0,
        "local_custom_charges": settings.get(f"local_custom_charges{suffix}") or 0,
        "transshipping_clearance": settings.get(f"transshipping_clearance{suffix}") or 0,
    }

# -------------------------------------------------------------
# Save data in the current user's server session
# -------------------------------------------------------------
@frappe.whitelist(allow_guest=True)
def session_save():
    try:
        # Get session data from cache or start with empty dict
        session_key = frappe.session.sid
        session_data = frappe.cache().get_value(f"session_data:{session_key}") or {}

        # Get quote
        quote = frappe.form_dict.get("quote")
        if quote:
            if isinstance(quote, str):
                import json
                quote = json.loads(quote)
            session_data["quote"] = quote

        # Get booking payload
        booking = frappe.form_dict.get("booking")
        if booking:
            if isinstance(booking, str):
                import json
                booking = json.loads(booking)
            session_data["booking"] = booking

        if not session_data:
            frappe.throw("No session data received.")

        # Store in cache using a unique key (e.g., session_id)
        frappe.cache().set_value(f"session_data:{session_key}", session_data, expires_in_sec=3600)

        return {
            "status": "success",
            "data": session_data
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "session_save error")
        return {"status": "error", "message": str(e)}


# -------------------------------------------------------------
# Retrieve the data from current user's server session
# -------------------------------------------------------------
@frappe.whitelist(allow_guest=True)
def session_data():
    try:
        session_key = frappe.session.sid
        session_data = frappe.cache().get_value(f"session_data:{session_key}") or {}

        return {"status": "success", "data": session_data}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "session_data error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist(allow_guest=True)
def book():
    """
    Generic booking router API.
    Detects provider and routes to the correct internal function.
    """
    try:
        raw_data = frappe.request.get_data(as_text=True)
        if not raw_data:
            frappe.throw("No booking payload received.")

        payload = json.loads(raw_data)

        provider = payload.get("provider")
        booking_details = payload.get("booking_details")

        if not provider:
            frappe.throw("Provider is missing.")
        if not booking_details:
            frappe.throw("Booking details are missing.")

        # Map provider to internal functions
        provider_map = {
            "norsk": "click2ship.api.norsk_api.book_shipment",
            "skynet": "click2ship.api.skynet_api.book_shipment",
            "karrio": "click2ship.api.karrio_api.book_shipment"
        }

        provider = provider.lower()

        if provider not in provider_map:
            frappe.throw(f"Unsupported provider: {provider}")

        # Dynamically import the right function
        module_path = provider_map[provider]
        module_name, func = module_path.rsplit('.', 1)

        module = __import__(module_name, fromlist=[func])
        booking_function = getattr(module, func)

        # Call provider-specific booking function
        result = booking_function(booking_details)

        return {
            "status": "success",
            "provider": provider,
            "result": result
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Booking Router Error")
        raise e
