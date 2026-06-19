from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ReporteConfig(models.Model):
    _name = 'reporte.config'
    _description = 'Configuración de Reportes'
    _rec_name = 'usuario_id'

    usuario_id = fields.Many2one(
        'res.users',
        string='Usuario',
        required=True,
    )

    rol = fields.Selection([
        ('administrador', 'Administrador'),
        ('editor', 'Editor'),
        ('lector', 'Lector'),
        ('supervisor', 'Supervisor'),
    ], string='Rol Asignado', required=True, default='lector')

    area_ids = fields.Many2many(
        'reporte.area',
        string='Áreas Asignadas',
        help='Áreas a las que tiene acceso este usuario'
    )

    activo = fields.Boolean(string='Activo', default=True)

    @api.constrains('usuario_id')
    def _check_usuario_unico(self):
        for record in self:
            existing = self.search([
                ('usuario_id', '=', record.usuario_id.id),
                ('id', '!=', record.id)
            ])
            if existing:
                raise ValidationError(_('Este usuario ya tiene una configuración asignada.'))

    @api.model
    def create(self, vals):
        if vals.get('usuario_id'):
            existing = self.search([('usuario_id', '=', vals['usuario_id'])])
            if existing:
                raise ValidationError(_('Este usuario ya tiene una configuración asignada.'))
        return super(ReporteConfig, self).create(vals)


# Extensión de res.users para reglas de seguridad
class ResUsers(models.Model):
    _inherit = 'res.users'

    reporte_area_ids = fields.Many2many(
        'reporte.area',
        compute='_compute_reporte_area_ids',
        string='Áreas del Usuario'
    )

    def _compute_reporte_area_ids(self):
        for user in self:
            config = self.env['reporte.config'].search([('usuario_id', '=', user.id)], limit=1)
            user.reporte_area_ids = config.area_ids if config else False