import requests
import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def get_air_tariff(origin_airport_code, destination_airport_code, weight: float = None):

    # Fetch all matching Air Tariff documents
    names = frappe.get_all(
        "Air Tariff",
        filters={
            "origin_airport_code": origin_airport_code,
            "destination_airport_code": destination_airport_code
        },
        pluck="name"
    )

    quotes = []

    for name in names:
        doc = frappe.get_doc("Air Tariff", name)

        matched_rate = None
        if weight is not None:
            try:
                w = float(weight)
            except:
                w = None

            if w is not None:
                # Sort child table rows by weight (upper limit)
                slabs = sorted(
                    [row for row in doc.air_tariff_rate if row.weight],
                    key=lambda x: float(x.weight)
                )

                # Loop through slabs and pick the first one that matches the weight
                for row in slabs:
                    try:
                        upper_limit = float(row.weight)
                    except:
                        continue

                    if w <= upper_limit:
                        matched_rate = row.rate
                        break

        # Prepare result item
        result_item = {
            "rate": matched_rate if matched_rate is not None else "No rate found",
            "airline": doc.airline
            # Add more fields here if needed, e.g.:
            # "service_type": doc.air_freight_service_type,
            # "tariff_name": doc.name
        }

        quotes.append(result_item)

    return quotes

@frappe.whitelist(allow_guest=True)
def get_airports():
    return frappe.get_all(
        "Airport",
        fields=["name", "airport_code", "airport_name", "city"],
        order_by="airport_code asc"
    )
