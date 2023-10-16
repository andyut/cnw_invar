# -*- coding: utf-8 -*-
import requests 
import xlsxwriter
import numpy as np
import pandas as pd
import pandas.io.sql
import os
import pytz
from odoo.exceptions import UserError
from odoo.modules import get_modules, get_module_path
from datetime import datetime
from odoo import models, fields, api
import base64
import pymssql


class CNW_pembayaranharian(models.TransientModel):
    _name           = "cnw.awr28.pembayaranharian"
    _description    = "cnw.pembayaranharian"
    company_id      = fields.Many2many('res.company', string="Company",required=True)
    
    datefrom        = fields.Date ("Date From", default=fields.Date.today())
    dateto          = fields.Date ("Date To", default=fields.Date.today()) 
    filexls         = fields.Binary("File Output")    
    filenamexls     = fields.Char("File Name Output")
    
    @api.multi
    def view_pembayaranharian(self): 
        mpath       = get_module_path('cnw_awr28')
        filename    = 'pembayaran_'+   self.dateto.strftime("%Y%m%d")  + '.xlsx'
        filepath    = mpath + '/temp/'+ filename
        listfinal = []
        for comp in self.company_id:
            host        = comp.server
            database    = comp.db_name
            user        = comp.db_usr
            password    = comp.db_pass
            print (host,database,user,password)
            
            #conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';UID='+user+';PWD='+ password + ';TrustServerCertificate=yes')
            conn = pymssql.connect(host=host, user=user, password=password, database=database)
            cursor = conn.cursor()
            
            cursor.execute( "exec [dbo].[IGU_ACT_pembayarandetail] '" +  self.datefrom.strftime("%Y%m%d") + "', '" +  self.dateto.strftime("%Y%m%d") + "','" + comp.code_base +"'")

            rowdata = cursor.fetchall()  
            listfinal += rowdata
        label=["Company",
                "journalEntry",
                "TransNo",
                "RefDate",
                "cardcode",
                "cardname",
                "PaymentGroup",
                "maingroup",
                "groupname",
                "U_AR_Person",
                "Payment",
                "UnReconsile Payment" ,
                ]
        #print (listfinal)
        df = pd.DataFrame.from_records(listfinal,columns=label,coerce_float=True)

        df.to_excel(mpath + '/temp/'+ filename )  
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
 
#        conn.close()    

 
