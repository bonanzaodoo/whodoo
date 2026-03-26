# -*- coding: utf-8 -*-
from odoo.addons.helpdesk.tests.common import HelpdeskCommon


class StageAnalysisCommon(HelpdeskCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        stage_as_manager = cls.env['helpdesk.stage'].with_user(
            cls.helpdesk_manager,
        )

        cls.stage_review = stage_as_manager.create({
            'name': 'Review',
            'sequence': 15,
            'team_ids': [(4, cls.test_team.id, 0)],
        })

        cls.stage_quotation = stage_as_manager.create({
            'name': 'Quotation',
            'sequence': 25,
            'team_ids': [(4, cls.test_team.id, 0)],
            'auto_user_id': cls.helpdesk_manager.id,
        })

        # Set auto_user_id on existing stage_new
        cls.stage_new.write({
            'auto_user_id': cls.helpdesk_user.id,
        })

        # Set timezone for test users
        cls.helpdesk_user.write({'tz': 'America/Costa_Rica'})
        cls.helpdesk_manager.write({'tz': 'America/Costa_Rica'})

        # Create a second helpdesk team for team filter tests
        cls.test_team_2 = cls.env['helpdesk.team'].create({
            'name': 'Team Beta',
            'stage_ids': [
                (4, cls.stage_new.id, 0),
                (4, cls.stage_progress.id, 0),
                (4, cls.stage_done.id, 0),
            ],
        })
