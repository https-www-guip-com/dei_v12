# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import date
from datetime import datetime
from datetime import *
import datetime
from odoo.exceptions import UserError, ValidationError

class fiscal_regime(models.Model):
    _name = "test_fiscal_regime"
    _order = 'cai_fiscal'
    _rec_name = 'cai_fiscal'

    cai_fiscal = fields.Many2one('test_model_dei', required=True)
    sequence = fields.Many2one('ir.sequence')
    selected = fields.Boolean('selected')
    desde = fields.Integer('Desde')
    hasta = fields.Integer('Hasta') 

@api.onchange('selected')
def disable_other_regimes(self):
    if self.selected:
        lista = self.env['test_fiscal_regime'].search([('sequence.name','=',self.sequence.name)])
        for regime in lista:
             regime.write({'selected':0})
        self.write({'selected':1})   

class menu_principal_dei(models.Model):
    _name = "test_model_dei"
    #Esta herencia funciona para que se pueda mostrar el pie de pagina en los formularios con las notas y poder enviar correos
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'cai'
    _rec_name = 'cai'

    expiration_date = fields.Date("Fecha Expiracion",  required=True, select=True)
    cai = fields.Char('CAI', help='Clave de Autorización de Impresión ', required=True, select=True)
    compania = fields.Many2one('res.company', required=True)
    fiscal_regimes = fields.One2many('test_fiscal_regime','cai_fiscal', string="Regimen Fiscal")
