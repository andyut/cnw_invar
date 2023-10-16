# -*- coding: utf-8 -*-
import requests 
import xlsxwriter
import numpy as np
import pandas as pd
import pandas.io.sql
import os
import pdfkit
import pytz
from odoo.exceptions import UserError
from odoo.modules import get_modules, get_module_path
from datetime import datetime
from odoo import models, fields, api
import base64
import pymssql
from jinja2 import Environment, FileSystemLoader

class CNW_AnalysisPiutangREPORT(models.TransientModel):
    _name           = "cnw.awr28.analysispiutang"
    _description    = "cnw.awr28.analysispiutang"
    company_id      = fields.Many2many('res.company', string="Company",required=True)
     
    datefrom        = fields.Date ("Date From", default=fields.Date.today()) 
    dateto          = fields.Date ("Date To", default=fields.Date.today()) 
    partner        = fields.Char("partner")
    export_to       = fields.Selection([ ('xls', 'Excel'),('xlspivot', 'xlspivot'),],string='Export To', default='pdf')
    filexls         = fields.Binary("File Output")    
    filenamexls     = fields.Char("File Name Output")
    
    @api.multi
    def view_awr28_analysispiutang(self): 
        mpath       = get_module_path('cnw_awr28')
        filenamexls = 'sls_analysispiutang_'+   self.dateto.strftime("%Y%m%d")  + '.xlsx'
        filenamepdf = 'sls_analysispiutang_'+   self.dateto.strftime("%Y%m%d")  + '.pdf'
        filename    =""
        filepath    = mpath + '/temp/'
        logo        = mpath + '/awr_template/logoigu.png'
        listfinal   = []
        cssfile     = mpath + '/awr_template/style.css'

        #global Var

        igu_title = "Analysis Piutang"
        igu_tanggal = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")
        igu_remarks = "Analysis Piutang Per Tanggal "
        options = {
                    'page-size': 'legal',
                    'orientation': 'portrait',
                    }
        pd.options.display.float_format = '{:,.2f}'.format

        for comp in self.company_id:
            host        = comp.server
            database    = comp.db_name
            user        = comp.db_usr
            password    = comp.db_pass 
            
            #conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';UID='+user+';PWD='+ password + ';TrustServerCertificate=yes')
            conn = pymssql.connect(host=host, user=user, password=password, database=database)
            msg_sql= "exec dbo.IGU_ACT_analysispiutang   '"+ self.datefrom.strftime("%Y%m%d")   + "','"+ self.dateto.strftime("%Y%m%d")   + "','" + comp.code_base  + "'"

            data = pandas.io.sql.read_sql(msg_sql,conn)
            listfinal.append(data)

        df = pd.concat(listfinal)
        #df.loc['Total'] = df.select_dtypes(pd.np.number).sum().reindex(df.columns, fill_value='')
        



        
        if self.export_to =="xls":
            filename = filenamexls 
            df.to_excel(mpath + '/temp/'+ filenamexls)  
        if self.export_to =="xlspivot":
            filename = filenamexls 
            df.to_excel(mpath + '/temp/'+ filenamexls)  


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

 