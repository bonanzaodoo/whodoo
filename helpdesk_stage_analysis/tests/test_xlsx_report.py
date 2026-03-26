# -*- coding: utf-8 -*-
import io
from datetime import datetime, timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import StageAnalysisCommon

try:
    import xlrd
except ImportError:
    xlrd = None


@tagged('post_install', '-at_install')
class TestXlsxReport(StageAnalysisCommon):

    def _create_ticket(self, vals=None):
        """Helper to create a ticket with sensible defaults."""
        default_vals = {
            'name': 'Test Ticket',
            'team_id': self.test_team.id,
            'stage_id': self.stage_new.id,
        }
        if vals:
            default_vals.update(vals)
        return self.env['helpdesk.ticket'].with_user(
            self.helpdesk_manager,
        ).create(default_vals)

    def _create_wizard(self, vals=None):
        """Helper to create a wizard with sensible defaults."""
        now = fields.Datetime.now()
        default_vals = {
            'date_from': now - timedelta(days=1),
            'date_to': now + timedelta(days=1),
        }
        if vals:
            default_vals.update(vals)
        return self.env['helpdesk.stage.analysis.wizard'].with_user(
            self.helpdesk_manager,
        ).create(default_vals)

    def _generate_report_data(self, wizard):
        """Call action_generate_report and return the report action."""
        return wizard.action_generate_report()

    def test_wizard_generates_report_action(self):
        """The wizard returns an ir.actions.report action for XLSX."""
        self._create_ticket()
        wizard = self._create_wizard()
        result = self._generate_report_data(wizard)

        self.assertIsInstance(result, dict)
        self.assertEqual(
            result.get('type'), 'ir.actions.report',
            "Action type should be ir.actions.report.",
        )

    def test_wizard_no_tickets_raises(self):
        """A UserError is raised when no tickets match the criteria."""
        wizard = self._create_wizard({
            'date_from': datetime(2010, 1, 1),
            'date_to': datetime(2010, 1, 2),
        })
        with self.assertRaises(UserError):
            wizard.action_generate_report()

    def test_wizard_date_filter(self):
        """Only tickets within the wizard date range are included."""
        self._create_ticket({'name': 'In Range Ticket'})
        now = fields.Datetime.now()

        wizard = self._create_wizard({
            'date_from': now - timedelta(hours=1),
            'date_to': now + timedelta(hours=1),
        })
        result = self._generate_report_data(wizard)
        self.assertEqual(result.get('type'), 'ir.actions.report')

        wizard_miss = self._create_wizard({
            'date_from': datetime(2020, 1, 1),
            'date_to': datetime(2020, 1, 2),
        })
        with self.assertRaises(UserError):
            wizard_miss.action_generate_report()

    def test_wizard_stage_filter(self):
        """When stage_ids are set, only tickets with tracking in those
        stages are included."""
        ticket = self._create_ticket()
        ticket.write({'stage_id': self.stage_review.id})

        wizard = self._create_wizard({
            'stage_ids': [(6, 0, [self.stage_review.id])],
        })
        result = self._generate_report_data(wizard)
        self.assertEqual(result.get('type'), 'ir.actions.report')

        wizard_miss = self._create_wizard({
            'stage_ids': [(6, 0, [self.stage_quotation.id])],
        })
        with self.assertRaises(UserError):
            wizard_miss.action_generate_report()

    def test_wizard_team_filter(self):
        """When team_ids are set, only tickets from those teams are
        included."""
        self._create_ticket({'name': 'Team Alpha Ticket'})

        # Filter by test_team (Team Alpha) -> should find ticket
        wizard = self._create_wizard({
            'team_ids': [(6, 0, [self.test_team.id])],
        })
        result = self._generate_report_data(wizard)
        self.assertEqual(result.get('type'), 'ir.actions.report')

        # Filter by test_team_2 (Team Beta) -> no tickets
        wizard_miss = self._create_wizard({
            'team_ids': [(6, 0, [self.test_team_2.id])],
        })
        with self.assertRaises(UserError):
            wizard_miss.action_generate_report()

    def test_wizard_team_filter_multiple_teams(self):
        """Filtering by multiple teams includes tickets from all."""
        self._create_ticket({'name': 'Alpha Ticket'})
        self._create_ticket({
            'name': 'Beta Ticket',
            'team_id': self.test_team_2.id,
        })

        wizard = self._create_wizard({
            'team_ids': [(6, 0, [
                self.test_team.id, self.test_team_2.id,
            ])],
        })
        result = self._generate_report_data(wizard)
        self.assertEqual(result.get('type'), 'ir.actions.report')

    def test_show_in_report_default_true(self):
        """New stages have show_in_report=True by default."""
        new_stage = self.env['helpdesk.stage'].create({
            'name': 'Test Default Stage',
            'team_ids': [(4, self.test_team.id)],
        })
        self.assertTrue(
            new_stage.show_in_report,
            "show_in_report should default to True.",
        )

    def test_show_in_report_excludes_stage(self):
        """Stages with show_in_report=False are excluded from report
        columns."""
        ticket = self._create_ticket()
        ticket.write({'stage_id': self.stage_review.id})
        ticket.write({'stage_id': self.stage_quotation.id})

        # Mark stage_review as excluded from report
        self.stage_review.write({'show_in_report': False})

        wizard = self._create_wizard()
        report_model = self.env[
            'report.helpdesk_stage_analysis.report_stage_analysis'
        ]
        data = {'wizard_id': wizard.id}
        tickets = report_model._get_tickets(data)
        stages = report_model._get_report_stages(tickets, data)

        self.assertNotIn(
            self.stage_review, stages,
            "stage_review with show_in_report=False should not appear.",
        )
        self.assertIn(
            self.stage_quotation, stages,
            "stage_quotation with show_in_report=True should appear.",
        )

    def test_wizard_timezone_handling(self):
        """Tickets created at late hours are correctly handled with
        UTC boundaries."""
        ticket = self._create_ticket({'name': 'Timezone Ticket'})
        create_date = ticket.create_date
        wizard_hit = self._create_wizard({
            'date_from': create_date - timedelta(hours=1),
            'date_to': create_date + timedelta(hours=1),
        })
        result = self._generate_report_data(wizard_hit)
        self.assertEqual(result.get('type'), 'ir.actions.report')

        wizard_miss = self._create_wizard({
            'date_from': create_date - timedelta(days=10),
            'date_to': create_date - timedelta(days=9),
        })
        with self.assertRaises(UserError):
            wizard_miss.action_generate_report()

    def test_report_uses_company_color(self):
        """The report uses company.primary_color for header background."""
        report_model = self.env[
            'report.helpdesk_stage_analysis.report_stage_analysis'
        ]
        # If company has no primary_color, fallback is used
        self.env.company.write({'primary_color': '#FF5733'})
        workbook_mock = type('MockWorkbook', (), {
            'add_format': lambda self, fmt: fmt,
        })()
        header_fmt = report_model._get_header_format(workbook_mock)
        self.assertEqual(
            header_fmt['bg_color'], '#FF5733',
            "Header should use company primary_color.",
        )

    def test_report_fallback_color(self):
        """When company has no primary_color, Talentix default is used."""
        report_model = self.env[
            'report.helpdesk_stage_analysis.report_stage_analysis'
        ]
        self.env.company.write({'primary_color': False})
        workbook_mock = type('MockWorkbook', (), {
            'add_format': lambda self, fmt: fmt,
        })()
        header_fmt = report_model._get_header_format(workbook_mock)
        self.assertEqual(
            header_fmt['bg_color'], '#373b59',
            "Header should fallback to Talentix default color.",
        )
