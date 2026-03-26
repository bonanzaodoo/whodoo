# Changelog

## [17.0.2.0.0] - 2026-03-25

### Added
- `show_in_report` boolean field on helpdesk stages to control which stages
  appear as columns in the XLSX report
- `total_resolution_time` stored computed field on helpdesk tickets (sum of
  all tracking durations)
- Team filter (`team_ids` Many2many) in the Stage Analysis wizard
- Company color theming for XLSX report headers using `company.primary_color`
  with fallback to `#373b59`
- Stage search view with filters (Show in Report, Auto Assignment Configured)
  and Group By options
- Batch ticket creation support via `@api.model_create_multi`
- New unit tests: team filters, multiple teams, `show_in_report` exclusion,
  timezone handling, company color, fallback color, batch write (24 total,
  up from 19)

- Spanish (Latin America) translations (`es_419.po`)
- Spanish (Spain) translations (`es_ES.po`)

### Changed
- Dynamic stage columns in XLSX report now respect `show_in_report` flag
- Switched to OCA `report_xlsx` base module as dependency for XLSX generation
- Updated and completed Spanish (Costa Rica) translations (`es_CR.po`)
- Redesigned `static/description/index.html` module description page

## [17.0.1.0.0] - 2026-03-24

### Added
- Stage tracking model (helpdesk.stage.tracking) with start/end dates and duration
- Automatic tracking creation on ticket stage changes
- Auto user assignment field on helpdesk stages
- Stage Analysis wizard with date range and stage filters
- XLSX report generation with dynamic stage columns
- Timezone-aware date handling for reports
- Spanish (Costa Rica) translations (es_CR.po)
- Module description page (index.html)
