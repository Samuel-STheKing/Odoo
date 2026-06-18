{
    'name': 'Gestión de Reportes',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Módulo para creación y gestión de reportes',
    'description': """
        Módulo para gestión de reportes con:
        - Vista Kanban para crear nuevos reportes
        - Formulario con código secuencial
        - Campos: fecha, usuario, título, área
        - Estados: borrador y guardado
    """,
    'author': 'Tu Nombre',
    'website': 'https://tuweb.com',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/secuencia_data.xml',
        'views/area_views.xml',
        'views/reporte_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}