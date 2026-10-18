# ERPNext / Frappe v16 Manufacturing Demo Dataset

This package contains a fictional, internally consistent manufacturing demo for **ERPNext v16 + Frappe v16**. It uses a small product family: a compact centrifugal pump assembly.

## Important setup assumptions

- Create/confirm a Company first, then set `company` in `config.json` to its exact ERPNext Company name.
- Create/confirm these Warehouses under that company (or edit `config.json` to match existing warehouses):
  - Stores - DEMO
  - WIP - DEMO
  - Finished Goods - DEMO
- Create/confirm the Item Groups `Raw Materials`, `Sub Assemblies`, `Finished Goods`, and `Consumables` (or map them to your existing groups).
- Create/confirm UOMs `Nos`, `Kg`, and `Litre`.
- This dataset is for a **demo/sandbox**, not for posting into a live company.
- CSVs use standard ERPNext DocType fieldnames where practical. Customizations, mandatory fields, and exact import-template columns can differ between sites and patches.

## Recommended import order

1. `config.json` — edit company and warehouse names.
2. `item_groups.csv` — create missing Item Groups manually or via Data Import.
3. `items.csv` — Items (make sure UOMs and Item Groups exist).
4. `workstations.csv` — Workstations.
5. `operations.csv` — Operations.
6. `bom_headers.csv`, `bom_items.csv`, `bom_operations.csv` — load BOMs using the included helper script. Child table rows are intentionally separate CSVs and are assembled into parent BOM documents by the script.
7. `routing.csv` — optional Routing records if your site uses Routing. Review the target site's field requirements first.
8. `production_plan.csv` — optional planning reference data; production plan child rows are assembled by the helper.
9. `work_orders.csv` — Work Orders. Import only after active BOMs exist and required warehouses are configured.
10. `stock_entries.csv` — draft Material Transfer / Manufacture entries for demo navigation. These are **not submitted** and do not affect stock until validated and submitted.

## Import helper

`import_dataset.py` is designed to run in a Frappe bench context, for example:

```bash
bench --site your-site.local console
```

Then, from the bench console, run:

```python
exec(open("/path/to/erpnext_v16_manufacturing_demo/import_dataset.py").read())
```

Copy the extracted folder somewhere readable by the bench user first. Edit `config.json` before running. The helper creates/updates master records and draft transaction records in dependency order. It skips unsupported optional doctypes/fields and prints warnings rather than pretending every site's schema is identical.

**Review the generated records before submitting anything.** The helper intentionally leaves Work Orders and Stock Entries in Draft. Depending on the exact ERPNext v16 patch and installed apps, Production Plan field requirements and transaction child-table schemas may differ; the helper treats Production Plan creation as best-effort and logs a warning if the site's schema does not accept the sample.

## Dataset contents

- 15 Items (raw materials, components, subassemblies, finished products)
- 4 Workstations
- 7 Operations
- 4 BOMs with component and operation rows
- 2 Routing reference records
- 2 Production Plan examples
- 3 Work Orders
- 3 Draft Stock Entry examples
- Item Groups, config, import helper, and validation checklist

## Demo flow

1. Review Item masters and Workstations.
2. Review operations and routing.
3. Open the BOM for `PUMP-1000` and inspect components, operation times, and costing fields.
4. Review the Production Plan examples and create a live Production Plan using your site's normal workflow.
5. Open Work Orders and demonstrate planned quantities and source/WIP/target warehouses.
6. Demonstrate Material Transfer for Manufacture, Job Cards (create from Work Order if enabled), and Manufacture Stock Entry.
7. Inspect finished-goods stock and valuation after you intentionally submit the required stock transactions in the sandbox.

## Validation checklist

- [ ] Company exists and `config.json` matches its exact name.
- [ ] Warehouses exist and belong to that company.
- [ ] Item Groups and UOMs exist.
- [ ] All Items save successfully.
- [ ] Workstations and Operations save successfully.
- [ ] BOMs are saved and **submitted/active** before Work Orders are created.
- [ ] BOM item quantities and operation times look correct.
- [ ] Work Orders are Draft until reviewed.
- [ ] Stock Entries are Draft; do not submit until stock, valuation, and accounting setup are verified.
