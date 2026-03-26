from odoo import api, fields, models


class HelpdeskStageTracking(models.Model):
    _name = 'helpdesk.stage.tracking'
    _description = 'Helpdesk Stage Tracking'
    _order = 'start_date desc'

    ticket_id = fields.Many2one(
        'helpdesk.ticket', string='Ticket', required=True, ondelete='cascade', index=True,
    )
    stage_id = fields.Many2one('helpdesk.stage', string='Stage', required=True, ondelete='restrict')
    start_date = fields.Datetime(string='Start Date', required=True, default=fields.Datetime.now)
    end_date = fields.Datetime(string='End Date')
    duration = fields.Float(string='Duration (Hours)', compute='_compute_duration', store=True)

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        for record in self:
            if record.start_date and record.end_date:
                delta = record.end_date - record.start_date
                record.duration = delta.total_seconds() / 3600.0
            else:
                record.duration = 0.0
