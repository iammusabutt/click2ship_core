import frappe
import json
from frappe.utils import now_datetime
import pytz

def get_context(context):
    context.csrf_token = frappe.sessions.get_csrf_token()

