import frappe

from manufacturing_demo.install import load_demo_data


def execute():
    try:
        load_demo_data()
    except Exception:
        frappe.log_error(title="manufacturing_demo import v4 failed")
