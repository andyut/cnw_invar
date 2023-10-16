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


class AWR_InterCompAR(models.TransientModel):
    _name           = "cnw.intercomp.ar"
    _description    = "cnw.intercomp.ar"
    company_id      = fields.Many2many('res.company', string="Company",required=True) 
    dateto          = fields.Date ("Date To", default=fields.Date.today()) 
    export_to       = fields.Selection([ ('xls', 'Excel'),('pdf', 'PDF'),],string='Export To', default='xls')
    filexls         = fields.Binary("File Output")    
    filenamexls     = fields.Char("File Name Output")
    
    
    
    def view_pl(self): 
        mpath       = get_module_path('cnw_awr28')
        filename    = 'AR'+ self.env.user.company_id.db_name +  self.dateto.strftime("%Y%m%d")  + '.xlsx'
        filenamexls    = 'AR'+ self.env.user.company_id.db_name +   self.dateto.strftime("%Y%m%d")  + '.xlsx'
        filenamexls2    = 'AR'+  self.env.user.company_id.db_name +  self.dateto.strftime("%Y%m%d")  + '.xlsx'
        filenamepdf = 'AR'+  self.env.user.company_id.db_name +  self.dateto.strftime("%Y%m%d")  + '.pdf'
        filepath    = mpath + '/temp/'+ filename
        logo        = mpath + '/awr_template/logoigu.png' 
        listfinal   = []
        options = {
                    'orientation': 'portrait',
                    }        
        igu_tanggal = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")
        
        datacompany = (
                        {'codename':'01-IGU','npwp':'013605910007000', 'company':'INDOGUNA UTAMA','Active':True,'host': '192.168.1.13',	'db_name':'IGU_LIVE',	'user':'sa','password':'B1admin'},
                        {'codename':'02-CCKI','npwp':'210208617407000', 'company':'CAHAYA KARYA INDAH','Active':True,'host': '192.168.1.13',	'db_name':'PTCKI',	'user':'sa','password':'B1admin'},
                        {'codename':'03-CSCA','npwp':'210208708407000', 'company':'SURYA CEMERLANG ABADI','Active':True,'host': '192.168.1.13',	'db_name':'PTSCA',	'user':'sa','password':'B1admin'},
                        {'codename':'04-IMS','npwp':'318081007451000', 'company':'INDO MANDIRI SEJAHTERA','Active':True,'host': '192.168.1.13',	'db_name':'PTIMS',	'user':'sa','password':'B1admin'},
                        {'codename':'05-BWN','npwp':'823080627451000', 'company':'BOGA WISESA NUSANTARA','Active':True,'host': '192.168.1.13',	'db_name':'PTBWU',	'user':'sa','password':'B1admin'},
                        {'codename':'07-STU','npwp':'312929961028000', 'company':'SINAR TERANG UTAMA','Active':True,'host': '192.168.1.13',	'db_name':'PTSTU',	'user':'sa','password':'B1admin'},
                        {'codename':'06-NGU','npwp':'312928997028000', 'company':'NUANSA GUNA UTAMA','Active':False,'host': '192.168.1.27',	'db_name':'ANU01',	'user':'trade','password':'password#01'},
                        {'codename':'04-ISU','npwp':'805147816447000', 'company':'INDOKULINA SARANA UTAMA','Active':True,'host': '192.168.6.20',	'db_name':'Live_Indokulina',	'user':'sa','password':'password#01'},
                        {'codename':'08-SKI','npwp':'017705872028000', 'company':'SARANA KULINA INTI SEJAHTERA','Active':False,'host': '192.168.9.15',	'db_name':'SR2020',	'user':'trade','password':'trade'},
                        {'codename':'10-BLKU','npwp':'017997099904000', 'company':'BALI KULINA','Active':True,'host': '192.168.6.20',	'db_name':'Live_Bali_Kulina',	'user':'sa','password':'password#01'},
                        {'codename':'11-BDKU','npwp':'211154307429000', 'company':'BANDUNG KULINA','Active':True,'host': '192.168.6.20',	'db_name':'Live_Bandung_Kulina_Utama',	'user':'sa','password':'password#01'},
                        {'codename':'12-MSKU','npwp':'030516868801000', 'company':'MAKASSAR KULINA','Active':True,'host': '192.168.6.20',	'db_name':'Live_Makasar_Kulina_Utama',	'user':'sa','password':'password#01'},
                        {'codename':'15-PKU','npwp':'848784252307000', 'company':'PALEMBANG KULINA UTAMA','Active':True,'host': '192.168.6.20',	'db_name':'Live_Palembang_Kulina_Utama',	'user':'sa','password':'password#01'},
                        {'codename':'13-JKU','npwp':'025422445541000', 'company':'JOGJA KULINA UTAMA','Active':True,'host': '192.168.6.20',	'db_name':'Live_Jogja_Kulina_Utama',	'user':'sa','password':'password#01'},
                        {'codename':'14-BPKU','npwp':'727152142721000', 'company':'BALIKPAPAN KULINA UTAMA','Active':True,'host': '192.168.6.20',	'db_name':'Live_Jogja_Kulina_Utama',	'user':'sa','password':'password#01'},
                        {'codename':'09-SIL','npwp':'020097440604000', 'company':'SARANA IND LESTARI','Active':True,'host': '192.168.6.20',	'db_name':'Live_Sarana_Indoguna_Lestari',	'user':'sa','password':'password#01'},
                        {'codename':'16-SKU','npwp':'844230656503000', 'company':'SEMARANG KULINA UTAMA','Active':True,'host': '192.168.6.20',	'db_name':'Live_Semarang_Kulina_Utama',	'user':'sa','password':'password#01'},
                        {'codename':'17-PANAL','npwp':'019549401325000', 'company':'PANEN AGRO LESTARI','Active':False,'host': '',	'db_name':'',	'user':'sa','password':''},
                        {'codename':'18-PTI','npwp':'954940862008000', 'company':'CV PASAR TANI','Active':True,'host': '192.168.1.13',	'db_name':'CVPASARTANI',	'user':'sa','password':'B1admin'},
                        )
                        
        datalist=[]
        listcom = []
        print()
        i=0
        mybp=""
        for company in datacompany:
            if i==0 :
                mybp = mybp + "'" + company["npwp"]+ "'"  
            else :
                mybp = mybp +  ",'" + company["npwp"] + "'"
            i+=1

        for company in datacompany:
            
            msg_sql=  """select  '""" + company["company"] + """' Company , '""" + company["codename"] + """' CompCode,
                        b.lictradnum npwp, 
                        sum(a.debit - a.credit )amount from JDT1 A 
                            inner join OCRD B ON A.shortname = b.cardcode
                            WHERE CONVERT(VARCHAR,A.REFDATE,112)<= '""" +  self.dateto.strftime("%Y%m%d") + """'
                            AND A.Account ='1130001'
                            and b.lictradnum in (""" + mybp + """ )
                        group by b.lictradNum
                        """
            #print(msg_sql)
            if company["Active"]==True:
                listcom.append(company["db_name"])
                #print(company["db_name"])
                conn = pymssql.connect(host=company["host"] , user=company["user"] , password=company["password"], database=company["db_name"] )
                cursor = conn.cursor()     
                data = pandas.io.sql.read_sql(msg_sql,conn)
                datalist.append(data)
                #print(type(datacompany))

        df = pd.concat(datalist)  
        df2 = pd.DataFrame(datacompany)

        new_df = pandas.merge(df, df2, how = 'left', on=["npwp"])



        if self.export_to =="xls":
            filename = filenamexls2 
            report = new_df.pivot_table(index=["codename"],columns=["CompCode"],aggfunc=np.sum,  values=["amount"],fill_value=0,margins=True )
            report.to_excel(mpath + '/temp/'+ filenamexls2)
             
            
            
             
             
               
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

 