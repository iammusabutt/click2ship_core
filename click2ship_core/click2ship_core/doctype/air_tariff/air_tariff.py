# Copyright (c) 2025, DrCodeX Technologies and contributors
# For license information, please see license.txt

import frappe
import json
from frappe.model.document import Document

class AirTariff(Document):
    pass

@frappe.whitelist()
def origin_airport_code_query(doctype, txt, searchfield, start, page_len, filters=None):
    """Custom query for airport link field: store airport_code, show code + name"""
    if isinstance(filters, str):
        try:
            filters = json.loads(filters)
        except Exception:
            filters = {}
    filters = filters or {}

    city = filters.get("city")
    if not city:
        return []

    airports = frappe.get_all(
        "Airport",
        filters={"city": city},
        fields=["airport_code", "airport_name"],
        or_filters=[
            ["airport_code", "like", f"%{txt}%"],
            ["airport_name", "like", f"%{txt}%"]
        ],
        order_by="airport_code asc",
        start=start,
        page_length=page_len
    )

    # return value = airport_code (Link field stores this)
    # label = "CODE - Airport Name"
    return [(a["airport_code"], f"{a['airport_code']} - {a['airport_name']}") for a in airports]


@frappe.whitelist()
def get_airport_if_single(city):
    """Return airport_code if only one airport exists for given city"""
    airports = frappe.get_all(
        "Airport",
        filters={"city": city},
        fields=["airport_code"]
    )
    if len(airports) == 1:
        return airports[0]["airport_code"]
    return None



