# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from odoo import fields
from odoo.tests import tagged

from .common import StageAnalysisCommon


@tagged('post_install', '-at_install')
class TestStageTracking(StageAnalysisCommon):

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

    def test_tracking_created_on_ticket_create(self):
        """A tracking record is created when a ticket is created."""
        ticket = self._create_ticket()
        trackings = ticket.stage_tracking_ids
        self.assertEqual(
            len(trackings), 1,
            "Exactly one tracking record should exist after creation.",
        )
        self.assertEqual(trackings.stage_id, self.stage_new)
        self.assertTrue(trackings.start_date)
        self.assertFalse(trackings.end_date)

    def test_tracking_closed_on_stage_change(self):
        """The current tracking is closed when the stage changes."""
        ticket = self._create_ticket()
        first_tracking = ticket.stage_tracking_ids

        ticket.write({'stage_id': self.stage_progress.id})

        self.assertTrue(
            first_tracking.end_date,
            "First tracking should have an end_date after stage change.",
        )
        # Duration may be 0 if operations are instant in tests
        self.assertGreaterEqual(
            first_tracking.duration, 0.0,
            "Duration should be >= 0 after closing the tracking.",
        )

    def test_tracking_new_on_stage_change(self):
        """A new tracking record is created for the new stage."""
        ticket = self._create_ticket()
        ticket.write({'stage_id': self.stage_progress.id})

        trackings = ticket.stage_tracking_ids.sorted('id')
        self.assertEqual(
            len(trackings), 2,
            "Two tracking records should exist after one stage change.",
        )
        self.assertEqual(trackings[0].stage_id, self.stage_new)
        self.assertEqual(trackings[1].stage_id, self.stage_progress)
        self.assertTrue(trackings[1].start_date)

    def test_tracking_duration_computed(self):
        """Duration is correctly computed from start_date and end_date."""
        ticket = self._create_ticket()
        tracking = self.env['helpdesk.stage.tracking'].create({
            'ticket_id': ticket.id,
            'stage_id': self.stage_new.id,
            'start_date': datetime(2026, 3, 20, 10, 0, 0),
            'end_date': datetime(2026, 3, 20, 12, 0, 0),
        })
        self.assertAlmostEqual(
            tracking.duration, 2.0, places=2,
            msg="Duration should be 2.0 hours for a 2-hour interval.",
        )

    def test_tracking_multiple_transitions(self):
        """Multiple stage transitions create the correct tracking chain."""
        ticket = self._create_ticket()
        ticket.write({'stage_id': self.stage_review.id})
        ticket.write({'stage_id': self.stage_progress.id})

        trackings = ticket.stage_tracking_ids.sorted('id')
        self.assertEqual(len(trackings), 3)
        self.assertEqual(trackings[0].stage_id, self.stage_new)
        self.assertEqual(trackings[1].stage_id, self.stage_review)
        self.assertEqual(trackings[2].stage_id, self.stage_progress)

    def test_tracking_back_and_forth(self):
        """Moving back to a previous stage creates a new tracking."""
        ticket = self._create_ticket()
        ticket.write({'stage_id': self.stage_review.id})
        ticket.write({'stage_id': self.stage_new.id})

        trackings = ticket.stage_tracking_ids.sorted('id')
        self.assertEqual(
            len(trackings), 3,
            "Three tracking records expected for new -> review -> new.",
        )
        self.assertEqual(trackings[0].stage_id, self.stage_new)
        self.assertEqual(trackings[1].stage_id, self.stage_review)
        self.assertEqual(trackings[2].stage_id, self.stage_new)

    def test_total_resolution_time(self):
        """total_resolution_time is the sum of tracking durations."""
        ticket = self._create_ticket()
        # Move through stages to generate trackings with duration
        ticket.write({'stage_id': self.stage_review.id})
        ticket.write({'stage_id': self.stage_done.id})
        ticket.invalidate_recordset()

        # Total should equal the sum of all tracking durations
        expected = sum(ticket.stage_tracking_ids.mapped('duration'))
        self.assertEqual(
            ticket.total_resolution_time, expected,
            "total_resolution_time should equal the sum of "
            "tracking durations.",
        )

    def test_total_resolution_time_with_manual_durations(self):
        """total_resolution_time sums tracking durations correctly."""
        ticket = self._create_ticket()
        # Create trackings with known durations
        self.env['helpdesk.stage.tracking'].create([
            {
                'ticket_id': ticket.id,
                'stage_id': self.stage_new.id,
                'start_date': datetime(2026, 3, 20, 10, 0, 0),
                'end_date': datetime(2026, 3, 20, 12, 0, 0),
            },
            {
                'ticket_id': ticket.id,
                'stage_id': self.stage_review.id,
                'start_date': datetime(2026, 3, 20, 12, 0, 0),
                'end_date': datetime(2026, 3, 20, 13, 30, 0),
            },
        ])
        ticket.invalidate_recordset()

        # 2h + 1.5h = 3.5h (plus the initial tracking from create)
        self.assertGreaterEqual(
            ticket.total_resolution_time, 3.5,
            "Resolution time should be at least 3.5 hours.",
        )

    def test_batch_write_tracking(self):
        """Batch writing stage_id creates tracking for all tickets."""
        ticket_1 = self._create_ticket({'name': 'Batch Ticket 1'})
        ticket_2 = self._create_ticket({'name': 'Batch Ticket 2'})

        (ticket_1 | ticket_2).write({'stage_id': self.stage_progress.id})

        for ticket in (ticket_1, ticket_2):
            trackings = ticket.stage_tracking_ids.sorted('id')
            self.assertEqual(
                len(trackings), 2,
                "Each ticket should have 2 tracking records.",
            )
            self.assertEqual(trackings[1].stage_id, self.stage_progress)
