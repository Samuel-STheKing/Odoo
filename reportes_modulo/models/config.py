from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ReporteConfig(models.Model):
    _name = 'reporte.config'
    _description = 'Configuración de Reportes'
    _rec_name = 'usuario_id'

    # Rol del usuario logueado (siempre readonly, calculado)
    rol_actual = fields.Selection([
        ('administrador', 'Administrador'),
        ('editor', 'Editor'),
        ('lector', 'Lector'),
        ('supervisor', 'Supervisor'),
    ], string='Tu Rol Actual', compute='_compute_rol_actual', store=False)

    # Usuario al que se le asigna el rol
    usuario_id = fields.Many2one(
        'res.users',
        string='Asignar Rol a',
        required=True,
    )

    rol = fields.Selection([
        ('administrador', 'Administrador'),
        ('editor', 'Editor'),
        ('lector', 'Lector'),
        ('supervisor', 'Supervisor'),
    ], string='Rol Asignado', required=True, default='lector')

    activo = fields.Boolean(string='Activo', default=True)

    @api.depends()
    def _compute_rol_actual(self):
        """Busca el rol del usuario logueado en la tabla de configuración."""
        for record in self:
            config = self.search([('usuario_id', '=', self.env.user.id)], limit=1)
            record.rol_actual = config.rol if config else 'administrador'

    @api.constrains('usuario_id')
    def _check_usuario_unico(self):
        for record in self:
            existing = self.search([
                ('usuario_id', '=', record.usuario_id.id),
                ('id', '!=', record.id)
            ])
            if existing:
                raise ValidationError(_('Este usuario ya tiene un rol asignado.'))

    @api.model
    def create(self, vals):
        if vals.get('usuario_id'):
            existing = self.search([('usuario_id', '=', vals['usuario_id'])])
            if existing:
                raise ValidationError(_('Este usuario ya tiene un rol asignado.'))
        return super(ReporteConfig, self).create(vals)