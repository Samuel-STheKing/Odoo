from odoo import models, fields, api

class ModuloCategoria(models.Model):
    _name = 'modulo.categoria'
    _description = 'Módulos o categorías que agrupan manuales'
    _rec_name = 'nombre'
    _order = 'nombre'

    # Información básica del módulo
    nombre = fields.Char(string='Nombre del Módulo', required=True)
    descripcion = fields.Text(string='Descripción')
    activo = fields.Boolean(string='Activo', default=True)
    
    manual_ids = fields.One2many('documentacion.manual', 'categoria_id', string='Manuales')
    cantidad_manuales = fields.Integer(string='Cantidad de Manuales', compute='_compute_cantidad_manuales')

    # Grupos de Odoo autorizados a ver este módulo y sus manuales.
    group_ids = fields.Many2many(
        'res.groups',
        'modulo_categoria_groups_rel',
        'modulo_id',
        'group_id',
        string='Aplicaciones con Acceso',
        domain="[('category_id', '!=', False)]",
        help='Grupos de Odoo que pueden ver este módulo y sus manuales. '
             'Si está vacío, todos los usuarios con acceso al módulo Documentación pueden verlo.',
    )
    
    @api.depends('manual_ids')
    def _compute_cantidad_manuales(self):
        for record in self:
            record.cantidad_manuales = len(record.manual_ids)
    
    def action_ver_manuales(self):
        return {
            'type': 'ir.actions.act_window',
            'name': f'Manuales — {self.nombre}',
            'res_model': 'documentacion.manual',
            'view_mode': 'tree,form',
            'domain': [('categoria_id', '=', self.id)],
            'context': {'default_categoria_id': self.id},
        }

    # ==================== SINCRONIZACIÓN DE ACCESO ====================
    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._sincronizar_grupos_a_manuales()
        return record

    def write(self, vals):
        res = super().write(vals)
        if 'group_ids' in vals:
            self._sincronizar_grupos_a_manuales()
        return res

    def _sincronizar_grupos_a_manuales(self):
        """Propaga los grupos del módulo a todos sus manuales existentes"""
        for modulo in self:
            if modulo.manual_ids:
                modulo.manual_ids.write({'roles_ids': [(6, 0, modulo.group_ids.ids)]})