# -*- coding: utf-8 -*-
from odoo.tests import tagged

from .common import StageAnalysisCommon


@tagged('post_install', '-at_install')
class TestAutoAssignment(StageAnalysisCommon):

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

    def test_auto_user_field_on_stage(self):
        """The auto_user_id field exists on the helpdesk.stage model."""
        field = self.env['helpdesk.stage']._fields.get('auto_user_id')
        self.assertIsNotNone(
            field,
            "Field 'auto_user_id' should exist on helpdesk.stage.",
        )
        self.assertEqual(field.comodel_name, 'res.users')

    def test_auto_assign_on_stage_change(self):
        """Moving to a stage with auto_user_id assigns the configured
        user to the ticket."""
        ticket = self._create_ticket()
        ticket.write({'stage_id': self.stage_quotation.id})

        self.assertEqual(
            ticket.user_id, self.helpdesk_manager,
            "Ticket user should be auto-assigned to the manager "
            "configured on stage_quotation.",
        )

    def test_no_auto_assign_without_config(self):
        """Moving to a stage without auto_user_id does not change the
        ticket assignee."""
        ticket = self._create_ticket({
            'user_id': self.helpdesk_user.id,
        })
        original_user = ticket.user_id

        ticket.write({'stage_id': self.stage_progress.id})

        self.assertEqual(
            ticket.user_id, original_user,
            "Ticket user should remain unchanged when the target stage "
            "has no auto_user_id.",
        )

    def test_auto_assign_overrides_current(self):
        """Auto-assignment overrides the currently assigned user."""
        ticket = self._create_ticket({
            'user_id': self.helpdesk_user.id,
        })
        self.assertEqual(ticket.user_id, self.helpdesk_user)

        ticket.write({'stage_id': self.stage_quotation.id})

        self.assertEqual(
            ticket.user_id, self.helpdesk_manager,
            "Ticket user should be overridden by stage_quotation's "
            "auto_user_id (helpdesk_manager).",
        )
