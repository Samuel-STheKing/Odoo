from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

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
        sanitize=False,
        sanitize_attributes=False,
        sanitize_tags=False
    )
    
    area_ids = fields.Many2many(
        'reporte.area',
        'reporte_modulo_area_rel',
        'reporte_id',
        'area_id',
        string='Áreas',
        required=True
    )
    
    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('guardado', 'Guardado'),
        ('culminado', 'Culminado'),
        ('enviado', 'Enviado'),
    ], string='Estado', default='borrador', tracking=True)
    
    fecha_guardado = fields.Datetime(string='Fecha de Guardado', readonly=True)
    fecha_borrador = fields.Datetime(string='Fecha de Borrador', readonly=True)
    fecha_culminado = fields.Datetime(string='Fecha de Culminado', readonly=True)

    @api.model
    def create(self, vals):
        if vals.get('codigo', _('Nuevo')) == _('Nuevo'):
            vals['codigo'] = self.env['ir.sequence'].next_by_code('reporte.modulo') or _('Nuevo')
        return super(Reporte, self).create(vals)

    def write(self, vals):
        campos_protegidos = {'titulo', 'fecha', 'usuario_id', 'area_ids', 'contenido'}
        for record in self:
            if record.estado == 'enviado' and campos_protegidos.intersection(vals.keys()):
                raise ValidationError(_(
                    'No se puede modificar el reporte "%s" porque ya fue enviado.'
                ) % record.titulo)
        return super(Reporte, self).write(vals)

    def action_guardar_borrador(self):
        for record in self:
            if not record.titulo or not record.titulo.strip():
                raise ValidationError(_('El título no puede estar vacío'))
            record.estado = 'borrador'
            record.fecha_borrador = fields.Datetime.now()
            record.fecha_guardado = False
            record.fecha_culminado = False

    def action_guardar(self):
        for record in self:
            if not record.contenido or record.contenido.strip() in ['', '<p><br></p>', '<p></p>']:
                raise ValidationError(_('El contenido del reporte no puede estar vacío'))
            if not record.titulo or not record.titulo.strip():
                raise ValidationError(_('El título no puede estar vacío'))
            if not record.area_ids:
                raise ValidationError(_('Debes seleccionar al menos un área'))
            record.estado = 'guardado'
            record.fecha_guardado = fields.Datetime.now()

    def action_culminar(self):
        for record in self:
            if not record.contenido or record.contenido.strip() in ['', '<p><br></p>', '<p></p>']:
                raise ValidationError(_('El contenido del reporte no puede estar vacío'))
            if not record.titulo or not record.titulo.strip():
                raise ValidationError(_('El título no puede estar vacío'))
            if not record.area_ids:
                raise ValidationError(_('Debes seleccionar al menos un área'))
            record.estado = 'culminado'
            record.fecha_culminado = fields.Datetime.now()
            record.fecha_guardado = fields.Datetime.now()

    def action_borrador(self):
        for record in self:
            if record.estado == 'enviado':
                raise ValidationError(_('No se puede volver a borrador un reporte enviado'))
            record.estado = 'borrador'
            record.fecha_borrador = fields.Datetime.now()
            record.fecha_guardado = False
            record.fecha_culminado = False

    def action_enviar(self):
        for record in self:
            if record.estado not in ['guardado', 'culminado']:
                raise ValidationError(_('El reporte debe estar guardado o culminado antes de enviarlo'))
            if not record.contenido or record.contenido.strip() in ['', '<p><br></p>', '<p></p>']:
                raise ValidationError(_('El contenido del reporte no puede estar vacío'))
            if not record.titulo or not record.titulo.strip():
                raise ValidationError(_('El título no puede estar vacío'))
            if not record.area_ids:
                raise ValidationError(_('Debes seleccionar al menos un área'))
            record.estado = 'enviado'
