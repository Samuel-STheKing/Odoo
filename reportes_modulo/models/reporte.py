from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
# Elimina la línea incorrecta: from odoo.tools.html import sanitize_html

class Reporte(models.Model):
    _name = 'reporte.modulo'
    _description = 'Reporte'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'titulo'

    @api.model
    def _get_default_usuario(self):
        return self.env.user.id

    codigo = fields.Char(
        string='Código',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Nuevo')
    )
    
    fecha = fields.Datetime(
        string='Fecha',
        default=fields.Datetime.now,
        required=True
    )
    
    usuario_id = fields.Many2one(
        'res.users',
        string='Usuario',
        default=_get_default_usuario,
        required=True,
        tracking=True
    )
    
    titulo = fields.Char(
        string='Título',
        required=True,
        tracking=True
    )
    
    contenido = fields.Html(
        string='Contenido del Reporte',
        required=True,
        sanitize=False,  # Permite HTML sin sanitizar
        sanitize_attributes=False,
        sanitize_tags=False
    )
    
    area_ids = fields.Many2many(
        'reporte.area',
        string='Áreas',
        required=True
    )
    
    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('guardado', 'Guardado'),
        ('enviado', 'Enviado'),
    ], string='Estado', default='borrador', tracking=True)
    
    fecha_guardado = fields.Datetime(string='Fecha de Guardado', readonly=True)
    fecha_borrador = fields.Datetime(string='Fecha de Borrador', readonly=True)

    @api.model
    def create(self, vals):
        if vals.get('codigo', _('Nuevo')) == _('Nuevo'):
            vals['codigo'] = self.env['ir.sequence'].next_by_code('reporte.modulo') or _('Nuevo')
        return super(Reporte, self).create(vals)

    def action_guardar(self):
        """Acción para guardar el reporte"""
        for record in self:
            # Validar contenido (verificar que no esté vacío)
            if not record.contenido or record.contenido.strip() in ['', '<p><br></p>', '<p></p>']:
                raise ValidationError(_('El contenido del reporte no puede estar vacío'))
            
            # Validar título
            if not record.titulo or not record.titulo.strip():
                raise ValidationError(_('El título no puede estar vacío'))
            
            # Validar áreas
            if not record.area_ids:
                raise ValidationError(_('Debes seleccionar al menos un área'))
            
            record.estado = 'guardado'
            record.fecha_guardado = fields.Datetime.now()
    
    def action_borrador(self):
        """Acción para pasar a borrador"""
        for record in self:
            record.estado = 'borrador'
            record.fecha_borrador = fields.Datetime.now()
    
    def action_enviar(self):
        """Acción para enviar el reporte"""
        for record in self:
            if record.estado != 'guardado':
                raise ValidationError(_('El reporte debe estar guardado antes de enviarlo'))
            record.estado = 'enviado'
    
    @api.constrains('titulo')
    def _check_titulo(self):
        """Validar que el título no sea solo espacios"""
        for record in self:
            if record.titulo and not record.titulo.strip():
                raise ValidationError(_('El título no puede contener solo espacios en blanco'))