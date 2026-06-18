from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ReporteArea(models.Model):
    _name = 'reporte.area'
    _description = 'Área de Reporte'
    _rec_name = 'nombre'
    _order = 'nombre'

    nombre = fields.Char(
        string='Nombre del Área',
        required=True,
        tracking=True
    )
    
    descripcion = fields.Text(string='Descripción')
    
    reporte_ids = fields.Many2many(
        'reporte.modulo',
        string='Reportes'
    )
    
    activo = fields.Boolean(string='Activo', default=True)
    
    _sql_constraints = [
        ('nombre_unique', 'UNIQUE(nombre)', 'El nombre del área debe ser único'),
        ('nombre_upper_check', "CHECK(nombre = UPPER(nombre))", 'El nombre del área debe estar en mayúsculas'),
    ]
    
    @api.constrains('nombre')
    def _check_nombre_mayusculas(self):
        """Validar que el nombre esté en mayúsculas"""
        for record in self:
            if record.nombre and record.nombre != record.nombre.upper():
                raise ValidationError(_('El nombre del área debe estar en mayúsculas: %s') % record.nombre)
    
    @api.model
    def create(self, vals):
        # Asegurar que el nombre esté en mayúsculas al crear
        if 'nombre' in vals and vals['nombre']:
            vals['nombre'] = vals['nombre'].upper().strip()
        return super(ReporteArea, self).create(vals)
    
    def write(self, vals):
        # Asegurar que el nombre esté en mayúsculas al actualizar
        if 'nombre' in vals and vals['nombre']:
            vals['nombre'] = vals['nombre'].upper().strip()
        return super(ReporteArea, self).write(vals)
    
    def name_get(self):
        """Personalizar la visualización del nombre"""
        result = []
        for record in self:
            result.append((record.id, record.nombre))
        return result