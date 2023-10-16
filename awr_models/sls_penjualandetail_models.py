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
from jinja2 import Environment, FileSystemLoader
import pymssql
import pdfkit

class CNW_penjualandetail(models.TransientModel):
    _name           = "cnw.awr28.penjualandetail"
    _description    = "cnw.penjualandetail"
    company_id      = fields.Many2many('res.company', string="Company",required=True)
    
    datefrom        = fields.Date ("Date From", default=fields.Date.today())
    dateto          = fields.Date ("Date To", default=fields.Date.today()) 
    customer        = fields.Char("Customer",default=" ")
    export_to       = fields.Selection([ ('xls', 'Excel'),('pdf', 'PDF'),],string='Export To', default='pdf')
    filexls         = fields.Binary("File Output",default=" ")    
    filenamexls     = fields.Char("File Name Output",default="EmptyText.txt")
	  
    def view_penjualandetail(self): 
        mpath       = get_module_path('cnw_awr28')
        filenamexls = 'penjualan_'+   self.dateto.strftime("%Y%m%d")  + '.xlsx'
        filenamepdf = 'penjualan_'+   self.dateto.strftime("%Y%m%d")  + '.pdf'
        filex = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y%m%d%H%M%S") 
        filejson    = "Penjualan_" + filex+ ".json"
        fileoutput  = "Penjualan_" + filex + ".pdf"
        filename    =""
        filepath    = mpath + '/temp/'
        logo        = mpath + '/awr_template/logoigu.png'
        listfinal   = []

        pd.options.display.float_format = '{:,.2f}'.format

        for comp in self.company_id:
            host        = comp.server
            database    = comp.db_name
            user        = comp.db_usr
            password    = comp.db_pass 
            
            #conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';UID='+user+';PWD='+ password + ';TrustServerCertificate=yes')
            conn = pymssql.connect(host=host, user=user, password=password, database=database)
            msg_sql1 = """
                            declare @company varchar(50) , @datefrom varchar(10), @dateto varchar(10)
                            set @datefrom = '"""+  self.datefrom.strftime("%Y%m%d") +"""' 
                            set @dateto = '"""+  self.dateto.strftime("%Y%m%d") +"""' 
                            set @company = '""" + comp.name + """' 

                            select  @company Company,
                            @datefrom   Datefrom, @dateto Dateto,
                            NumAtCard ,
                                    docdate ,
                                    customer, 
                                    U_IDU_FPajak ,
                                    Amount,
                                    discount, 
                                    tax ,
                                    doctotal 
                            from 
                            (
                            select 
                                    isnull(a.NumAtCard,a.docnum) NumAtCard ,
                                    convert(varchar,a.docdate,23) docdate ,
                                    '[' + b.cardcode + '] '+ b.cardname customer, 
                                    a.U_IDU_FPajak ,
                                    a.doctotal - a.vatsum + a.DiscSum Amount,
                                    a.DiscSum discount, 
                                    a.vatsum Tax ,
                                    a.doctotal 

                            from oinv a 
                            inner join ocrd b on a.CardCode = b.cardcode 
                            where a.CANCELED ='N'
                            and convert(varchar, a.docdate ,112 ) between @datefrom  and @dateto
                            union all
                            select 
                                    isnull(a.NumAtCard,a.docnum) ,
                                    convert(varchar,a.docdate,23) docdate ,
                                    '[' + b.cardcode + '] '+ b.cardname customer, 
                                    a.U_IDU_FPajak ,
                                    -1 * (a.doctotal - a.vatsum + a.DiscSum) Amount,
                                    -1 * a.DiscSum discount, 
                                    -1 * a.vatsum Tax ,
                                    -1 * a.doctotal 

                            from orin a 
                            inner join ocrd b on a.CardCode = b.cardcode 
                            where a.CANCELED ='N'
                            and convert(varchar, a.docdate ,112 ) between @datefrom  and @dateto
                            )
                            as a 
                            order by docdate ,
                                    customer ,
                                    NumAtCard            
            """
            msg_sql2= "exec  [dbo].[IGU_SLS_PENJUALANDETAIL]   '"+ self.datefrom.strftime("%Y%m%d")   + "','"+ self.dateto.strftime("%Y%m%d")   + "','','" + comp.code_base  + "'"
            
            if self.export_to =="pdf":
                msg_sql = msg_sql1 
            else :
                msg_sql = msg_sql2

            data = pandas.io.sql.read_sql(msg_sql,conn)
            listfinal.append(data)

        df = pd.concat(listfinal)

        if self.export_to =="xls":
            filename = filenamexls 
            df.loc['Total'] = df.select_dtypes(pd.np.number).sum().reindex(df.columns, fill_value='')
            df.to_excel(mpath + '/temp/'+ filenamexls)  
        else:
## JASPER REPORT
            input_file 		= mpath + '/jasper/lapjual.jrxml'
            data_file 		= mpath + '/temp/' +  filejson
            output_file 	= mpath + '/temp/' +  fileoutput
            filename 		= fileoutput


            jasperwapi = self.company_id.webapi
## JSON FILE 			
			
            jsondata = df.to_json(orient="records" )
            print(jsondata)
                # "outputfile" :  mpath + '/temp/' +  filename ,
            with open(data_file,'w+') as f:
                f.write(jsondata)
            #f.close()
            appSession 	= requests.Session()
            payload = { "inputfile" :input_file,
                        "outputfile" :  mpath + '/temp/'+ fileoutput   ,
                        "datafile" :  mpath + '/temp/' + filejson ,
                        "extension" :  "pdf"
                }
            url = jasperwapi + "report"
            print(payload)
            response = appSession.post(url, json=payload,verify=False)
            print(response.text)
## END JASPER REPORT        


       # SAVE TO MODEL.BINARY 
        file = open(mpath + '/temp/'+ filename , 'rb')
        out = file.read()
        file.close()
        self.filexls =base64.b64encode(out)
        self.filenamexls = filename 
        if self.export_to !="pdf":
            return {
                'name': 'Report',
                'type': 'ir.actions.act_url',
                'url': "web/content/?model=" + self._name +"&id=" + str(
                    self.id) + "&filename_field=filenamexls&field=filexls&download=true&filename=" + self.filenamexls,
                'target': 'new',
                }
        else :
            return {
                'type': 'ir.actions.do_nothing'
                }
		        
         
