# -*- coding: utf-8 -*-
import requests 
import xlsxwriter
import os
import numpy as np
import pandas as pd
import pandas.io.sql
import pytz
from odoo.exceptions import UserError
from odoo.modules import get_modules, get_module_path
from datetime import datetime
from odoo import models, fields, api
import base64
import pymssql


class SAPINVNotKwitansi(models.TransientModel):
    _name           = "sap.notkwitansi"
    _description    = "sap.notkwitansi"
    company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
    datefrom          = fields.Date ("Date To", default=lambda s:fields.Date.today()) 
    dateto          = fields.Date ("Date To", default=lambda s:fields.Date.today()) 
    export_to       = fields.Selection([ ('xls', 'Excel'),],string='Export To', default='xls')
    filexls         = fields.Binary("File Output")    
    filenamexls     = fields.Char("File Name Output")


    @api.multi
    def view_notkwitansi_xls(self): 
        #PATH FILE 
        mpath       = get_module_path('cnw_invar')
        filenamexls2    = 'NotKwitansi_' + self.env.user.company_id.code_base + "_"  + self.env.user.name  +   self.dateto.strftime("%Y%m%d")   + '.xlsx'
        filename    = 'NotKwitansi_' + self.env.user.company_id.code_base + "_"  + self.env.user.name  +   self.dateto.strftime("%Y%m%d")   + '.xlsx'
        filepath    = mpath + '/temp/'+ filename

        #SERVER CONFIGURATION
        host        = self.env.user.company_id.server
        database    = self.env.user.company_id.db_name
        user        = self.env.user.company_id.db_usr
        password    = self.env.user.company_id.db_pass
        listfinal=[]
        #EXECUTE STORE PROCEDURE 
        conn = pymssql.connect(host=host, user=user, password=password, database=database)

        cursor = conn.cursor()
        mssql=   "exec [dbo].[IGU_INVOICE_NOT_KWITANSI_DATE] '" +  self.datefrom.strftime("%Y%m%d") + "','" +  self.dateto.strftime("%Y%m%d") + "','" +  self.company_id.code_base + "'" 

        data = pandas.io.sql.read_sql(mssql,conn) 
        listfinal.append(data)
        df = pd.concat(listfinal) 

        if self.export_to =="xls":
            filename = filenamexls2 
            #report = df.groupby(["Group","AR Person"]).sum()
            df.to_excel(mpath + '/temp/'+ filenamexls2,index=False,engine='xlsxwriter')          
        
        # SAVE TO MODEL.BINARY 
        file = open(mpath + '/temp/'+ filename , 'rb')
        out = file.read()
        file.close()
        self.filexls =base64.b64encode(out)
        self.filenamexls = filename
        os.remove(mpath + '/temp/'+ filename )
        return {
            'name': 'Report',
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=" + self._name +"&id=" + str(
                self.id) + "&filename_field=filenamexls&field=filexls&download=true&filename=" + self.filenamexls,
            'target': 'new',
            }

 
         
        
 
