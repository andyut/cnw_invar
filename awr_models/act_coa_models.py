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


class SAP_AWR28_JASPER(models.Model):
	_name           = "cnw.awr28.jasper"
	_description    = "cnw.awr28.jasper"	
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
	name            = fields.Char("Code Name" ,required=True)
	descr           = fields.Char("Description")
	filejasper		= fields.Binary("Jasper JRXML",required=True)    
	jaspername		= fields.Char("Jasper File Name")
        
class CNW_COAMASTER(models.TransientModel):
    _name           = "cnw.awr28.coamaster"
    _description    = "cnw.awr28.coamaster"
    company_id      = fields.Many2many('res.company', string="Company",required=True)
     
     
    export_to       = fields.Selection([ ('xls', 'Excel')],string='Export To', default='xls')
    filexls         = fields.Binary("File Output")    
    filenamexls     = fields.Char("File Name Output")
    
    @api.multi
    def view_awr28_coamaster(self): 
        mpath       = get_module_path('cnw_awr28')
        filenamexls = 'coa_'+     datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y_%m_%d_%H_%M_%S")  + '.xlsx'
        filenamepdf = 'coa_'+    datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y_%m_%d_%H_%M_%S")   + '.pdf'
        filename    =""
        filepath    = mpath + '/temp/'
        logo        = mpath + '/awr_template/logoigu.png'
        listfinal   = []
        cssfile     = mpath + '/awr_template/style.css'

        #global Var

        igu_title = "Fixed Asset"
        igu_tanggal = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")
        igu_remarks = "Fixed Asset "
        options = {
                    'page-size': 'A4',
                    'orientation': 'landscape',
                    }
        listfinal   = []
        for comp in self.company_id:
            host        = comp.server
            database    = comp.db_name
            user        = comp.db_usr
            password    = comp.db_pass 
            
            #conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';UID='+user+';PWD='+ password + ';TrustServerCertificate=yes')
            conn = pymssql.connect(host=host, user=user, password=password, database=database)
            msg_sql= """ 
                            select 
                                a.AcctCode ,
                                a.acctname , 
                                a.LocManTran ControlAccount,
                                a.FatherNum ,
                                b.AcctCode + '-' + b.acctName  header3,
                                c.AcctCode + '-' + c.acctName  header2,
                                d.acctName  header1
                           from oact a
                                left outer join oact b on left(a.AcctCode,4) = b.AcctCode 
                                left outer join oact c on left(a.AcctCode,2) = c.AcctCode 
                                left outer join oact d on (c.FatherNum) = d.AcctCode
                                where len(a.acctCode)>=7 and len(a.acctCode)<=12

                        """
            

            data = pandas.io.sql.read_sql(msg_sql,conn)
            listfinal.append(data)

        df = pd.concat(listfinal)
 



 
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

 