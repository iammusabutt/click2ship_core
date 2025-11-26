// Copyright (c) 2025, DrCodeX Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Air Tariff", {
    refresh: function(frm) {
        // Origin airport filter
        frm.set_query("origin_airport_code", function() {
            return {
                query: "click2ship_core.click2ship_core.doctype.air_tariff.air_tariff.origin_airport_code_query",
                filters: {
                    city: frm.doc.origin_city
                }
            };
        });

        // Destination airport filter
        frm.set_query("destination_airport_code", function() {
            return {
                query: "click2ship_core.click2ship_core.doctype.air_tariff.air_tariff.origin_airport_code_query",
                filters: {
                    city: frm.doc.destination_city
                }
            };
        });
    },

    // Auto-fill origin airport if only one
    origin_city: function(frm) {
        frm.set_value("origin_airport_code", ""); // reset
        if (frm.doc.origin_city) {
            frappe.call({
                method: "click2ship_core.click2ship_core.doctype.air_tariff.air_tariff.get_airport_if_single",
                args: {
                    city: frm.doc.origin_city
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value("origin_airport_code", r.message); // always code
                    }
                }
            });
        }
    },

    // Auto-fill destination airport if only one
    destination_city: function(frm) {
        frm.set_value("destination_airport_code", ""); // reset
        if (frm.doc.destination_city) {
            frappe.call({
                method: "click2ship_core.click2ship_core.doctype.air_tariff.air_tariff.get_airport_if_single",
                args: {
                    city: frm.doc.destination_city
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value("destination_airport_code", r.message); // always code
                    }
                }
            });
        }
    }
});
