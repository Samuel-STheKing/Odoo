from odoo import models, fields, api

class DocumentacionManual(models.Model):
    _name = 'wsl.documentacion.manual'
    _description = 'Almacena los manuales/documentos creados por los usuarios'
    _rec_name = 'titulo'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Hereda para tener el chatter (mensajería)

    # Campo que relaciona el manual con un módulo/categoría
    categoria_id = fields.Many2one('wsl.modulo.categoria', string='Módulo/Categoría', required=True)
    
    # Campos principales del manual
    titulo = fields.Char(string='Título', required=True, tracking=True)
    descripcion = fields.Html(string='Descripción', tracking=True)
    
    # Tipo de documento: PDF, Video o Documento
    tipo = fields.Selection([
        ('pdf', 'PDF'),
        ('video', 'Video'),
        ('documento', 'Documento')
    ], string='Tipo', required=True, default='pdf', tracking=True)
    
    # Campos según el tipo seleccionado
    archivo_pdf = fields.Binary(string='Archivo PDF', attachment=True, 
                                 help='Subir PDF si el tipo es PDF')
    url_video = fields.Char(string='URL del Video', 
                            help='URL de YouTube/Vimeo si es video')
    numero_pagina = fields.Integer(string='Número de Página', default=1)
    
    # Roles que pueden ver este manual
    roles_ids = fields.Many2many('res.groups', string='Roles aplicables')
    
    # Estado del documento: borrador, publicado o archivado
    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('publicado', 'Publicado'),
        ('archivado', 'Archivado')
    ], default='borrador', tracking=True)
    
    # Indica si es documento de inducción para nuevos empleados
    es_induccion = fields.Boolean(string='Es documento de inducción', default=False)
    fecha_creacion = fields.Datetime(string='Fecha de creación', default=fields.Datetime.now)
    
    # Acciones para cambiar el estado
    def action_publicar(self):
        self.estado = 'publicado'
    
    def action_archivar(self):
        self.estado = 'archivado'