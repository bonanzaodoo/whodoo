import pytz

from odoo import _, fields, models


class ReportStageAnalysisXlsx(models.AbstractModel):
    _name = 'report.helpdesk_stage_analysis.report_stage_analysis'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Stage Analysis XLSX Report'

    def _format_float_time(self, hours):
        """Format a float hours value as HH:MM string."""
        total_minutes = int(round(hours * 60))
        h = total_minutes // 60
        m = total_minutes % 60
        return '{:02d}:{:02d}'.format(h, m)

    def _get_user_tz(self):
        """Return the timezone string for the current user."""
        return self.env.user.tz or 'America/Costa_Rica'

    def _convert_to_user_tz(self, dt):
        """Convert a UTC datetime to the current user's timezone."""
        if not dt:
            return False
        user_tz = self._get_user_tz()
        return fields.Datetime.context_timestamp(
            self.with_context(tz=user_tz), dt,
        )

    def _get_header_format(self, workbook):
        """Return the header format using company primary color."""
        primary_color = self.env.company.primary_color or '#373b59'
        return workbook.add_format({
            'bold': True,
            'bg_color': primary_color,
            'font_color': '#FFFFFF',
            'border': 1,
            'text_wrap': True,
            'valign': 'vcenter',
            'align': 'center',
        })

    def _get_data_format(self, workbook):
        """Return the standard data cell format."""
        return workbook.add_format({
            'border': 1,
            'valign': 'vcenter',
        })

    def _get_data_center_format(self, workbook):
        """Return the centered data cell format."""
        return workbook.add_format({
            'border': 1,
            'valign': 'vcenter',
            'align': 'center',
        })

    def _get_tickets(self, data):
        """Search tickets based on wizard filters."""
        wizard = self.env['helpdesk.stage.analysis.wizard'].browse(data.get('wizard_id'))
        domain = [('create_date', '>=', wizard.date_from), ('create_date', '<=', wizard.date_to)]

        if wizard.team_ids:
            domain.append(('team_id', 'in', wizard.team_ids.ids))

        if wizard.stage_ids:
            tracking_records = self.env['helpdesk.stage.tracking'].search([('stage_id', 'in', wizard.stage_ids.ids)])
            ticket_ids = tracking_records.mapped('ticket_id').ids
            domain.append(('id', 'in', ticket_ids))

        return self.env['helpdesk.ticket'].search(domain, order='create_date asc')

    def _get_report_stages(self, tickets, data):
        """Determine which stages to include as columns."""
        wizard = self.env['helpdesk.stage.analysis.wizard'].browse(data.get('wizard_id'))

        if wizard.stage_ids:
            stages = wizard.stage_ids.filtered('show_in_report').sorted('sequence')
        else:
            all_trackings = self.env['helpdesk.stage.tracking'].search([('ticket_id', 'in', tickets.ids)])
            stages = all_trackings.mapped('stage_id').filtered('show_in_report').sorted('sequence')

        return stages

    def _build_tracking_map(self, tickets):
        """Build {ticket_id: {stage_id: total_duration}} dict."""
        all_trackings = self.env['helpdesk.stage.tracking'].search([('ticket_id', 'in', tickets.ids)])
        tracking_map = {}

        for tracking in all_trackings:
            tid = tracking.ticket_id.id
            sid = tracking.stage_id.id

            if tid not in tracking_map:
                tracking_map[tid] = {}
            tracking_map[tid][sid] = (tracking_map[tid].get(sid, 0.0) + tracking.duration)

        return tracking_map

    def generate_xlsx_report(self, workbook, data, objs):
        """Generate the Stage Analysis XLSX report."""
        # Ensure user language is in context for translations
        user_lang = self.env.user.lang or self.env.context.get('lang', 'en_US')
        self = self.with_context(lang=user_lang)

        tickets = self._get_tickets(data)
        stages = self._get_report_stages(tickets, data)
        tracking_map = self._build_tracking_map(tickets)

        # Formats
        header_fmt = self._get_header_format(workbook)
        data_fmt = self._get_data_format(workbook)
        data_center_fmt = self._get_data_center_format(workbook)

        sheet = workbook.add_worksheet(_('Stage Analysis'))

        # Build headers
        headers = [_('Ticket ID'), _('Subject'), _('Creation Date/Time')]

        for stage in stages:
            stage_name = stage.with_context(lang=user_lang).name
            headers.append(_('Time "%s"') % stage_name)

        headers.extend([_('Close Date/Time'), _('Total Resolution Time'), _('Current Stage')])

        # Write headers
        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_fmt)

        # Set column widths
        sheet.set_column(0, 0, 20)   # Ticket ID
        sheet.set_column(1, 1, 40)   # Subject
        sheet.set_column(2, 2, 22)   # Creation Date/Time
        stage_start_col = 3
        stage_end_col = stage_start_col + len(stages) - 1

        if stages:
            sheet.set_column(stage_start_col, stage_end_col, 18)

        close_col = stage_start_col + len(stages)
        sheet.set_column(close_col, close_col, 22)
        sheet.set_column(close_col + 1, close_col + 1, 18)
        sheet.set_column(close_col + 2, close_col + 2, 25)

        # Write data rows
        row = 1
        for ticket in tickets:
            col = 0

            # Ticket ID
            sheet.write(row, col, ticket.ticket_ref or '', data_fmt)
            col += 1

            # Subject
            sheet.write(row, col, ticket.name or '', data_fmt)
            col += 1

            # Creation Date/Time (user TZ)
            create_dt = self._convert_to_user_tz(ticket.create_date)

            if create_dt:
                sheet.write(
                    row, col,
                    create_dt.strftime('%Y-%m-%d %H:%M:%S'),
                    data_center_fmt,
                )
            else:
                sheet.write(row, col, '', data_center_fmt)
            col += 1

            # Stage duration columns
            ticket_trackings = tracking_map.get(ticket.id, {})
            for stage in stages:
                duration = ticket_trackings.get(stage.id, 0.0)
                if duration > 0:
                    sheet.write(
                        row, col,
                        self._format_float_time(duration),
                        data_center_fmt,
                    )
                else:
                    sheet.write(row, col, '', data_center_fmt)
                col += 1

            # Close Date/Time (user TZ)
            close_dt = self._convert_to_user_tz(ticket.close_date)
            if close_dt:
                sheet.write(
                    row, col,
                    close_dt.strftime('%Y-%m-%d %H:%M:%S'),
                    data_center_fmt,
                )
            else:
                sheet.write(row, col, '', data_center_fmt)
            col += 1

            # Total Resolution Time
            if ticket.total_resolution_time:
                sheet.write(
                    row, col,
                    self._format_float_time(
                        ticket.total_resolution_time,
                    ),
                    data_center_fmt,
                )
            else:
                sheet.write(row, col, '', data_center_fmt)
            col += 1

            # Current Stage (translated)
            stage_name = ''
            if ticket.stage_id:
                stage_name = ticket.stage_id.with_context(lang=user_lang).name

            sheet.write(row, col, stage_name, data_fmt)

            row += 1

        # Autofilter
        if row > 1:
            sheet.autofilter(0, 0, row - 1, len(headers) - 1)
