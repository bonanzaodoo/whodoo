from odoo import api, fields, models


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    stage_tracking_ids = fields.One2many(
        'helpdesk.stage.tracking', 'ticket_id', string='Stage Tracking',
    )
    total_resolution_time = fields.Float(
        string='Total Resolution Time (Hours)', compute='_compute_total_resolution_time', store=True,
    )

    @api.depends('stage_tracking_ids', 'stage_tracking_ids.duration')
    def _compute_total_resolution_time(self):
        for record in self:
            record.total_resolution_time = sum(record.stage_tracking_ids.mapped('duration'))

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        tracking_vals = []
        now = fields.Datetime.now()

        for record in records:
            if record.stage_id:
                tracking_vals.append({'ticket_id': record.id, 'stage_id': record.stage_id.id, 'start_date': now})

        if tracking_vals:
            self.env['helpdesk.stage.tracking'].create(tracking_vals)

        return records

    def write(self, vals):
        if 'stage_id' in vals:
            now = fields.Datetime.now()
            # Close open tracking records for all records in self
            open_trackings = self.env['helpdesk.stage.tracking'].search([
                ('ticket_id', 'in', self.ids), ('end_date', '=', False),
            ])

            if open_trackings:
                open_trackings.write({'end_date': now})

            # Check if new stage has auto_user_id
            new_stage = self.env['helpdesk.stage'].browse(vals['stage_id'])

            if new_stage.auto_user_id:
                vals['user_id'] = new_stage.auto_user_id.id

            # Call super with potentially modified vals
            result = super().write(vals)
            # Create new tracking records after super
            tracking_vals = []

            for record in self:
                tracking_vals.append({'ticket_id': record.id, 'stage_id': vals['stage_id'], 'start_date': now})

            if tracking_vals:
                self.env['helpdesk.stage.tracking'].create(tracking_vals)

            return result

        return super().write(vals)
