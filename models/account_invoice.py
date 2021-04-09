# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import date
from datetime import datetime
from datetime import *
import datetime
from odoo.exceptions import UserError, ValidationError
from num2words import num2words
from itertools import *


class account_invoice(models.Model):
    _inherit = "account.invoice"

    
    text_amount = fields.Char(string="Total en Letras", default='Cero')

    #Nuevos requerimientos
    numero_orden_exenta = fields.Char("N° Correlativo de orden de compra exenta")
    numero_correlativo_constancia_exonerado = fields.Char("N° Correlativo de constancia de registro exonerado")
    numero_identificacion_sag = fields.Char("N° Identificativo del registro de la SAG:")

    cai_shot = fields.Char("Cai", readonly=True)
    cai_expires_shot = fields.Date("expiration_date", readonly=True)
    min_number_shot = fields.Char("min_number", readonly=True)
    max_number_shot = fields.Char("max_number", readonly=True)
    #CONVERTIR NUMEROS A LETRAS
    amount_total_text = fields.Char("Total en Letras", compute ='get_totalt', default='Cero')

    #Se agregan dos campos mas uno que guarda la ultima tasa para esa factura
    tasa_total = fields.Float("Tasa Total",  default='0.0')
    #SUMATOTAL DE DOLARES A LEMPIRAS
    TotalLPS = fields.Float("Total LPS",  default='0.0')
    #Se agrega campo donde se guarda el resultado del total en dolares * la ultima tasa agregada.  
    lps_letras = fields.Char("Total Letras",  default='Cero')

    _sql_constraints = [
    ('number', 'unique(number)', 'the invoice number must be unique, see sequence settings in the selected journal!')
    ]

    @api.depends("invoice_line_ids", "invoice_line_ids.discount", "invoice_line_ids.quantity")
    def _gettotaldiscount(self):
        for x in self.invoice_line_ids:
            total = x.price_unit * (x.discount / 100) * x.quantity
            self.total_descuento += total

    total_descuento = fields.Float("Descuento Total", compute='_gettotaldiscount')

    @api.multi
    def invoice_validate(self):
        res = super(account_invoice, self).invoice_validate()
        if self.journal_id.sequence_id.fiscal_regime:
            if self.date_invoice > self.journal_id.sequence_id.expiration_date:
                self.journal_id.sequence_id.number_next_actual = self.journal_id.sequence_id.number_next_actual -1
                raise Warning(_('la fecha de expiracion para esta secuencia es %s ') %(self.journal_id.sequence_id.expiration_date) )
            self.cai_shot = ''

            for regimen in self.journal_id.sequence_id.fiscal_regime:
                if regimen.selected:
                    self.cai_shot = regimen.cai_fiscal.cai
                    self.cai_expires_shot = regimen.cai_fiscal.expiration_date
                    #self.min_number_shot = self.journal_id.sequence_id.dis_min_value 
                    #self.max_number_shot = self.journal_id.sequence_id.dis_max_value 		
        return res
    
    #Convierte el numero a letras

    @api.one
    @api.depends('journal_id')
    def get_totalt(self):
        self.amount_total_text =''
        if self.currency_id:
            self.amount_total_text = self.to_word(self.amount_total,self.currency_id.name)
        else:
            self.amount_total_text = self.to_word(self.amount_total,self.user_id.company_id.currency_id.name)
        return True

    def to_word(self, number, mi_moneda):
        valor = number
        number = int(number)
        centavos = int((round(valor - number, 2)) * 100)
        UNIDADES = (
            '',
            'UN ',
            'DOS ',
            'TRES ',
            'CUATRO ',
            'CINCO ',
            'SEIS ',
            'SIETE ',
            'OCHO ',
            'NUEVE ',
            'DIEZ ',
            'ONCE ',
            'DOCE ',
            'TRECE ',
            'CATORCE ',
            'QUINCE ',
            'DIECISEIS ',
            'DIECISIETE ',
            'DIECIOCHO ',
            'DIECINUEVE ',
            'VEINTE '
        )

        DECENAS = (
            'VEINTE',
            'TREINTA ',
            'CUARENTA ',
            'CINCUENTA ',
            'SESENTA ',
            'SETENTA ',
            'OCHENTA ',
            'NOVENTA ',
            'CIEN ')

        CENTENAS = (
            'CIENTO ',
            'DOSCIENTOS ',
            'TRESCIENTOS ',
            'CUATROCIENTOS ',
            'QUINIENTOS ',
            'SEISCIENTOS ',
            'SETECIENTOS ',
            'OCHOCIENTOS ',
            'NOVECIENTOS '
        )
        
        MONEDAS = (
            {'country': u'Colombia', 'currency': 'COP', 'singular': u'PESO COLOMBIANO', 'plural': u'PESOS COLOMBIANOS', 'symbol': u'$'},
            {'country': u'Honduras', 'currency': 'HNL', 'singular': u'Lempira', 'plural': u'Lempiras', 'symbol': u'L'},
            {'country': u'Estados Unidos', 'currency': 'USD', 'singular': u'DÓLAR', 'plural': u'DÓLARES', 'symbol': u'US$'},
            {'country': u'Europa', 'currency': 'EUR', 'singular': u'EURO', 'plural': u'EUROS', 'symbol': u'€'},
            {'country': u'México', 'currency': 'MXN', 'singular': u'PESO MEXICANO', 'plural': u'PESOS MEXICANOS', 'symbol': u'$'},
            {'country': u'Perú', 'currency': 'PEN', 'singular': u'NUEVO SOL', 'plural': u'NUEVOS SOLES', 'symbol': u'S/.'},
            {'country': u'Reino Unido', 'currency': 'GBP', 'singular': u'LIBRA', 'plural': u'LIBRAS', 'symbol': u'£'}
        )
        
        #if mi_moneda != None:
        #    try:
        #        moneda = ifilter(lambda x: x['currency'] == mi_moneda, MONEDAS).next()
        #        if number < 2:
        #            moneda = moneda['singular']
        #        else:
        #            moneda = moneda['plural']
        #    except:
        #        return "Tipo de moneda inválida"
        #else:
        #    moneda = ""
        
        if mi_moneda != None:
            for mo in MONEDAS:
                if mo['currency'] == mi_moneda:
                    if number < 2:
                        moneda =  mo['singular']
                    else:
                        moneda =  mo['plural']
        else:
            moneda = ""

        converted = ''
        if not (0 < number < 999999999):
            return 'No es posible convertir el numero a letras'

        number_str = str(number).zfill(9)
        millones = number_str[:3]
        miles = number_str[3:6]
        cientos = number_str[6:]

        if(millones):
            if(millones == '001'):
                converted += 'UN MILLON '
            elif(int(millones) > 0):
                converted += '%sMILLONES ' % self.convert_group(millones)

        if(miles):
            if(miles == '001'):
                converted += 'MIL '
            elif(int(miles) > 0):
                converted += '%sMIL ' % self.convert_group(miles)

        if(cientos):
            if(cientos == '001'):
                converted += 'UN '
            elif(int(cientos) > 0):
                converted += '%s ' % self.convert_group(cientos)
        if(centavos) > 0:
            converted += "con %2i/100 " % centavos
        converted += moneda
        return converted.title()

    def convert_group(self, n):
        UNIDADES = (
            '',
            'UN ',
            'DOS ',
            'TRES ',
            'CUATRO ',
            'CINCO ',
            'SEIS ',
            'SIETE ',
            'OCHO ',
            'NUEVE ',
            'DIEZ ',
            'ONCE ',
            'DOCE ',
            'TRECE ',
            'CATORCE ',
            'QUINCE ',
            'DIECISEIS ',
            'DIECISIETE ',
            'DIECIOCHO ',
            'DIECINUEVE ',
            'VEINTE '
        )
        DECENAS = (
            'VEINTE',
            'TREINTA ',
            'CUARENTA ',
            'CINCUENTA ',
            'SESENTA ',
            'SETENTA ',
            'OCHENTA ',
            'NOVENTA ',
            'CIEN '
        )

        CENTENAS = (
            'CIENTO ',
            'DOSCIENTOS ',
            'TRESCIENTOS ',
            'CUATROCIENTOS ',
            'QUINIENTOS ',
            'SEISCIENTOS ',
            'SETECIENTOS ',
            'OCHOCIENTOS ',
            'NOVECIENTOS '
        )
        MONEDAS = (
            {'country': u'Colombia', 'currency': 'COP', 'singular': u'PESO COLOMBIANO', 'plural': u'PESOS COLOMBIANOS', 'symbol': u'$'},
            {'country': u'Honduras', 'currency': 'HNL', 'singular': u'Lempira', 'plural': u'Lempiras', 'symbol': u'L'},
            {'country': u'Estados Unidos', 'currency': 'USD', 'singular': u'DÓLAR', 'plural': u'DÓLARES', 'symbol': u'US$'},
            {'country': u'Europa', 'currency': 'EUR', 'singular': u'EURO', 'plural': u'EUROS', 'symbol': u'€'},
            {'country': u'México', 'currency': 'MXN', 'singular': u'PESO MEXICANO', 'plural': u'PESOS MEXICANOS', 'symbol': u'$'},
            {'country': u'Perú', 'currency': 'PEN', 'singular': u'NUEVO SOL', 'plural': u'NUEVOS SOLES', 'symbol': u'S/.'},
            {'country': u'Reino Unido', 'currency': 'GBP', 'singular': u'LIBRA', 'plural': u'LIBRAS', 'symbol': u'£'}
        )
        output = ''

        if(n == '100'):
            output = "CIEN "
        elif(n[0] != '0'):
            output = CENTENAS[int(n[0]) - 1]

        k = int(n[1:])
        if(k <= 20):
            output += UNIDADES[k]
        else:
            if((k > 30) & (n[2] != '0')):
                output += '%sY %s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])
            else:
                output += '%s%s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])

        return output

    def addComa(self, snum):
        s = snum;
        i = s.index('.') # Se busca la posición del punto decimal
        while i > 3:
            i = i - 3
            s = s[:i] + ',' + s[i:]
        return s

   