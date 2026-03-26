# Helpdesk Stage Analysis

Track, analyze and report time spent in each helpdesk ticket stage with automated user assignment and Excel export capabilities.

## Requirements

- Odoo 17.0 Enterprise
- `helpdesk` module installed and configured

## Installation

1. Place the `helpdesk_stage_analysis` folder in your Odoo addons path.
2. Update the apps list: **Settings > Apps > Update Apps List**.
3. Search for "Helpdesk Stage Analysis" and click **Install**.

## Configuration

### Auto User Assignment on Stages

1. Navigate to **Helpdesk > Configuration > Stages**.
2. Open each stage and set the **Auto Assign User** field.
3. When a ticket moves to a configured stage, the assigned user is automatically updated.
4. Leave the field empty to keep manual assignment behavior.

## Usage

### Viewing Stage Tracking

1. Open any helpdesk ticket.
2. Navigate to the **Stage Tracking** tab.
3. View the complete history of stage transitions including start date, end date, and duration.

### Generating the Analysis Report

1. Go to **Helpdesk > Reporting > Stage Analysis**.
2. Select the desired date range (From / To).
3. Optionally filter by specific stages.
4. Click **Generate Report** to download an XLSX file.

### Report Contents

The Excel report includes the following columns:

- **Ticket ID**: Internal reference number
- **Subject**: Ticket name/description
- **Creation Date**: When the ticket was created
- **Stage columns**: Time spent in each stage (dynamically generated)
- **Close Date**: When the ticket was resolved
- **Total Resolution Time**: Overall time from creation to close
- **Current Stage**: The stage where the ticket currently resides

## Technical Notes

- **Timezone handling**: All dates in the report are converted to the user's timezone. If the user has no timezone configured, it defaults to `America/Costa_Rica`.
- **Stage transitions**: The module tracks every stage change, including back-and-forth movements. Each transition is recorded as a separate tracking entry.
- **Duration calculation**: Duration is computed as the difference between the start and end datetime of each tracking record.

## Models

| Model | Description |
|-------|-------------|
| `helpdesk.stage.tracking` | New model - Records individual stage transitions per ticket |
| `helpdesk.ticket` | Extended - Added stage tracking relation and write override |
| `helpdesk.stage` | Extended - Added auto assign user field |

## Author

- **Talentixs**
- Lead Developer: Marco Mandujano

## License

LGPL-3
