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

class CNW_fixedassetREPORT(models.TransientModel):
    _name           = "cnw.awr28.fixedasset"
    _description    = "cnw.awr28.fixedasset"
    company_id      = fields.Many2many('res.company', string="Company",required=True)
     
    dateto          = fields.Date ("Date To", default=fields.Date.today())  
    export_to       = fields.Selection([ ('xls', 'Excel')],string='Export To', default='xls')
    filexls         = fields.Binary("File Output")    
    filenamexls     = fields.Char("File Name Output")
    
    @api.multi
    def view_awr28_fixedasset(self): 
        mpath       = get_module_path('cnw_awr28')
        filenamexls = 'fixedasset_'+   self.dateto.strftime("%Y%m%d")  + '.xlsx'
        filenamepdf = 'fixedasset_'+   self.dateto.strftime("%Y%m%d")  + '.pdf'
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

        for comp in self.company_id:
            host        = comp.server
            database    = comp.db_name
            user        = comp.db_usr
            password    = comp.db_pass 
            
            #conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';UID='+user+';PWD='+ password + ';TrustServerCertificate=yes')
            conn = pymssql.connect(host=host, user=user, password=password, database=database)
            msg_sql= """ 
                            declare @dateto varchar(10)  
                            declare @before varchar(10) ,@after varchar(10) 
                            set @dateto = '""" + self.dateto.strftime("%Y%m%d") + """'
                            select @after = year(dateadd(year,1,convert(date , @dateto) ))
                            select @before = year(convert(date , @dateto))
                            select  '""" + comp.code_base + """' Company, 
                                    a.itemcode , 
                                    a.itemname ,
                                    @before periode,
                                    d.name assetCategory,
                                    convert(varchar,a.capdate,23) capdate,
                                    case left(convert(varchar,a.capdate,112),4) when @before then e.apc else  b.apc end                'Harga Perolehan' ,
                                    b.orDpAcc           'Akm. Penyusutan Th Lalu',        
                                    b.apc- b.orDpAcc    'Nilai Buku Th Lalu',        
                                    c.orddpramt         'Penyusutan Th. Berjalan',  
                                    case left(convert(varchar,a.capdate,112),4) when @before then  e.apc else 0 end 'Tambahan',    
                                    b.orDpAcc +  c.orddpramt   'Akm. Penyusutan Th. Berjalan',      
                                    case  when left(convert(varchar,a.capdate,112),4)  = @before  then  e.apc - b.orDpAcc -  c.orddpramt 
                                            else   b.apc - b.orDpAcc -  c.orddpramt 
                                    end 'Nilai Buku Th. Berjalan' 
                            from OITM A
                            LEFT OUTER join itm8 b on a.itemcode = b.itemcode  and b.DprArea = 'Main Area' and periodcat =  @before  
                            inner join (select  code , name from OACS) d on a.assetclass = d.code
                            LEFT OUTER join 
                            (   select itemcode,periodcat, sum(OrdDprAmt)OrdDprAmt From DRN2 a 
                                    inner join odrn b on a.docentry = b.docentry 
                                where    b.dprarea ='Main Area' and periodcat =  @before AND b.canceled='N'
                            group by itemcode,periodcat
                            )c on a.itemcode = c.itemcode and b.PeriodCat= c.PeriodCat 
                            left outer join 
                                    (
                                        SELECT 
                                                "ItemCode", SUM(T0.APC) AS "APC"
                                        FROM "FIX1" T0
                                        WHERE 
                                            t0."TransType" = '110'
                                            and t0.DprArea='Main Area'  and year(t0.refdate)= @before
                                    GROUP BY "ItemCode")as  e on a.itemcode = e.itemcode 
                        """
            #msg_sql= "exec IGU_ACCT_fixedasset   '"+ self.datefrom.strftime("%Y%m%d")   + "','" + self.dateto.strftime("%Y%m%d")  + "','"+ self.account + "','" + comp.code_base + "'"


            data = pandas.io.sql.read_sql(msg_sql,conn)
            listfinal.append(data)

        df = pd.concat(listfinal)
 



        
        if self.export_to =="xls":
            filename = filenamexls 
            #df["Balance"] = df["AMOUNT"].cumsum()
            df.to_excel(mpath + '/temp/'+ filenamexls)  
        else:
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

 