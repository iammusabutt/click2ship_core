# Copyright (c) 2025, DrCodeX Technologies and contributors
# For license information, please see license.txt

import frappe
import requests
import json

class CarrierConnection(frappe.model.document.Document):
    def validate(self):
        if not self.carrier_id:
            self.carrier_id = self.carrier_name

    def on_submit(self):
        self.send_to_karrio()

    def get_credentials_dict(self):
        """Convert child table entries to a key-value dict."""
        creds = {}
        for row in self.credentials:
            creds[row.key] = row.value
        return creds

    def send_to_karrio(self):
        karrio_url = frappe.db.get_single_value("Karrio Settings", "base_api_url")
        endpoint = f"{karrio_url}/v1/connections"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {frappe.db.get_single_value('Karrio Settings', 'api_token')}"
        }

        if self.test_mode:
            headers["x-test-mode"] = "true"

        payload = {
            "carrier_name": self.carrier_name,
            "carrier_id": self.carrier_id,
            "credentials": self.get_credentials_dict(),
            "active": self.active,
            "test_mode": self.test_mode
        }

        try:
            response = requests.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
            self.api_response = response.text
            frappe.msgprint(f"Carrier connection created successfully! ({response.status_code})")
        except requests.exceptions.RequestException as e:
            frappe.throw(f"Karrio API Error: {str(e)}")
