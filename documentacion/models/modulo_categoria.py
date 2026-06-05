from odoo import models, fields, api

class ModuloCategoria(models.Model):
    _name = 'wsl.modulo.categoria'
    _description = 'Módulos o categorías que agrupan manuales (ej: Ventas, Compras, Contabilidad)'
    _rec_name = 'nombre'
    _order = 'nombre'

    # Información básica del módulo
    nombre = fields.Char(string='Nombre del Módulo', required=True)
    descripcion = fields.Text(string='Descripción')
    activo = fields.Boolean(string='Activo', default=True)
    
    # Lista de manuales que pertenecen a este módulo
    manual_ids = fields.One2many('wsl.documentacion.manual', 'categoria_id', string='Manuales')
    
    # Campo calculado que muestra cuántos manuales tiene el módulo
    cantidad_manuales = fields.Integer(string='Cantidad de Manuales', compute='_compute_cantidad_manuales')
    
    @api.depends('manual_ids')
    def _compute_cantidad_manuales(self):
        for record in self:
            record.cantidad_manuales = len(record.manual_ids)
    
    # Acción que muestra los manuales de este módulo en una nueva vista
    def action_ver_manuales(self):
        return {
            'type': 'ir.actions.act_window',
            'name': f'Manuales - {self.nombre}',
            'res_model': 'wsl.documentacion.manual',
            'view_mode': 'kanban,tree,form',
            'domain': [('categoria_id', '=', self.id)],
            'context': {'default_categoria_id': self.id},
        }