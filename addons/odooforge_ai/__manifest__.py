{
    "name": "OdooForge AI",
    "summary": "AI-powered customer support agent for Odoo Helpdesk",
    "version": "18.0.1.0.0",
    "license": "Other OSI approved licence",
    "author": "Atif Ali",
    "website": "https://github.com/atifali-pm/odooforge",
    "category": "Productivity",
    "depends": ["base", "mail", "helpdesk_mgmt"],
    "external_dependencies": {"python": ["requests"]},
    "data": [
        "views/res_config_settings_views.xml",
        "views/helpdesk_ticket_views.xml",
    ],
    "application": True,
    "installable": True,
}
