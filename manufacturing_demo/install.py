import runpy

import frappe


def load_demo_data():
    path = frappe.get_app_path("manufacturing_demo", "data", "import_dataset.py")
    runpy.run_path(path, run_name="__main__")
    frappe.db.commit()


def after_install():
    try:
        load_demo_data()
    except Exception:
        frappe.log_error(title="manufacturing_demo: demo data import failed")
        print("manufacturing_demo: import failed, run load_demo_data() manually")
