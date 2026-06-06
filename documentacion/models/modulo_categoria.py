from odoo import models, fields, api

class ModuloCategoria(models.Model):
    _name = 'modulo.categoria'
    _description = 'Módulos o categorías que agrupan manuales (ej: Ventas, Compras, Contabilidad)'
    _rec_name = 'nombre'
    _order = 'nombre'

    # Información básica del módulo
    nombre = fields.Char(string='Nombre del Módulo', required=True)
    descripcion = fields.Text(string='Descripción')
    activo = fields.Boolean(string='Activo', default=True)
    
    manual_ids = fields.One2many('documentacion.manual', 'categoria_id', string='Manuales')
    cantidad_manuales = fields.Integer(string='Cantidad de Manuales', compute='_compute_cantidad_manuales')

    # Grupos de Odoo autorizados a ver este módulo y sus manuales.
    # Si está vacío, todos los usuarios de documentación pueden verlo.
    group_ids = fields.Many2many(
        'res.groups',
        'modulo_categoria_groups_rel',
        'modulo_id',
        'group_id',
        string='Aplicaciones con Acceso',
        domain="[('category_id', '!=', False)]",
        help='Seleccione los grupos de Odoo cuyo permiso habilita ver este módulo. '
             'Si no se selecciona ninguno, todos los usuarios de documentación pueden verlo.',
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