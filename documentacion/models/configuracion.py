from odoo import models, fields, api
from odoo.exceptions import UserError

class ConfiguracionModulos(models.TransientModel):
    _name = 'wsl.configuracion.modulos'
    _description = 'Ventana de configuración para crear nuevos módulos'

    # Configuración existente (legacy)
    modulo_seleccionado = fields.Selection([
        ('ventas', 'Ventas'),
        ('compras', 'Compras'),
        ('inventario', 'Inventario')
    ], string='Módulo', required=True)
    
    activar_manuales = fields.Boolean(string='Activar manuales', default=True)
    orden_visualizacion = fields.Integer(string='Orden de visualización', default=10)
    
    # Campos para crear un nuevo módulo
    nuevo_modulo_nombre = fields.Char(string='Nombre del nuevo módulo')
    nuevo_modulo_descripcion = fields.Text(string='Descripción del nuevo módulo')
    
    def action_crear_modulo(self):
        """Crea un nuevo módulo/categoría en el sistema"""
        if not self.nuevo_modulo_nombre:
            raise UserError('Debe ingresar un nombre para el módulo')
        
        # Verifica que no exista otro módulo con el mismo nombre
        existe = self.env['wsl.modulo.categoria'].search([
            ('nombre', '=', self.nuevo_modulo_nombre)
        ])
        
        if existe:
            raise UserError(f'Ya existe un módulo con el nombre "{self.nuevo_modulo_nombre}"')
        
        # Crea el nuevo módulo
        self.env['wsl.modulo.categoria'].create({
            'nombre': self.nuevo_modulo_nombre,
            'descripcion': self.nuevo_modulo_descripcion,
            'activo': True,
        })
        
        # Muestra mensaje de éxito
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Módulo creado',
                'message': f'El módulo "{self.nuevo_modulo_nombre}" ha sido creado exitosamente',
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_ver_modulos(self):
        """Muestra todos los módulos existentes"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Módulos Disponibles',
            'res_model': 'wsl.modulo.categoria',
            'view_mode': 'tree,form',
            'target': 'current',
        }


class ConfiguracionRoles(models.TransientModel):
    _name = 'wsl.configuracion.roles'
    _description = 'Configuración de permisos por rol de usuario'

    rol_id = fields.Many2one('res.groups', string='Rol')
    modulos_permitidos = fields.Many2many('ir.module.module', string='Módulos permitidos')
    ver_manuales = fields.Boolean(string='Puede ver manuales', default=True)
    ver_inducciones = fields.Boolean(string='Puede ver inducciones', default=True)