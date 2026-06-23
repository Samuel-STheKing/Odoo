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

    # ==================== Mapeo Rol → Grupo de Seguridad ====================
    ROLE_GROUP_MAP = {
        'administrador': 'reportes_modulo.group_reporte_administrador',
        'supervisor': 'reportes_modulo.group_reporte_supervisor',
        'editor': 'reportes_modulo.group_reporte_editor',
        'lector': 'reportes_modulo.group_reporte_lector',
    }

    def _sync_user_groups(self):
        """Sincroniza automáticamente los grupos de Odoo según el rol asignado"""
        for record in self:
            if not record.usuario_id:
                continue
                
            user = record.usuario_id
            target_xmlid = self.ROLE_GROUP_MAP.get(record.rol)
            if not target_xmlid:
                continue

            target_group = self.env.ref(target_xmlid, raise_if_not_found=False)
            if not target_group:
                continue

            # Eliminar todos los grupos del módulo para evitar solapamientos
            category = self.env.ref('reportes_modulo.module_category_gestion_reportes')
            all_report_groups = self.env['res.groups'].search([('category_id', '=', category.id)])
            
            user.write({'groups_id': [(3, g.id) for g in all_report_groups]})

            # Asignar el grupo correcto
            user.write({'groups_id': [(4, target_group.id)]})

    # ==================== CRUD ====================
    @api.model
    def create(self, vals):
        if not self.env.user.has_group('reportes_modulo.group_reporte_administrador'):
            raise AccessError(_('Solo los administradores pueden crear configuraciones.'))
        
        if vals.get('usuario_id'):
            existing = self.search([('usuario_id', '=', vals['usuario_id'])])
            if existing:
                raise ValidationError(_('Este usuario ya tiene una configuración asignada.'))

        record = super(ReporteConfig, self).create(vals)
        record._sync_user_groups()
        return record

    def write(self, vals):
        if not self.env.user.has_group('reportes_modulo.group_reporte_administrador'):
            raise AccessError(_('Solo los administradores pueden modificar configuraciones.'))
        
        res = super(ReporteConfig, self).write(vals)
        
        # Re-sincronizar si cambia rol o usuario
        if any(key in vals for key in ['rol', 'usuario_id']):
            self._sync_user_groups()
        return res

    def unlink(self):
        if not self.env.user.has_group('reportes_modulo.group_reporte_administrador'):
            raise AccessError(_('Solo los administradores pueden eliminar configuraciones.'))
        
        for record in self:
            if record.usuario_id:
                category = self.env.ref('reportes_modulo.module_category_gestion_reportes')
                all_report_groups = self.env['res.groups'].search([('category_id', '=', category.id)])
                record.usuario_id.write({'groups_id': [(3, g.id) for g in all_report_groups]})
        
        return super(ReporteConfig, self).unlink()

    @api.constrains('usuario_id')
    def _check_usuario_unico(self):
        for record in self:
            existing = self.search([
                ('usuario_id', '=', record.usuario_id.id),
                ('id', '!=', record.id)
            ])
            if existing:
                raise ValidationError(_('Este usuario ya tiene una configuración asignada.'))

    @api.constrains('area_ids', 'rol')
    def _check_supervisor_areas(self):
        """Validación: Los supervisores deben tener al menos un área asignada"""
        for record in self:
            if record.rol == 'supervisor' and not record.area_ids:
                raise ValidationError(_('Los supervisores deben tener al menos un área asignada.'))

    @api.model
    def check_access_rights(self, operation, raise_exception=True):
        if self.env.su or self.env.is_superuser():
            return super().check_access_rights(operation, raise_exception=raise_exception)
        
        if operation == 'read' and self._context.get('allow_self_read'):
            return True
        
        if operation in ['read', 'write', 'create', 'unlink']:
            if not self.env.user.has_group('reportes_modulo.group_reporte_administrador'):
                if raise_exception:
                    raise AccessError(_('Solo los administradores pueden acceder a la configuración.'))
                return False
        return super().check_access_rights(operation, raise_exception=raise_exception)

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if self.env.su or self.env.is_superuser():
            return super().search(args, offset=offset, limit=limit, order=order, count=count)
        
        if not self.env.user.has_group('reportes_modulo.group_reporte_administrador'):
            if count:
                return 0
            return self.browse()
        return super().search(args, offset=offset, limit=limit, order=order, count=count)
    
    @api.model
    def get_user_areas(self, user_id=None):
        if user_id is None:
            user_id = self.env.user.id
        
        config = self.sudo().with_context(allow_self_read=True).search([
            ('usuario_id', '=', user_id),
            ('activo', '=', True)
        ], limit=1)
        
        if config:
            return config.area_ids
        return self.env['reporte.area']


# ==================== Extensión de res.users ====================
class ResUsers(models.Model):
    _inherit = 'res.users'

    reporte_area_ids = fields.Many2many(
        'reporte.area',
        compute='_compute_reporte_area_ids',
        store=True,  # ← SOLO ESTE CAMBIO: store=True para que las reglas funcionen
        string='Áreas del Usuario'
    )

    def _compute_reporte_area_ids(self):
        for user in self:
            config = self.env['reporte.config'].sudo().search([
                ('usuario_id', '=', user.id),
                ('activo', '=', True)
            ], limit=1)
            user.reporte_area_ids = config.area_ids if config else False