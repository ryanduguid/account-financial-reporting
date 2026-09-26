#  Copyright 2021 Simone Rubino - Agile Business Group
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import date, timedelta

from odoo.tests import TransactionCase, tagged
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, test_reports


@tagged("post_install", "-at_install")
class TestAgedPartnerBalance(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                mail_create_nolog=True,
                mail_create_nosubscribe=True,
                mail_notrack=True,
                no_reset_password=True,
                tracking_disable=True,
            )
        )
        cls.wizard_model = cls.env["aged.partner.balance.report.wizard"]
        # Check that report is produced correctly
        cls.wizard_with_line_details = cls.wizard_model.create(
            {
                "show_move_line_details": True,
                "receivable_accounts_only": True,
            }
        )
        cls.wizard_without_line_details = cls.wizard_model.create(
            {
                "show_move_line_details": False,
                "receivable_accounts_only": True,
            }
        )
        cls.account_age_report_config = cls.env[
            "account.age.report.configuration"
        ].create(
            {
                "name": "Intervals configuration",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "1-30",
                            "inferior_limit": 30,
                        },
                    ),
                ],
            }
        )

    def test_custom_interval_boundaries(self):
        self.account_age_report_config.write(
            {
                "line_ids": [
                    (0, 0, {"name": "31-60", "inferior_limit": 60}),
                    (0, 0, {"name": "61-120", "inferior_limit": 120}),
                ]
            }
        )
        intervals = self.account_age_report_config.line_ids
        report = self.env[
            "report.account_financial_report.aged_partner_balance"
        ].with_context(age_partner_config=self.account_age_report_config)
        date_at = date(2026, 6, 30)
        cases = [
            (None, "current"),
            (-1, "current"),
            (0, "current"),
            (1, intervals[0]),
            (30, intervals[0]),
            (31, intervals[1]),
            (60, intervals[1]),
            (61, intervals[2]),
            (120, intervals[2]),
            (121, "older"),
        ]
        for days, bucket in cases:
            for residual in (125.0, -25.0):
                with self.subTest(days=days, residual=residual):
                    due_date = (
                        date_at - timedelta(days=days) if days is not None else None
                    )
                    data = report._initialize_account({}, 1)
                    report._initialize_partner(data, 1, 2)
                    report._calculate_amounts(data, 1, 2, residual, due_date, date_at)
                    move_line = {"due_date": due_date, "residual": residual}
                    report._compute_maturity_date(move_line, date_at)
                    expected_values = dict.fromkeys(
                        ["current", "older", *intervals], 0.0
                    )
                    expected_values[bucket] = residual
                    for values in (data[1], data[1][2], move_line):
                        self.assertEqual(values["residual"], residual)
                        for key, expected in expected_values.items():
                            self.assertEqual(values[key], expected)

    def test_report_without_aged_report_configuration(self):
        """Check that report is produced correctly."""
        wizard = self.wizard_with_line_details
        wizard.onchange_type_accounts_only()
        data = wizard._prepare_report_data()

        # Simulate web client behavior:
        # default value is a datetime.date but web client sends back strings
        data.update({"date_at": data["date_at"].strftime(DEFAULT_SERVER_DATE_FORMAT)})
        result = test_reports.try_report(
            self.env.cr,
            self.env.uid,
            "account_financial_report.aged_partner_balance",
            wizard.ids,
            data=data,
        )
        self.assertTrue(result)
        second_wizard = self.wizard_without_line_details
        second_wizard.onchange_type_accounts_only()
        data = second_wizard._prepare_report_data()

        # Simulate web client behavior:
        # default value is a datetime.date but web client sends back strings
        data.update({"date_at": data["date_at"].strftime(DEFAULT_SERVER_DATE_FORMAT)})
        result = test_reports.try_report(
            self.env.cr,
            self.env.uid,
            "account_financial_report.aged_partner_balance",
            second_wizard.ids,
            data=data,
        )
        self.assertTrue(result)

    def test_report_with_aged_report_configuration(self):
        """Check that report is produced correctly."""
        wizard = self.wizard_with_line_details
        wizard.age_partner_config_id = self.account_age_report_config.id

        wizard.onchange_type_accounts_only()
        data = wizard._prepare_report_data()

        # Simulate web client behavior:
        # default value is a datetime.date but web client sends back strings
        data.update({"date_at": data["date_at"].strftime(DEFAULT_SERVER_DATE_FORMAT)})
        result = test_reports.try_report(
            self.env.cr,
            self.env.uid,
            "account_financial_report.aged_partner_balance",
            wizard.ids,
            data=data,
        )
        self.assertTrue(result)

        second_wizard = self.wizard_without_line_details
        second_wizard.age_partner_config_id = self.account_age_report_config.id

        second_wizard.onchange_type_accounts_only()
        data = second_wizard._prepare_report_data()

        # Simulate web client behavior:
        # default value is a datetime.date but web client sends back strings
        data.update({"date_at": data["date_at"].strftime(DEFAULT_SERVER_DATE_FORMAT)})
        result = test_reports.try_report(
            self.env.cr,
            self.env.uid,
            "account_financial_report.aged_partner_balance",
            second_wizard.ids,
            data=data,
        )
        self.assertTrue(result)
