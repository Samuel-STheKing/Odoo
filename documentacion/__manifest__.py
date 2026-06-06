{
    'name': 'Documentación',
    'version': '16.0.1.0.0',
    'category': 'Documentation',
    'summary': 'Gestión de manuales, inducciones y configuración por módulos',
    'description': """
        Módulo para gestión documental:
        - Módulos/Categorías (Ventas, Compras, etc.)
        - Manuales (PDF/Videos)
        - Inducciones
        - Configuración por módulos y roles
    """,
    'author': 'Samuel',
    'depends': ['base', 'mail', 'web'],
    'data': [
        'security/documentacion_security.xml',
        'security/ir.model.access.csv',
        'views/documentacion_views.xml',
        'views/menu_views.xml',
        'data/data.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'icon': '/custom_wsl_u/static/description/icon.png',
}