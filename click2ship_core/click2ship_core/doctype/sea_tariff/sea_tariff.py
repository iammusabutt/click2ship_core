# Copyright (c) 2025, DrCodeX Technologies and contributors
# For license information, please see license.txt


import frappe
import json
from frappe.model.document import Document


class SeaTariff(Document):
	pass
	
@frappe.whitelist()
def origin_seaport_code_query(doctype, txt, searchfield, start, page_len, filters=None):
    """Custom query for airport link field: store airport_code, show code + name"""
    if isinstance(filters, str):
        try:
            filters = json.loads(filters)
        except Exception:
            filters = {}
    filters = filters or {}

    country = filters.get("country")
    if not country:
        return []

    searports = frappe.get_all(
        "Saeport",
        filters={"country": country},
        fields=["seaport_code", "seaport_name"],
        or_filters=[
            ["seaport_code", "like", f"%{txt}%"],
            ["seaport_name", "like", f"%{txt}%"]
        ],
        order_by="seaport_code asc",
        start=start,
        page_length=page_len
    )

    # return value = airport_code (Link field stores this)
    # label = "CODE - Airport Name"
    return [(a["seasport_code"], f"{a['seaport_code']} - {a['seaport_name']}") for a in seaports]


@frappe.whitelist()
def get_seaport_if_single(country):
    """Return airport_code if only one airport exists for given city"""
    seaports = frappe.get_all(
        "Seaport",
        filters={"country": country},
        fields=["seaport_code"]
    )
    if len(seaports) == 1:
        return seaports[0]["seaport_code"]
    return None



