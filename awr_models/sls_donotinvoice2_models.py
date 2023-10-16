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

class CNW_donotinvoice2REPORT(models.TransientModel):
    _name           = "cnw.awr28.donotinvoice2"
    _description    = "cnw.awr28.donotinvoice2"
    company_id      = fields.Many2many('res.company', string="Company",required=True)
     
    dateto          = fields.Date ("Date To", default=fields.Date.today()) 
    export_to       = fields.Selection([ ('xls', 'Excel'),('pdf', 'PDF'),],string='Export To', default='pdf')
    filexls         = fields.Binary("File Output")    
    filenamexls     = fields.Char("File Name Output")
    
    @api.multi
    def view_awr28_donotinvoice(self): 
        mpath       = get_module_path('cnw_awr28')
        filenamexls = 'notinvoice_'+   self.dateto.strftime("%Y%m%d")  + '.xlsx'
        filenamepdf = 'notinvoice_'+   self.dateto.strftime("%Y%m%d")  + '.pdf'
        filename    =""
        filepath    = mpath + '/temp/'
        logo        = mpath + '/awr_template/logoigu.png'
        listfinal   = []
        cssfile     = mpath + '/awr_template/style.css'

        #global Var

        igu_title = "Belum Jadi invoice"
        igu_tanggal = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")
        igu_remarks = "Belum Jadi invoice Per Tanggal "
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
            msg_sql= "exec dbo.IGU_ACT_DONOTINVOICE   '"+ self.dateto.strftime("%Y%m%d")   + "','" + comp.code_base  + "'"

            data = pandas.io.sql.read_sql(msg_sql,conn)
            listfinal.append(data)

        df = pd.concat(listfinal)

        msg_sql2= """
                    select  a.s_canceled , 
                            a.numatcard , 
                            to_char(a.docdate,'yyyyMMdd') ,
                            a.ord_no ,
                            a.cardcode ,
                            a.cardname ,
                            a.shiptocode ,
                            to_char(a.sap_createdate,'yyyyMMdd') createdate , 
                            a.doctime ,
                            case a.posisi 
                            when 'who' then 'Process in Wh Admin'
                            when 'whi' then 'deliver To Accounting'
                            when 'acin' then 'Process in Accounting'
                            end as status,
                            a.shiptocode,
                            a.remarks,
                            a.status,
                            coalesce(a.notes,'') notes,
                            a.state done_status,
                            a.notes_log ,
                            a.date_release tgl_naik,
                            a.customer_group ,
                            a.salesperson ,
                            a.salesgroup ,
                            a.cancel_reason

                    from sp_do_list a  where a.ord_no in ('""" + "','".join(data["SO Number"].tolist()) + """')
                """        

        df.loc['Total'] = df.select_dtypes(pd.np.number).sum().reindex(df.columns, fill_value='')
        



        
        if self.export_to =="xls":
            filename = filenamexls 
            df.to_excel(mpath + '/temp/'+ filenamexls)  
        else:
            # JINJA 2 Template
            filename = filenamepdf
            env = Environment(loader=FileSystemLoader(mpath + '/awr_template/'))
            template = env.get_template("awr_template_report.html")            
            template_var = {"logo":logo,
                            "igu_title" :igu_title,
                            "igu_tanggal" :igu_tanggal ,
                            "igu_remarks" :igu_remarks ,
                            "detail": df.to_html(index=True,float_format='{:20,.2f}'.format)}
            
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
 
#        conn.close()    

 