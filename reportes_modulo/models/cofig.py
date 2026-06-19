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
        default=lambda self: self.env.user
    )
    
    rol = fields.Selection([
        ('administrador', 'Administrador'),
        ('editor', 'Editor'),
        ('lector', 'Lector'),
        ('supervisor', 'Supervisor'),
    ], string='Rol Asignado', required=True, default='lector')
    
    rol_actual = fields.Selection([
        ('administrador', 'Administrador'),
        ('editor', 'Editor'),
        ('lector', 'Lector'),
        ('supervisor', 'Supervisor'),
    ], string='Tu Rol Actual', readonly=True, default='administrador')
    
    activo = fields.Boolean(string='Activo', default=True)
    
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
        # Verificar si ya existe configuración para este usuario
        if vals.get('usuario_id'):
            existing = self.search([('usuario_id', '=', vals['usuario_id'])])
            if existing:
                raise ValidationError(_('Este usuario ya tiene un rol asignado.'))
        return super(ReporteConfig, self).create(vals)