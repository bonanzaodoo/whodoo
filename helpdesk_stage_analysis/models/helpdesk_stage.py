from odoo import fields, models


class HelpdeskStage(models.Model):
    _inherit = 'helpdesk.stage'

    auto_user_id = fields.Many2one(
        'res.users', string='Auto Assign User',
        help=(
            'User automatically assigned to tickets when they '
            'reach this stage. Leave empty to keep the current '
            'assignee.'
        ),
    )
    show_in_report = fields.Boolean(
        string='Show in Report', default=True,
        help=(
            'If checked, this stage will appear as a column in '
            'the Stage Analysis XLSX report. Uncheck to exclude '
            'it from the report.'
        ),
    )
