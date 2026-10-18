# CSV import notes

For the cleanest result, use the included `import_dataset.py` from the bench console. It composes child rows into their parent BOM documents, which ordinary standalone CSV imports cannot reliably do for child-table DocTypes.

If using Data Import manually:
- Import Items, Workstations, and Operations first.
- For BOMs, download a fresh **Data Import template for BOM** from your own site, then map the columns from `bom_headers.csv`, `bom_items.csv`, and `bom_operations.csv` into the parent BOM's `items` and `operations` child tables. Child field naming and required columns must follow the site's template.
- `work_orders.csv`, `production_plan.csv`, and `stock_entries.csv` are source/reference CSVs. They intentionally do not pretend to be universal one-click transaction imports; transaction schemas and required fields can differ by patch and site configuration.
- The helper uses the site's actual DocType metadata to avoid setting fields that do not exist. It cannot guarantee a record will save if the site has additional mandatory custom fields or strict business validations.
