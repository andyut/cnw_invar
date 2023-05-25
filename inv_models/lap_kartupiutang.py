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




class CNWKartuPiutang(models.TransientModel):
    _name           = "cnw.invar.kartupiutang"
    _description    = "Kartu Piutang"
    company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)

    dateto          = fields.Date("Date To",default=lambda s:fields.Date.today())
    customer        = fields.Char("Business Partner",default="")
    filexls         = fields.Binary("File Output")    
    filenamexls     = fields.Char("File Name Output")
    
    export_to       = fields.Selection([ ('xls', 'Excel'),('pdf', 'PDF'),],string='Export To', default='pdf')

    def get_saldopiutangdetail(self):

#PATH & FILE NAME & FOLDER
        mpath       = get_module_path('cnw_invar')
        filenamexls2    = 'SaldoPiutangDetail_'+   self.dateto.strftime("%Y%m%d")  + '.xlsx'
        filenamepdf    = 'SaldoPiutangDetail_'+   self.dateto.strftime("%Y%m%d")  + '.pdf'
        filepath    = mpath + '/temp/'+ filenamexls2

#LOGO CSS AND TITLE
        logo        = mpath + '/template/logoigu.png' 
        cssfile     = mpath + '/template/style.css'        
        options = {
                    'page-size': 'A4',
                    'orientation': 'landscape',
                    }
        igu_title = "Piutang Detail"
        igu_tanggal = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")
        igu_remarks = "Piutang Detail Per Tanggal " + self.dateto.strftime("%Y-%m-%d")                    

#MULTI COMPANY 

        listfinal = []
        pandas.options.display.float_format = '{:,.2f}'.format
        for comp in self.company_id:

            host        = comp.server
            database    = comp.db_name
            user        = comp.db_usr
            password    = comp.db_pass 
            
            conn = pymssql.connect(host=host, user=user, password=password, database=database)
            
            bp = self.customer if self.customer else ""

            msgsql =  "exec [dbo].[IGU_ACT_SALDOPIUTANGDETAIL] '" +  self.dateto.strftime("%Y%m%d") + "','" + bp + "','"  + comp.code_base + "' " 
            data = pandas.io.sql.read_sql(msgsql,conn) 
            listfinal.append(data)
  
        


        df = pd.concat(listfinal) 

        if self.export_to =="xls":
            filename = filenamexls2 
            #report = df.groupby(["Group","AR Person"]).sum()
            df.to_excel(mpath + '/temp/'+ filenamexls2,index=False,engine='xlsxwriter') 
        else:
                   
            filename = filenamepdf
            env = Environment(loader=FileSystemLoader(mpath + '/template/'))
            template = env.get_template("saldopiutangDetail_Template.html")            
            template_var = {"logo":logo,
                            "igu_title" :igu_title,
                            "igu_tanggal" :igu_tanggal ,
                            "igu_remarks" :igu_remarks ,
                            "detail": df.to_html(float_format='{:20,.2f}'.format,index=False)}
            
            html_out = template.render(template_var)
            pdfkit.from_string(html_out,mpath + '/temp/'+ filenamepdf,options=options,css=cssfile) 
     
        
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

 