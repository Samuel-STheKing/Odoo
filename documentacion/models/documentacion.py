from odoo import models, fields, api
import re

class DocumentacionManual(models.Model):
    _name = 'documentacion.manual'
    _description = 'Almacena los manuales/documentos creados por los usuarios'
    _rec_name = 'titulo'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    categoria_id = fields.Many2one('modulo.categoria', string='Módulo/Categoría', required=True)
    
    titulo = fields.Char(string='Título', required=True, tracking=True)
    descripcion = fields.Html(string='Descripción', tracking=True)
    
    tipo = fields.Selection([
        ('pdf', 'PDF'),
        ('video', 'Video'),
        ('documento', 'Documento')
    ], string='Tipo', required=True, default='pdf', tracking=True)
    
    archivo_pdf = fields.Binary(string='Archivo PDF', attachment=True,
                                help='Subir PDF si el tipo es PDF')
    url_video = fields.Char(string='URL del Video',
                            help='URL de YouTube/Vimeo si es video')

    # Campo que guarda la URL embed — store=True para que llegue al frontend
    youtube_embed_url = fields.Char(
        compute='_compute_youtube_embed_url',
        string='URL Embebida de YouTube',
        store=True,                         # ← clave: guarda en BD
    )

    # Campo Html que genera el iframe completo — sanitize=False permite iframes
    youtube_embed_html = fields.Html(
        compute='_compute_youtube_embed_url',
        string='Vista Previa Video',
        store=False,
        sanitize=False,                     # ← necesario para renderizar iframes
    )

    numero_pagina = fields.Integer(string='Número de Página', default=1)
    roles_ids = fields.Many2many('res.groups', string='Roles aplicables')

    active = fields.Boolean(default=True, tracking=True)

    estado = fields.Selection([
        ('en_edicion', 'En Edición'),
        ('culminado', 'Culminado'),
    ], default='en_edicion', tracking=True)

    es_induccion = fields.Boolean(string='Es documento de inducción', default=False)
    fecha_creacion = fields.Datetime(string='Fecha de creación', default=fields.Datetime.now)

    def action_culminar(self):
        self.estado = 'culminado'

    def action_en_edicion(self):
        self.estado = 'en_edicion'

    @api.depends('url_video')
    def _compute_youtube_embed_url(self):
        """
        Extrae el ID del video de YouTube de diferentes formatos de URL
        y construye tanto la URL embed como el HTML del iframe.
        """
        regex = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
        for record in self:
            embed_url = False
            embed_html = False
            if record.url_video:
                match = re.search(regex, record.url_video)
                if match:
                    video_id = match.group(1)
                    embed_url = f'https://www.youtube.com/embed/{video_id}'
                    embed_html = (
                        f'<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;">'
                        f'<iframe src="{embed_url}" '
                        f'style="position:absolute;top:0;left:0;width:100%;height:100%;border:1px solid #ddd;border-radius:4px;" '
                        f'frameborder="0" allowfullscreen="true" '
                        f'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture">'
                        f'</iframe></div>'
                    )
            record.youtube_embed_url = embed_url
            record.youtube_embed_html = embed_html