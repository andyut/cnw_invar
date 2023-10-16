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
    _name           = "cnw.awr28.araging"
    _description    = "cnw.araging"
    company_id      = fields.Many2many('res.company', string="Company",required=True)
     
    dateto          = fields.Date ("Date To", default=fields.Date.today())
    bp              = fields.Char("Business Partner",default="")
    filexls         = fields.Binary("File Output")    
    filenamexls     = fields.Char("File Name Output")
    
    export_to       = fields.Selection([ ('xls', 'Excel'),('pdf', 'PDF'),],string='Export To', default='pdf')

    @api.multi
    def view_araging(self): 

#PATH & FILE NAME & FOLDER
        mpath       = get_module_path('cnw_awr28')
        filenamexls2    = 'aging_'+   self.dateto.strftime("%Y%m%d")  + '.xlsx'
        filenamepdf    = 'aging_'+   self.dateto.strftime("%Y%m%d")  + '.pdf'
        filepath    = mpath + '/temp/'+ filenamexls2

#LOGO CSS AND TITLE
        logo        = mpath + '/awr_template/logoigu.png' 
        cssfile     = mpath + '/awr_template/style.css'        
        options = {
                    'orientation': 'landscape',
                    }
        igu_title = "Aging Receivable"
        igu_tanggal = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")
        igu_remarks = "Aging Receivable "                    

#MULTI COMPANY 

        listfinal = []
        pandas.options.display.float_format = '{:,.2f}'.format
        
        bp = self.bp if self.bp else ""
        
        for comp in self.company_id:

            host        = comp.server
            database    = comp.db_name
            user        = comp.db_usr
            password    = comp.db_pass 
            
            #conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';UID='+user+';PWD='+ password + ';TrustServerCertificate=yes')
            conn = pymssql.connect(host=host, user=user, password=password, database=database)
            
#            msgsql =  "exec [dbo].[IGU_ACT_AGINGDETAIL_SCHEDULER] '" +  self.dateto.strftime("%Y%m%d") + "','"  + comp.code_base + "' " 
            msgsql =  """
                            select  '""" + comp.code_base  + """' Company,
                                d.groupname 'Group',  
								c.cardcode  ,
								c.cardname 'Partner Name', 
								c.shiptodef , 
								sum(case 
										when datediff(day,a.refdate,getdate())<=30 and a.transtype in (13,14) then (a.BalScDeb -a.balsccred ) 
										else 0
								end) '0-30',  
								sum(case 
										when datediff(day,a.refdate,getdate()) between 31 and 60  and a.transtype in (13,14)  then (a.BalScDeb -a.balsccred ) 
										else 0
								end) '31-60',  
								sum(case 
										when datediff(day,a.refdate,getdate())  between 61 and 90  and a.transtype in (13,14)  then (a.BalScDeb -a.balsccred ) 
										else 0
								end) '61-90',  
								sum(case 
										when datediff(day,a.refdate,getdate())  between 91 and 120    and a.transtype in (13,14)  then (a.BalScDeb -a.balsccred ) 
										else 0
								end) '91-120',  
								sum(case 
										when datediff(day,a.refdate,getdate()) >=121 and a.transtype in (13,14)  then (a.BalScDeb -a.balsccred ) 
										else 0
								end) '121+',
								sum(a.BalScDeb -a.balsccred ) 'Total'
						from jdt1 a 
						inner join ojdt b on a.transid = b.transid 
						inner join ocrd c on a.ShortName = c.cardcode 
						inner join ocrg d on d.groupcode = c.groupcode 
						where 
								a.account ='1130001' 
								and a.BalScDeb -a.balsccred  <>0 
								and convert(varchar,a.refdate,112)<= '""" + self.dateto.strftime("%Y%m%d") + """'
                                and c.cardcode + c.cardname + isnull(c.shiptodef,'') like '%' +'""" + self.bp + """' 
						group by  
								c.cardcode ,
								d.groupname ,
								c.cardname ,
								c.shiptodef     """
            data = pandas.io.sql.read_sql(msgsql,conn) 
            listfinal.append(data)
  
        


        df = pd.concat(listfinal)

        if self.export_to =="xls":
            filename = filenamexls2 
            #report = df.groupby(["Group","AR Person"]).sum()
            df.to_excel(mpath + '/temp/'+ filenamexls2,index=False) 

        if self.export_to =="pdf":
            filename = filenamepdf
            
            datalist = df.values.tolist()
            
            i30 = 0
            i60 = 0
            i90 = 0
            i120 = 0
            i121 = 0
            itotal = 0
            
            for dl  in datalist:
                i30 += dl[4]
                i60 += dl[5]
                i90 += dl[6]
                i120 += dl[7]
                i121 += dl[8]
                itotal += dl[9]
            
            env = Environment(loader=FileSystemLoader(mpath + '/template/'))
            template = env.get_template("aging_template.html")            
            template_var = {"logo":logo,
                            "igu_title" :igu_title,
                            "datetime" :igu_tanggal ,
                            "dateto" :self.dateto.strftime("%Y-%m-%d") ,
                            "igu_remarks" :igu_remarks ,
                            "data":datalist,
                            "i30":i30 ,
                            "i60":i60 ,
                            "i90":i90 ,
                            "i120":i120 ,
                            "i121":i121 ,
                            "itotal":itotal}
            
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

 