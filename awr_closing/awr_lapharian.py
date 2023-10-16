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


class AWR_lapharian(models.TransientModel):
    _name           = "cnw.awr28.lapharian"
    _description    = "cnw.awr28.lapharian"
    company_id      = fields.Many2many('res.company', string="Company",required=True)
    dateto          = fields.Date ("Date To", default=fields.Date.today()) 
    export_to       = fields.Selection([ ('xls', 'Excel'),('xlspivot','Excel Pivot'),('pdf', 'PDF'),('aging','Aging')],string='Export To', default='xls')
    filexls         = fields.Binary("File Output")    
    filenamexls     = fields.Char("File Name Output")
    
    
    
    def view_lap(self): 
        mpath       = get_module_path('cnw_awr28')
        filename    = 'lapharian_'+ self.env.user.company_id.db_name +  self.dateto.strftime("%Y%m%d")  + '.xlsx'
        filenamexls    = 'lapharian_'+ self.env.user.company_id.db_name +   self.dateto.strftime("%Y%m%d")  + '.xlsx'
        filenamexls2    = 'lapharian_'+  self.env.user.company_id.db_name +  self.dateto.strftime("%Y%m%d")  + '.xlsx'
        filenamepdf = 'lapharian_'+  self.env.user.company_id.db_name +  self.dateto.strftime("%Y%m%d")  + '.pdf'
        filepath    = mpath + '/temp/'+ filename
        logo        = mpath + '/awr_template/logoigu.png' 
        listfinal   = []
        options = {
                    'orientation': 'portrait',
                    }        
        igu_tanggal = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")
        
        for comp in self.company_id:

            host        = comp.server
            database    = comp.db_name
            user        = comp.db_usr
            password    = comp.db_pass 
            
            #conn = pymssql.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';UID='+user+';PWD='+ password + ';TrustServerCertificate=yes')
            conn = pymssql.connect(host=host, user=user, password=password, database=database)
            cursor = conn.cursor()
            if self.export_to =="aging":
                msg_sql=  """
                                    select  case   when upper(d.groupname) like '%CABANG%' then 'IGU' 
                                                        when upper(d.groupname) like '%GROUP%' then 'IGU' 
                                                        when upper(d.groupname) like '%TANI%' then 'IGU' 
                                                        when upper(d.groupname) like '%MANUFACTURE%' then 'WET'
                                                        when upper(d.groupname) like '%DISTRIBUTOR%' then 'WET'
                                                        when upper(d.groupname) like '%UMUM%' then 'UMUM/OTHER'
                                                        when upper(d.groupname) like '%FC%' then 'INTERNAL /FC'
                                                        when upper(d.groupname) like '%HOTEL%' then 'HOREKA' 
                                                        when upper(d.groupname) like '%RESTAUR%' then 'HOREKA' 
                                                        when upper(d.groupname) like '%CATERING%' then 'HOREKA' 
                                                        when upper(d.groupname) like '%PASTRY%' then 'PASTRY' 
                                                        when upper(d.groupname) like '%QSR%' then 'HOREKA' 
                                                        when upper(d.groupname) like '%COFFEE%' then 'HOREKA' 
                                                        when upper(d.groupname) like '%KARYAWAN%' then 'INTERNAL'  
                                                        when upper(d.groupname) like '%ECOMMERCE%' then 'RETAIL'  
                                                        when upper(d.groupname) like '%SUPERMARKET%' then 'RETAIL'  
                                            else 
                                                        d.GroupName
                                            end                  igroup,

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
                                            end) '121+ ',

                                            sum(a.BalScDeb -a.balsccred ) 'Total'
                                    from jdt1 a 
                                    inner join ojdt b on a.transid = b.transid 
                                    inner join ocrd c on a.ShortName = c.cardcode 
                                    inner join ocrg d on d.groupcode = c.groupcode 

                                    where 
                                            a.account ='1130001' 
                                            and a.BalScDeb -a.balsccred  <>0 
                                            and convert(varchar,a.refdate,112)<= '""" +  self.dateto.strftime("%Y%m%d") + """'
                                    group by  
                                            case   when upper(d.groupname) like '%CABANG%' then 'IGU' 
                                                        when upper(d.groupname) like '%GROUP%' then 'IGU' 
                                                        when upper(d.groupname) like '%TANI%' then 'IGU' 
                                                        when upper(d.groupname) like '%MANUFACTURE%' then 'WET'
                                                        when upper(d.groupname) like '%DISTRIBUTOR%' then 'WET'
                                                        when upper(d.groupname) like '%UMUM%' then 'UMUM/OTHER'
                                                        when upper(d.groupname) like '%FC%' then 'INTERNAL /FC'
                                                        when upper(d.groupname) like '%HOTEL%' then 'HOREKA' 
                                                        when upper(d.groupname) like '%RESTAUR%' then 'HOREKA' 
                                                        when upper(d.groupname) like '%CATERING%' then 'HOREKA' 
                                                        when upper(d.groupname) like '%PASTRY%' then 'PASTRY' 
                                                        when upper(d.groupname) like '%QSR%' then 'HOREKA' 
                                                        when upper(d.groupname) like '%COFFEE%' then 'HOREKA' 
                                                        when upper(d.groupname) like '%KARYAWAN%' then 'INTERNAL'  
                                                        when upper(d.groupname) like '%ECOMMERCE%' then 'RETAIL'  
                                                        when upper(d.groupname) like '%SUPERMARKET%' then 'RETAIL'  
                                            else 
                                                        d.GroupName
                                            end                 
                """
            else:
                msg_sql=  "exec [dbo].[IGU_ACT_LAPHARIAN] '" +  self.dateto.strftime("%Y%m%d") + "','"+ comp.code_base + "' "

            data = pandas.io.sql.read_sql(msg_sql,conn)
            listfinal.append(data)

 

        df = pd.concat(listfinal)
        dflist = df.values.tolist() 

        if self.export_to =="xls":
            filename = filenamexls2 
            #report = df.groupby(["Group","AR Person"]).sum()
            df.to_excel(mpath + '/temp/'+ filenamexls2,index=False)

        if self.export_to =="xlspivot":
            filename = filenamexls2 
            #report = df.groupby(["Group","AR Person"]).sum()
            rpt = df.pivot_table(index=["itype","description"],columns=["icompany"],aggfunc=np.sum,  values=["amount"],fill_value="0",margins=True )
            rpt.to_excel(mpath + '/temp/'+ filenamexls2)
            #df.to_excel(mpath + '/temp/'+ filenamexls2,index=False)

        if self.export_to =="aging":
            filename = filenamexls2  
            df.to_excel(mpath + '/temp/'+ filenamexls2,index=False)
            #df.to_excel(mpath + '/temp/'+ filenamexls2,index=False)            
        if self.export_to =="pdf":
            filename = filenamepdf
            
            env = Environment(loader=FileSystemLoader(mpath + '/template/'))
            template = env.get_template("lapharian_template.html")            
            print(dflist)
            template_var = {"company":self.env.user.company_id.name,
                            "igu_title" :"HPP Global",
                            "datetime" :igu_tanggal ,
                            "dateto" :self.dateto.strftime("%Y-%m-%d") ,
                            "igu_remarks" :"HPP Global" ,
                            "data":dflist}
            
            html_out = template.render(template_var)
            pdfkit.from_string(html_out,mpath + '/temp/'+ filenamepdf,options=options) 
            
            
             
             
               
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

 