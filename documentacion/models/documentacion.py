from odoo import models, fields, api
import re
import base64
import io

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader


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

    version = fields.Char(string='Versión', default='1.0', size=20, tracking=True)

    archivo_pdf = fields.Binary(string='Archivo PDF', attachment=True)

    url_video = fields.Char(string='URL del Video')

    youtube_embed_url = fields.Char(compute='_compute_youtube_embed_url', store=True)
    youtube_embed_html = fields.Html(compute='_compute_youtube_embed_url', sanitize=False)

    numero_pagina = fields.Integer(string='Número de Páginas', default=1)

    roles_ids = fields.Many2many('res.groups', string='Roles aplicables')

    active = fields.Boolean(default=True, tracking=True)
    estado = fields.Selection([('en_edicion', 'En Edición'), ('culminado', 'Culminado')],
                              default='en_edicion', tracking=True)
    es_induccion = fields.Boolean(string='Es documento de inducción', default=False)
    fecha_creacion = fields.Datetime(default=fields.Datetime.now)

    # ==================== CONTADOR DE PÁGINAS ====================

    def _get_page_count_from_binary(self, binary_value):
        """
        Recibe el valor del campo Binary (base64 como string o bytes)
        y retorna el número de páginas del PDF.
        Retorna 1 si ocurre cualquier error.
        """
        if not binary_value:
            return 1
        try:
            # Los campos Binary en Odoo almacenan el valor como base64.
            # Puede llegar como str o como bytes según el contexto.
            if isinstance(binary_value, str):
                pdf_bytes = base64.b64decode(binary_value)
            else:
                pdf_bytes = base64.b64decode(binary_value)
            pdf_file = io.BytesIO(pdf_bytes)
            reader = PdfReader(pdf_file)
            return len(reader.pages)
        except Exception:
            return 1

    @api.onchange('archivo_pdf', 'tipo')
    def _onchange_archivo_pdf(self):
        """Actualiza el número de páginas en tiempo real al subir el PDF."""
        if self.tipo == 'pdf' and self.archivo_pdf:
            page_count = self._get_page_count_from_binary(self.archivo_pdf)
            self.numero_pagina = page_count
        else:
            self.numero_pagina = 1 if self.tipo == 'pdf' else 0

    # ==================== SINCRONIZACIÓN DE ROLES ====================

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('default_categoria_id'):
            modulo = self.env['modulo.categoria'].browse(self.env.context.get('default_categoria_id'))
            if modulo.exists() and modulo.group_ids:
                res['roles_ids'] = [(6, 0, modulo.group_ids.ids)]
        return res

    @api.model
    def create(self, vals):
        record = super().create(vals)
        if record.tipo == 'pdf' and record.archivo_pdf:
            record.numero_pagina = record._get_page_count_from_binary(record.archivo_pdf)
        return record

    def write(self, vals):
        res = super().write(vals)

        if any(key in vals for key in ['archivo_pdf', 'tipo']):
            for record in self:
                if record.tipo == 'pdf' and record.archivo_pdf:
                    record.numero_pagina = record._get_page_count_from_binary(record.archivo_pdf)

        if 'categoria_id' in vals:
            for record in self:
                modulo = record.categoria_id
                if modulo and modulo.group_ids:
                    record.roles_ids = [(6, 0, modulo.group_ids.ids)]
        return res

    # ==================== OTROS MÉTODOS ====================

    def action_guardar_edicion(self):
        return True

    def action_culminar(self):
        self.estado = 'culminado'

    def action_en_edicion(self):
        self.estado = 'en_edicion'

    @api.depends('url_video')
    def _compute_youtube_embed_url(self):
        regex = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
        for record in self:
            embed_url = embed_html = False
            if record.url_video:
                match = re.search(regex, record.url_video)
                if match:
                    video_id = match.group(1)
                    embed_url = f'https://www.youtube.com/embed/{video_id}'
                    embed_html = (
                        f'<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;">'
                        f'<iframe src="{embed_url}" '
                        f'style="position:absolute;top:0;left:0;width:100%;height:100%;'
                        f'border:1px solid #ddd;border-radius:4px;" '
                        f'frameborder="0" allowfullscreen="true" '
                        f'allow="accelerometer; autoplay; clipboard-write; encrypted-media; '
                        f'gyroscope; picture-in-picture"></iframe></div>'
                    )
            record.youtube_embed_url = embed_url
            record.youtube_embed_html = embed_html