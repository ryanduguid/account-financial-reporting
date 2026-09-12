To use this module, you need to:

- go to the list view of the journal items
- select the lines you wish to export
- click on the button on top to export

The Excel export can be tailored to your exact needs via the following
methods of the 'account.move.line' object:

- **\_report_xlsx_fields**

  Add/drop columns or change order from the list of columns that are
  defined in the Excel template.

  The following fields are defined in the Excel template:

  > move, name, ref, date, partner, partner_ref, account, date_maturity,
  > debit, credit, balance, full_reconcile, reconcile_amount,
  > matched_debit_ids, matched_credit_ids, amount_currency, currency_name,
  > journal, company_currency, product, product_ref, product_uom, quantity,
  > statement, invoice, amount_residual, amount_residual_currency,
  > narration, blocked, id

- **\_report_xlsx_template**

  Change/extend the Excel template.
