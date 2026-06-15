def post_init_hook(cr, registry):
    from odoo import api, SUPERUSER_ID
    env = api.Environment(cr, SUPERUSER_ID, {})

    # No forzar etapas predefinidas - el usuario creará sus propias etapas
    pass