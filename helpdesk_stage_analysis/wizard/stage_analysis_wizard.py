from datetime import timedelta

from odoo import _, fields, models
from odoo.exceptions import UserError


class StageAnalysisWizard(models.TransientModel):
    _name = 'helpdesk.stage.analysis.wizard'
    _description = 'Stage Analysis Report Wizard'

    date_from = fields.Datetime(
        string='Date From', required=True, default=lambda self: fields.Datetime.now() - timedelta(days=30),
    )
    date_to = fields.Datetime(string='Date To', required=True, default=fields.Datetime.now)
    team_ids = fields.Many2many(
        'helpdesk.team', string='Helpdesk Teams',
        help='Select helpdesk teams to include in the report. '
             'Leave empty to include all teams.',
    )
    stage_ids = fields.Many2many(
        'helpdesk.stage', string='Stages',
        help='Select stages to include in the report. '
             'Leave empty to include all stages.',
    )

    def action_generate_report(self):
        self.ensure_one()

        # Validate that tickets exist for the criteria
        domain = [('create_date', '>=', self.date_from), ('create_date', '<=', self.date_to)]

        if self.team_ids:
            domain.append(('team_id', 'in', self.team_ids.ids))

        if self.stage_ids:
            tracking_records = self.env['helpdesk.stage.tracking'].search([('stage_id', 'in', self.stage_ids.ids)])
            ticket_ids = tracking_records.mapped('ticket_id').ids
            domain.append(('id', 'in', ticket_ids))

        tickets = self.env['helpdesk.ticket'].search(domain, limit=1)
        if not tickets:
            raise UserError(_('No tickets found for the selected criteria.'))

        data = {'wizard_id': self.id}
        return self.env.ref('helpdesk_stage_analysis.action_report_stage_analysis_xlsx').report_action(self, data=data)
