# Validation / demo checklist

## Masters
- Confirm the Company and three warehouses in `config.json`.
- Ensure `Nos`, `Kg`, and `Litre` UOMs exist.
- Ensure the four Item Groups exist.
- Confirm all Items have `Maintain Stock` enabled where required and valid default UOMs.
- Check whether your site requires additional fields (e.g. valuation method, item defaults, account mappings).

## BOMs
- BOM components refer to existing Items.
- Subassembly BOMs (`PUMP-ROTOR`, `PUMP-END-COVER`) should be created before the finished pump BOM.
- In ERPNext, save BOMs, then submit/activate them according to the site's normal process. The helper defaults to not submitting BOMs.
- The alternative BOM is intentionally a second recipe for comparison; do not mark both as default.

## Transactions
- Work Orders and Stock Entries are created in Draft.
- Use **Get Items from BOM / Work Order** in the ERPNext UI to verify exploded quantities.
- Stock Entry rows are intentionally assembled by ERPNext where possible. The sample transaction CSV is a workflow reference; it is not a substitute for checking the actual child rows.
- Do not submit transactions unless stock availability, valuation, and accounting configuration are correct.
