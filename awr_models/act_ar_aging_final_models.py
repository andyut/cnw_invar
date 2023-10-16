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
from jinja2 import Environment, FileSystemLoader
import pdfkit

class CNW_AR_AGING(models.TransientModel):
    _name           = "cnw.awr28.agingperdate"
    _description    = "cnw.agingperdate"
    company_id      = fields.Many2many('res.company', string="Company",required=True)
     
    dateto          = fields.Date ("Date To", default=fields.Date.today()) 
    filexls         = fields.Binary("File Output")    
    filenamexls     = fields.Char("File Name Output")
    
    export_to       = fields.Selection([ ('xls', 'Excel'),],string='Export To', default='xls')

    @api.multi
    def view_araging(self): 

#PATH & FILE NAME & FOLDER
        mpath       = get_module_path('cnw_awr28')
        filenamexls2    = 'aging_perdate_'+   self.dateto.strftime("%Y%m%d")  + '.xlsx'
        filenamepdf    = 'aging_perdate_'+   self.dateto.strftime("%Y%m%d")  + '.pdf'
        filepath    = mpath + '/temp/'+ filenamexls2

#LOGO CSS AND TITLE
        logo        = mpath + '/awr_template/logoigu.png' 
        cssfile     = mpath + '/awr_template/style.css'        
        options = {
                    'page-size': 'legal',
                    'orientation': 'landscape',
                    }
        igu_title = "Aging Receivable"
        igu_tanggal = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")
        igu_remarks = "Aging Receivable Per Date "                    

#MULTI COMPANY 

        listfinal = []
        pandas.options.display.float_format = '{:,.2f}'.format
        for comp in self.company_id:

            host        = comp.server
            database    = comp.db_name
            user        = comp.db_usr
            password    = comp.db_pass 
            
            #conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';UID='+user+';PWD='+ password + ';TrustServerCertificate=yes')
            conn = pymssql.connect(host=host, user=user, password=password, database=database)
            
            msgsql =  "exec [dbo].[IGU_ACT_AGING_FINAL] '" +  self.dateto.strftime("%Y%m%d") + "','"  + comp.code_base + "' " 
            data = pandas.io.sql.read_sql(msgsql,conn) 
            listfinal.append(data)
  
        


        df = pd.concat(listfinal)
        #data_ar = df.pivot_table(index=["Groups","AR"],columns=["Aging_period"],aggfunc=np.sum,  values=["Total"],fill_value="0",margins=True)
        #data_ar2 = df.pivot_table(index=["AR","Groups",],columns=["Aging_period"],aggfunc=np.sum,  values=["Total"],fill_value="0",margins=True)

        if self.export_to =="xls":
            filename = filenamexls2 
            #report = df.groupby(["Group","AR Person"]).sum()
            df.to_excel(mpath + '/temp/'+ filenamexls2,index=False) 
 
        
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

 