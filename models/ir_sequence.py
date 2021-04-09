# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import date
from datetime import datetime
from datetime import *
import datetime
from odoo.exceptions import UserError, ValidationError

class ir_sequence(models.Model):
    _inherit = "ir.sequence"

    fiscal_regime = fields.One2many('test_fiscal_regime', 'sequence')

    start_date = fields.Date('Start Date')
    expiration_date = fields.Date('Expiration Date', compute="get_expiration_date")
    min_value = fields.Integer('min value', compute="get_min_value")
    max_value = fields.Integer('max value', compute="get_max_value")
    dis_min_value = fields.Char('min number', compute="display_min_value", readonly=True )
    dis_max_value = fields.Char('max number',  compute="display_max_value", readonly=True)

    percentage_alert = fields.Float('percentage alert', default=80)
    #percentage 		= fields.Float('percentage' )
    percentage = fields.Float('percentage', compute='compute_percentage')

    l_prefix = fields.Char('prefix', related='prefix')
    l_padding = fields.Integer('Number padding', related='padding')
    l_number_next_actual = fields.Integer('Next Number', related='number_next_actual')

    @api.model
    def create(self, values):
        new_id = super(ir_sequence, self).create(values)
        self.validar()
        return new_id

#	def write(self, cr, uid, ids, vals, context=None):
    @api.multi
    def write(self,values):
        write_id = super(ir_sequence, self).write(values)
        self.validar()
        return write_id 
    
    def validar(self):
        """ Verify unique cai in sequence """
        already_in_list = []
        for fiscal_line in self.fiscal_regime:
            if fiscal_line.cai_fiscal.cai in already_in_list:
                raise Warning(_(' %s this cai is already in use ') % (fiscal_line.cai_fiscal.cai ))
            already_in_list.append(fiscal_line.cai_fiscal.cai)
        """ No overlap """
        for fiscal_line in self.fiscal_regime:
            for fiscal_line_compare in self.fiscal_regime:
                if fiscal_line.desde > fiscal_line_compare.desde and fiscal_line.desde < fiscal_line_compare.hasta:
                    raise Warning(_('%s to %s fiscal line overlaps ' ) % (fiscal_line.desde,fiscal_line.hasta))
                if fiscal_line.hasta > fiscal_line_compare.desde and fiscal_line.hasta < fiscal_line_compare.hasta:
                    raise Warning(_('%s to %s fiscal line overlaps ' ) % (fiscal_line.desde,fiscal_line.hasta))
        """ desde < hasta """
        for fiscal_line in self.fiscal_regime:
            if fiscal_line.desde > fiscal_line.hasta:
                raise Warning(_('min_value %s to max_value %s' ) %(fiscal_line.desde,fiscal_line.hasta))

    #Obtiene la fecha de expiracion
    @api.depends('fiscal_regime')
    @api.one
    def get_expiration_date(self):
        if self.fiscal_regime:
            for regime in self.fiscal_regime:
                if regime.selected:
                    self.expiration_date = regime.cai_fiscal.expiration_date

    #Se obtiene el minimo de la factura ingresa
    @api.depends('fiscal_regime')
    @api.one
    def get_min_value(self):
        if self.fiscal_regime:
            for regime in self.fiscal_regime:
                if regime.selected:
                    self.min_value = regime.desde
        else:
            self.min_value = 0

    #Se obtiene el maximo de la factura ingresa
    @api.depends('fiscal_regime')
    @api.one
    def get_max_value(self):
        if self.fiscal_regime:
            for regime in self.fiscal_regime:
                if regime.selected:
                    self.max_value = regime.hasta
        else:
            self.max_value = 0

    #ESTA MALO ESTAS FUNCIONES MIN VALU Y MAX VALUE
    @api.multi
    def display_min_value(self):
            # rellenar con ceros hasta el numero inicial con el padding especificado
            start_number_filled = str(self.min_value)
            for relleno in range(len(str(self.min_value)), self.padding):
                start_number_filled = '0'+ start_number_filled
            self.dis_min_value = str(self.prefix) + str(start_number_filled)
            

    @api.multi
    def display_max_value(self):
            # rellenar con ceros hasta el numero final con el padding especificado
            final_number_filled = str(self.max_value)
            for relleno in range(len(str(self.max_value)), self.padding):
                final_number_filled = '0'+ final_number_filled
            self.dis_max_value = str(self.prefix) +  str(final_number_filled)
            

    #porcentaje
    @api.depends('number_next')
    def compute_percentage(self):
        numerador = self.number_next_actual - self.min_value
        denominador = self.max_value - self.min_value
        if denominador > 0:			
            division = (self.number_next_actual - self.min_value) / (self.max_value - self.min_value)
            self.percentage = (division * 100) - 1
        else:
            self.percentage = 0

    def _next(self):
        # Esta parte hace lo mismo que hacia antes la funcion
        if not self._ids:
            return False
        if self._context is None:
            self._context = {} 
        force_company = self._context.get('force_company')
        if not force_company:
            force_company = self.env['res.users'].browse(self.env.uid).company_id.id
        domain = [('id', 'in', self._ids)]
        sequences = self.env['ir.sequence'].search_read( domain, ['name','company_id','implementation','number_next','prefix','suffix','padding'] )  
        preferred_sequences = [s for s in sequences if s['company_id'] and s['company_id'][0] == force_company ]
        seq = preferred_sequences[0] if preferred_sequences else sequences[0]
        
        if seq['implementation'] == 'standard':
            self.env.cr.execute("SELECT nextval('ir_sequence_%03d')" % seq['id'])
            seq['number_next'] = self.env.cr.fetchone()
        else:
            self.env.cr.execute("SELECT number_next FROM ir_sequence WHERE id=%s FOR UPDATE NOWAIT", (seq['id'],))
            self.env.cr.execute("UPDATE ir_sequence SET number_next=number_next+number_increment WHERE id=%s ", (seq['id'],))
            self.invalidate_cache(['number_next'], [seq['id']])
        d = self._get_prefix_suffix()
        
        try:
            interpolated_prefix = d[0] 
            interpolated_suffix = d[1] 
        except ValueError:
            raise osv.except_osv(_('Warning'), _('Invalid prefix or suffix for sequence \'%s\'') % (seq.get('name')))
        # nuevas funcione
        # chequea que la secuencia esta vigente 
        self.check_limits(self._ids)
        # Guarda en la factura las viarables de la secuencia para futuras consultas como el cai que se usaba en el momento, 
        # los limites de la secuencia y la fecha de expiracion, todo esto es necesario para que se imprima en la factura
        return interpolated_prefix + '%%0%sd' % seq['padding'] % seq['number_next'] + interpolated_suffix
    
    def check_limits(self, ids):
        this_sequence =  self.env['ir.sequence'].browse(ids)
        #self.pool.get('ir.sequence').browse(cr,uid,ids)

        """ Verificar si la secuencia tiene regimenes fiscales """
        # No generar numeros si no hay secuencias activadas
        if this_sequence.fiscal_regime:
            flag_any_active = False
            for regimen in this_sequence.fiscal_regime:
                if regimen.selected:
                    flag_any_active = True
                    break

            if not flag_any_active:
                raise Warning(_('La secuencia no tiene ningun regimen seleccionado '))
        else:
        # si no hay regimen fiscal agregado a esta secuencia no es necesario validar hacer mas validaciones
            return True

        """ Alerta de que restan pocos numeros en la secuencia """
        if this_sequence.percentage and this_sequence.percentage_alert:
            if this_sequence.percentage > this_sequence.percentage_alert:
                restantes = (this_sequence.max_value - this_sequence.number_next) + 1

        if this_sequence.max_value:
            this_number = this_sequence.number_next_actual - 1
            if this_number > this_sequence.max_value :
                raise Warning(_('you have no more numbers for this sequence ' 'this number is %s ' 'your limit is %s numbers ' )
                    %(this_number,this_sequence.max_value ))


        return True
ir_sequence()