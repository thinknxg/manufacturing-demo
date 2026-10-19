import contextlib
import io
import json
import os
import runpy
import shutil
import tempfile

import frappe


def _prepare(cfg):
    companies = frappe.get_all("Company", fields=["name", "abbr"])
    if not companies:
        raise Exception("No Company found on this site")
    comp = next((c for c in companies if c.name == cfg.get("company")), None)
    if not comp:
        default = frappe.defaults.get_global_default("company")
        comp = next((c for c in companies if c.name == default), companies[0])
    cfg["company"] = comp.name

    wh = cfg.get("warehouses")
    if isinstance(wh, dict):
        for key, val in list(wh.items()):
            if not isinstance(val, str):
                continue
            base = val.rsplit(" - ", 1)[0]
            name = f"{base} - {comp.abbr}"
            if not frappe.db.exists("Warehouse", name):
                frappe.get_doc(
                    {"doctype": "Warehouse", "warehouse_name": base, "company": comp.name}
                ).insert(ignore_permissions=True)
            wh[key] = name

    for g in ["Raw Materials", "Sub Assemblies", "Finished Goods", "Consumables"]:
        if not frappe.db.exists("Item Group", g):
            frappe.get_doc(
                {"doctype": "Item Group", "item_group_name": g,
                 "parent_item_group": "All Item Groups", "is_group": 0}
            ).insert(ignore_permissions=True)

    for u in ["Nos", "Kg", "Litre"]:
        if not frappe.db.exists("UOM", u):
            frappe.get_doc({"doctype": "UOM", "uom_name": u}).insert(ignore_permissions=True)
    return cfg


def _create_operations(data_dir):
    import csv

    with open(os.path.join(data_dir, "operations.csv"), newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames
        key = next((c for c in ("name", "operation", "operation_name") if c in cols), cols[0])
        for row in reader:
            name = (row.get(key) or "").strip()
            if not name or frappe.db.exists("Operation", name):
                continue
            doc = frappe.new_doc("Operation")
            doc.__newname = name
            doc.name = name
            doc.insert(ignore_permissions=True)
            print(f"OK Operation (pre-created): {name}")


def load_demo_data():
    src = frappe.get_app_path("manufacturing_demo", "data")
    dst = os.path.join(tempfile.mkdtemp(), "data")
    shutil.copytree(src, dst)

    cfg_path = os.path.join(dst, "config.json")
    with open(cfg_path, encoding="utf-8-sig") as f:
        cfg = json.load(f)
    cfg = _prepare(cfg)
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

    _create_operations(dst)

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        runpy.run_path(os.path.join(dst, "import_dataset.py"), run_name="__main__")
    frappe.db.commit()
    out = buf.getvalue()
    print(out)
    frappe.log_error(title="manufacturing_demo import log", message=out or "no output")


def after_install():
    try:
        load_demo_data()
    except Exception:
        frappe.log_error(title="manufacturing_demo import failed")
