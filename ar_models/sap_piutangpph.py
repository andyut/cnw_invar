# -*- coding: utf-8 -*-
import requests 
import pandas as pd
import io
import os
from odoo.exceptions import UserError
from odoo.modules import get_modules, get_module_path
from datetime import datetime
from odoo import models, fields, api
import base64


class SAPPiutangPPH(models.TransientModel):
    _name           = "sap.piutang.pph"
    _description    = "sap.piutang.pph"
    company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
    datefrom         = fields.Date ("Date From", default=fields.Date.today())
    dateto          = fields.Date ("Date To", default=fields.Date.today())
    account         = fields.Char("Account Code / Name",default="1136001") 
    filexls         = fields.Binary("File Output")    
    filenamexls     = fields.Char("File Name Output")
    
    @api.multi
    def view_piutangpph_xls(self): 
        mpath = get_module_path('igu_actreport')
        filename = 'pph23_from' +  self.datefrom.strftime("%Y%m%d")  +'_'+  self.dateto.strftime("%Y%m%d") + '.xls' 

        url =  'http://192.168.1.171/odoo_webapps/sap-piutangpph.asp?company={}&datefrom={}&dateto={}&account={}'.format(self.env.user.company_id.code_base, self.datefrom.strftime("%Y%m%d") , self.dateto.strftime("%Y%m%d"), self.account)
        
        s = requests.get(url).content
        ds = pd.read_csv(io.StringIO(s.decode('utf-8')),sep=";")
        writer = pd.ExcelWriter(mpath + '/temp/'+ filename )
        
        ds.to_excel(writer,index=0)
        writer.save() 
        file = open(mpath + '/temp/'+ filename , 'rb')
        out = file.read()
        file.close()
        os.remove(mpath + '/temp/'+ filename )
        self.filexls =base64.b64encode(out)
        self.filenamexls = filename
        return {
            'name': 'Report',
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=" + self._name +"&id=" + str(
                self.id) + "&filename_field=filenamexls&field=filexls&download=true&filename=" + self.filenamexls,
            'target': 'new',
            }

         
        
 