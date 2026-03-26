{
    'name': 'Análisis de Etapas de Mesa de Ayuda',
    'version': '17.0.2.0.0',
    'category': 'Services/Helpdesk',
    'summary': 'Rastree y analice el tiempo invertido en cada etapa de tickets de mesa de ayuda',
    'description': """
Análisis de Etapas de Mesa de Ayuda
====================================
Registra automáticamente cada transición de etapa en los tickets de
mesa de ayuda con fechas y duraciones. Permite asignar usuarios
automáticamente según la etapa, configurar cuáles etapas incluir en
el reporte, y generar reportes Excel (XLSX) detallados con filtros
por equipo, fechas y etapas específicas.
    """,
    'author': 'Talentixs, Marco Mandujano',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'helpdesk',
        'report_xlsx',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/helpdesk_stage_views.xml',
        'views/helpdesk_ticket_views.xml',
        'wizard/stage_analysis_wizard_views.xml',
        'report/report_stage_analysis_xlsx.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
