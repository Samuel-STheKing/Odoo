{
    "name": "Helpdesk Project",
    "summary": "Add the option to select project in the tickets.",
    "version": "16.0.1.0.3",
    "license": "AGPL-3",
    "category": "After-Sales",
    "author": "PuntSistemes S.L.U., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/helpdesk",
    "depends": ["helpdesk_mgmt", "project"],
    "data": [
        "views/helpdesk_ticket_view.xml",
        "views/helpdesk_ticket_team_view.xml",
        "views/project_view.xml",
        "views/project_task_view.xml",
        "views/project_milestone.xml",
        "views/menus.xml",
    ],
    "development_status": "Production/Stable",
}