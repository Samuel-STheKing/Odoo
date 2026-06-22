from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError


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
        # Verificar permisos
        if not self.env.user.has_group('reportes_modulo.group_reporte_administrador'):
            raise AccessError(_('Solo los administradores pueden crear configuraciones.'))
        
        if vals.get('usuario_id'):
            existing = self.search([('usuario_id', '=', vals['usuario_id'])])
            if existing:
                raise ValidationError(_('Este usuario ya tiene una configuración asignada.'))
        return super(ReporteConfig, self).create(vals)

    def write(self, vals):
        # Verificar permisos
        if not self.env.user.has_group('reportes_modulo.group_reporte_administrador'):
            raise AccessError(_('Solo los administradores pueden modificar configuraciones.'))
        return super(ReporteConfig, self).write(vals)

    def unlink(self):
        # Verificar permisos
        if not self.env.user.has_group('reportes_modulo.group_reporte_administrador'):
            raise AccessError(_('Solo los administradores pueden eliminar configuraciones.'))
        return super(ReporteConfig, self).unlink()

    @api.model
    def check_access_rights(self, operation, raise_exception=True):
        """Sobrescribir para verificar permisos en operaciones de lectura"""
        if operation in ['read', 'write', 'create', 'unlink']:
            if not self.env.user.has_group('reportes_modulo.group_reporte_administrador'):
                if raise_exception:
                    raise AccessError(_('Solo los administradores pueden acceder a la configuración.'))
                return False
        return super(ReporteConfig, self).check_access_rights(operation, raise_exception=raise_exception)

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """Sobrescribir search para evitar que usuarios no admin vean configuraciones"""
        if not self.env.user.has_group('reportes_modulo.group_reporte_administrador'):
            # Si no es admin, devolver recordset vacío o solo su propia configuración
            if count:
                return 0
            return self.browse()
        return super(ReporteConfig, self).search(args, offset=offset, limit=limit, order=order, count=count)


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