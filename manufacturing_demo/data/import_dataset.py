# Run inside `bench --site <site> console` after editing config.json.
# Example: exec(open("/path/to/import_dataset.py").read())
import csv, json, os, frappe
from frappe.utils import getdate, nowdate

ROOT = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(ROOT, "config.json"), encoding="utf-8") as f:
    CFG = json.load(f)
COMPANY = CFG["company"]
WH = CFG["warehouses"]

def rows(file):
    with open(os.path.join(ROOT, file), newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def warn(msg):
    print("WARNING:", msg)

def has_field(doctype, fieldname):
    try:
        return frappe.get_meta(doctype).has_field(fieldname)
    except Exception:
        return False

def set_if_field(doc, fieldname, value):
    if value not in (None, "") and has_field(doc.doctype, fieldname):
        doc.set(fieldname, value)

def save_doc(doctype, name, fields, children=None, submit=False):
    """Create/update a doc by name; only assign fields available in this site's schema."""
    if not frappe.db.exists(doctype, name):
        doc = frappe.new_doc(doctype)
        if name and has_field(doctype, "name") and doctype not in ("Item",):
            # Most naming series doctypes should be allowed to autoname.
            pass
    else:
        doc = frappe.get_doc(doctype, name)
    for k, v in fields.items():
        if v in (None, ""):
            continue
        if has_field(doctype, k):
            doc.set(k, v)
    if children:
        for table_field, child_rows in children.items():
            if not has_field(doctype, table_field):
                warn(f"{doctype}.{table_field} not available; skipped child rows")
                continue
            doc.set(table_field, [])
            for child in child_rows:
                doc.append(table_field, child)
    try:
        doc.save(ignore_permissions=True)
        if submit and doc.docstatus == 0:
            doc.submit()
        print(f"OK {doctype}: {doc.name}")
        return doc
    except Exception as e:
        warn(f"Could not save {doctype} {name or ''}: {e}")
        return None

# Company and warehouse validation
if not frappe.db.exists("Company", COMPANY):
    raise Exception(f"Company '{COMPANY}' does not exist. Edit config.json first.")
for key in ("source", "wip", "finished_goods"):
    wh = WH[key]
    if not frappe.db.exists("Warehouse", wh):
        warn(f"Warehouse '{wh}' does not exist. Create it under {COMPANY} before importing.")

# Item Groups (create only when parent exists)
for r in rows("item_groups.csv"):
    if not frappe.db.exists("Item Group", r["item_group"]):
        if not frappe.db.exists("Item Group", r["parent_item_group"]):
            warn(f"Parent Item Group missing for {r['item_group']}; skipped")
            continue
        save_doc("Item Group", r["item_group"], {
            "item_group_name": r["item_group"],
            "parent_item_group": r["parent_item_group"],
            "is_group": int(r["is_group"])
        })

# Items
for r in rows("items.csv"):
    fields = {
        "item_code": r["item_code"],
        "item_name": r["item_name"],
        "item_group": r["item_group"],
        "stock_uom": r["stock_uom"],
        "is_stock_item": int(r["is_stock_item"]),
        "is_purchase_item": int(r["is_purchase_item"]),
        "is_sales_item": int(r["is_sales_item"]),
        "include_item_in_manufacturing": int(r["include_item_in_manufacturing"]),
        "description": r["description"]
    }
    if has_field("Item", "default_warehouse"):
        fields["default_warehouse"] = WH["source"]
    save_doc("Item", r["item_code"], fields)

# Workstations
for r in rows("workstations.csv"):
    save_doc("Workstation", r["workstation_name"], {
        "workstation_name": r["workstation_name"],
        "workstation_description": r["workstation_description"],
        "description": r["description"],
        "is_group": int(r["is_group"]),
        "hour_rate": float(r["hour_rate"])
    })

# Operations
for r in rows("operations.csv"):
    save_doc("Operation", r["operation"], {
        "operation": r["operation"],
        "workstation": r["workstation"],
        "time_in_mins": float(r["time_in_mins"]),
        "operating_cost": float(r["operating_cost"]),
        "description": r["description"]
    })

# BOM child records are composed into the parent document. BOMs are created in subassembly-first order.
bom_items = {}
for r in rows("bom_items.csv"):
    bom_items.setdefault(r["bom"], []).append({
        "item_code": r["item_code"],
        "qty": float(r["qty"]),
        "include_item_in_manufacturing": int(r["include_item_in_manufacturing"]),
        "do_not_explode": int(r["do_not_explode"])
    })
bom_ops = {}
for r in rows("bom_operations.csv"):
    bom_ops.setdefault(r["bom"], []).append({
        "operation": r["operation"],
        "time_in_mins": float(r["time_in_mins"]),
        "operating_cost": float(r["operating_cost"]),
        "sequence_id": int(r["sequence_id"])
    })

for r in rows("bom_headers.csv"):
    # ERPNext BOM uses autoname in many configurations; the requested name is assigned only if supported.
    fields = {
        "item": r["item"],
        "quantity": float(r["quantity"]),
        "is_active": int(r["is_active"]),
        "is_default": int(r["is_default"]),
        "company": COMPANY,
        "description": r["description"],
        "with_operations": 1 if bom_ops.get(r["name"]) else 0
    }
    doc = None
    try:
        existing = frappe.db.exists("BOM", r["name"])
        if existing:
            doc = frappe.get_doc("BOM", r["name"])
        else:
            doc = frappe.new_doc("BOM")
            # Standard BOM autoname is commonly based on item and naming series; custom name is not forced.
        for k, v in fields.items():
            if has_field("BOM", k):
                doc.set(k, v)
        for table_field, source in (("items", bom_items.get(r["name"], [])),
                                    ("operations", bom_ops.get(r["name"], []))):
            if has_field("BOM", table_field):
                doc.set(table_field, [])
                for child in source:
                    doc.append(table_field, child)
        doc.save(ignore_permissions=True)
        if CFG.get("submit_boms", False) and doc.docstatus == 0:
            doc.submit()
        print(f"OK BOM: {doc.name} (requested {r['name']})")
    except Exception as e:
        warn(f"Could not save BOM requested as {r['name']}: {e}")

# Routing is optional and schema varies by installed ERPNext version.
if frappe.db.exists("DocType", "Routing"):
    grouped = {}
    for r in rows("routing.csv"):
        grouped.setdefault(r["routing_name"], []).append(r)
    for routing_name, rr in grouped.items():
        try:
            d = frappe.new_doc("Routing")
            if has_field("Routing", "routing_name"): d.routing_name = routing_name
            if has_field("Routing", "operations"):
                for x in rr:
                    child = {"operation": x["operation"], "sequence_id": int(x["sequence_id"])}
                    d.append("operations", child)
            if has_field("Routing", "description"): d.description = rr[0]["description"]
            d.save(ignore_permissions=True)
            print("OK Routing:", d.name)
        except Exception as e:
            warn(f"Routing {routing_name} skipped: {e}")
else:
    warn("Routing DocType not found; routing.csv remains reference data.")

# Production Plans are best-effort because mandatory fields/child table names vary by ERPNext patch.
if CFG.get("create_production_plans"):
    for r in rows("production_plan.csv"):
        try:
            d = frappe.new_doc("Production Plan")
            if has_field("Production Plan", "company"): d.company = COMPANY
            if has_field("Production Plan", "posting_date"): d.posting_date = getdate(r["posting_date"])
            if has_field("Production Plan", "get_items_from"): d.get_items_from = "Sales Order"
            if has_field("Production Plan", "combine_items"): d.combine_items = 1
            table_field = "po_items" if has_field("Production Plan", "po_items") else ("items" if has_field("Production Plan", "items") else None)
            if table_field:
                child = {"item_code": r["item_code"], "planned_qty": float(r["planned_qty"])}
                if has_field("Production Plan", table_field):
                    d.append(table_field, child)
            if has_field("Production Plan", "notes"): d.notes = r["notes"]
            d.save(ignore_permissions=True)
            print("OK Production Plan:", d.name, "(source ref", r["plan_name"] + ")")
        except Exception as e:
            warn(f"Production Plan {r['plan_name']} skipped; create it in the UI if needed: {e}")

# Work Orders: create Draft records only, with BOM name resolved from item + BOM if possible.
if CFG.get("create_work_orders"):
    for r in rows("work_orders.csv"):
        try:
            bom_name = r["bom_no"]
            if not frappe.db.exists("BOM", bom_name):
                # Try matching by item if BOM was auto-named.
                matches = frappe.get_all("BOM", filters={"item": r["production_item"], "is_active": 1},
                                         fields=["name"], order_by="is_default desc, modified desc", limit=1)
                if matches: bom_name = matches[0]["name"]
                else:
                    warn(f"No BOM found for {r['work_order_name']} / {r['production_item']}; skipped")
                    continue
            d = frappe.new_doc("Work Order")
            for k, v in {
                "production_item": r["production_item"], "bom_no": bom_name,
                "qty": float(r["qty"]), "company": COMPANY,
                "planned_start_date": getdate(r["planned_start_date"]),
                "source_warehouse": WH["source"], "wip_warehouse": WH["wip"],
                "fg_warehouse": WH["finished_goods"]
            }.items():
                if has_field("Work Order", k): d.set(k, v)
            d.save(ignore_permissions=True)
            print("OK Work Order:", d.name, "(requested", r["work_order_name"] + ")")
        except Exception as e:
            warn(f"Work Order {r['work_order_name']} skipped: {e}")

# Stock Entries are reference examples. Do not manufacture empty entries: the UI should pull exact items from Work Order.
if CFG.get("create_stock_entries"):
    warn("stock_entries.csv is a workflow reference only. Create Stock Entries from each Work Order using ERPNext's Get Items from Work Order flow; this avoids incorrect or incomplete child rows.")
print("Import helper finished. Review warnings and validate every document in the UI before submitting.")
