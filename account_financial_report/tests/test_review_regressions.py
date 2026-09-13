# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import io
from unittest.mock import patch

import xlsxwriter

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestReportRegressions(TransactionCase):
    def test_currency_format_cache(self):
        report = self.env["report.a_f_r.report_open_items_xlsx"]
        currency = self.env.company.currency_id
        with xlsxwriter.Workbook(io.BytesIO(), {"in_memory": True}) as workbook:
            data = {
                "workbook": workbook,
                "formats": {
                    "format_amount": workbook.add_format(),
                    "format_header_amount": workbook.add_format(),
                },
            }
            row = {"currency_id": currency, "currency_name": currency.name}
            first = report._get_currency_amt_format_dict(row, data)
            self.assertIs(first, report._get_currency_amt_format_dict(row, data))
            row["currency_id"] = currency.id
            first = report._get_currency_amt_header_format_dict(row, data)
            self.assertIs(first, report._get_currency_amt_header_format_dict(row, data))

    def test_partner_sheet_names(self):
        report = self.env["report.a_f_r.report_open_items_xlsx"]
        names = ["History", "history", "A/B", "A:B", "'", "'Edge'", "a" * 40, "A" * 40]
        res_data = {
            "Open_Items": {},
            "accounts_data": {},
            "journals_data": {},
            "total_amount": {},
            "partners_data": {i: {"name": name} for i, name in enumerate(names)},
        }
        with xlsxwriter.Workbook(io.BytesIO(), {"in_memory": True}) as workbook:
            report._generate_report_content_by_salesperson(
                workbook, None, {}, {}, res_data
            )
            actual = [sheet.get_name() for sheet in workbook.worksheets()]
            self.assertEqual(len(actual), len(names))
            self.assertEqual(len({name.casefold() for name in actual}), len(names))
            self.assertNotIn("history", [name.casefold() for name in actual])

    def test_initial_balances_group_tax_and_base_lines(self):
        report = self.env["report.account_financial_report.general_ledger"]
        tax_line = {
            "account_id": (1, "100"),
            "tax_line_id": (3, "GST"),
            "credit": 10,
            "balance": -10,
        }
        base_line = {
            "account_id": (1, "100"),
            "tax_ids": (3, "GST"),
            "credit": 100,
            "balance": -100,
        }
        no_tax = {
            "account_id": (1, "100"),
            "tax_ids": False,
            "credit": 5,
            "balance": -5,
        }
        with patch.object(
            type(self.env["account.move.line"]),
            "read_group",
            side_effect=[[tax_line], [base_line, no_tax]],
        ) as grouped:
            result = report._prepare_gen_ld_data_group_taxes({1: {}}, [], "taxes")
        self.assertEqual(result[1][3]["init_bal"]["balance"], -110)
        self.assertEqual(result[1][3]["fin_bal"]["balance"], -110)
        self.assertEqual(result[1][0]["init_bal"]["balance"], -5)
        self.assertEqual(
            grouped.call_args_list[0].kwargs["groupby"], ["account_id", "tax_line_id"]
        )
        self.assertEqual(
            grouped.call_args_list[1].kwargs["groupby"], ["account_id", "tax_ids"]
        )

    def test_refund_uses_refund_tags(self):
        report = self.env["report.account_financial_report.vat_report"]
        tax_data = {
            3: {"amount_type": "percent", "tags_ids": [1], "refund_tags_ids": [2]}
        }
        lines = [
            {"tax_line_id": 3, "is_refund": False, "net": 100, "tax": 10},
            {"tax_line_id": 3, "is_refund": True, "net": -40, "tax": -4},
        ]
        with patch.object(
            type(report),
            "_get_tags_data",
            return_value={
                1: {"name": "Invoice", "code": ""},
                2: {"name": "Refund", "code": ""},
            },
        ):
            result = report._get_vat_report_tag_data(lines, tax_data, False)
        self.assertEqual(
            {row["name"]: row["tax"] for row in result}, {"Invoice": 10, "Refund": -4}
        )
