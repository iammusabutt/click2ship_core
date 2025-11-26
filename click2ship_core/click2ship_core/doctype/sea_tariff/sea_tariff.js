// Copyright (c) 2025, DrCodeX Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Sea Tariff", {
    refresh: function(frm) {
        // Origin seaport filter
        frm.set_query("origin_seaport_code", function() {
            return {
                query: "click2ship_core.click2ship_core.doctype.sea_tariff.sea_tariff.origin_seaport_code_query",
                filters: {
                    country: frm.doc.origin_country
                }
            };
        });

        // Destination airport filter
        frm.set_query("destination_seaport_code", function() {
            return {
                query: "click2ship_core.click2ship_core.doctype.sea_tariff.sea_tariff.origin_seaport_code_query",
                filters: {
                    country: frm.doc.destination_country
                }
            };
        });
    },

    // Auto-fill origin airport if only one
    origin_country: function(frm) {
        frm.set_value("origin_seaport_code", ""); // reset
        if (frm.doc.origin_country) {
            frappe.call({
                method: "click2ship_core.click2ship_core.doctype.sea_tariff.sea_tariff.get_seaport_if_single",
                args: {
                    country: frm.doc.origin_country
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value("origin_seaport_code", r.message); // always code
                    }
                }
            });
        }
    },

    // Auto-fill destination airport if only one
    destination_country: function(frm) {
        frm.set_value("destination_seaport_code", ""); // reset
        if (frm.doc.destination_country) {
            frappe.call({
                method: "click2ship_core.click2ship_core.doctype.sea_tariff.sea_tariff.get_seaport_if_single",
                args: {
                    country: frm.doc.destination_country
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value("destination_seaport_code", r.message); // always code
                    }
                }
            });
        }
    }
});
