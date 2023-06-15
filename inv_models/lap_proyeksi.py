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




class CNWProyeksi(models.TransientModel):
    _name           = "cnw.invar.proyeksi"
    _description    = "Lap Tukar Faktur BK"
    company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)

    datefrom        = fields.Date("Date from",default=lambda s:fields.Date.today())
    dateto          = fields.Date("Date To",default=lambda s:fields.Date.today())
    arperson        = fields.Char("AR Person ",default="")
    customer        = fields.Char("customer",default="")
    filexls         = fields.Binary("File Output")    
    filenamexls     = fields.Char("File Name Output")
    
    based_on       = fields.Selection([ ('tftop', 'TF') ,  ('tf', 'DueDate') ,  ],string='Based On', default='tftop')
    export_to       = fields.Selection([ ('xls', 'Excel') ,  ],string='Export To', default='xls')

    def getproyeksi(self):

#PATH & FILE NAME & FOLDER
        mpath       = get_module_path('cnw_invar')
        filenamexls2    = 'Proyeksi_'+   self.dateto.strftime("%Y%m%d")  + '.xlsx'
        filenamepdf    = 'Proyeksi_'+   self.dateto.strftime("%Y%m%d")  + '.pdf'
        filepath    = mpath + '/temp/'+ filenamexls2

 
#MULTI COMPANY 

        listfinal = []
        pandas.options.display.float_format = '{:,.2f}'.format
        arperson = self.arperson if self.arperson else ""
        customer = self.customer if self.customer else ""
        for comp in self.company_id:

            host        = comp.server
            database    = comp.db_name
            user        = comp.db_usr
            password    = comp.db_pass 
            
            conn = pymssql.connect(host=host, user=user, password=password, database=database)

            msgsql1 ="""
                        declare @customer varchar(50), @arperson varchar(50),@datefrom varchar(20),@dateto varchar(20)

                        set @arperson = '""" + arperson + """' 
                        set @customer = '""" + customer + """' 
                        set @datefrom = '""" + self.datefrom.strftime("%Y%m%d")  + """' 
                        set @dateto = '""" + self.dateto.strftime("%Y%m%d")  + """' 
                        
                      
                        
                        select  iday,  
                                idivisi,
                                 cardcode,
                                 cardname ,
                                cardfname,
                                  slsgroup,
                                u_AR_Person,
                                sum(amount) amount
                        from (
                        select 
                                case when convert(varchar,a.taxdate,112)< @datefrom then '00' else right(convert(varchar,a.TaxDate ,112),2) end  iday, 
                                d.GroupName
                                idivisi,
                                c.cardcode,
                                c.cardname ,
                                c.cardfname,
                                e.memo slsgroup,
                                c.u_AR_Person,
                                sum(a.doctotal-a.PaidSys) amount
                        from oinv a  
                        inner join ocrd c on a.cardcode = c.cardcode 
                        inner join ocrg d on c.groupcode = d.groupcode 
                        inner join oslp e on c.slpcode = e.slpcode 
                        where 
                            convert(varchar, a.Taxdate,112) <= @dateto 
                            and (a.doctotal-a.PaidSys)<>0 
                            and a.CANCELED ='N'
                            and isnull( c.u_AR_Person,'') like '%' +  @arperson  + '%'
                            and c.cardcode + c.cardname like '%' +  @customer  + '%'
                        group by 
                                case when convert(varchar,a.taxdate,112)< @datefrom then '00' else right(convert(varchar,a.TaxDate ,112),2) end  , 
                                d.GroupName,
                                c.cardcode,
                                c.cardname ,
                                e.memo ,
                                c.u_AR_Person,
                                c.cardfname
                        union ALL
                        select 
                                case when convert(varchar,a.taxdate,112)< @datefrom then '00' else right(convert(varchar,a.TaxDate ,112),2) end  iday, 
                                d.GroupName
                                idivisi,
                                c.cardcode,
                                c.cardname ,
                                c.cardfname,
                                e.memo slsgroup,
                                c.u_AR_Person,
                                -1 * sum(a.doctotal-a.PaidSys) amount
                        from orin a  
                        inner join ocrd c on a.cardcode = c.cardcode 
                        inner join ocrg d on c.groupcode = d.groupcode 
                        inner join oslp e on c.slpcode = e.slpcode 
                        where 
                        convert(varchar, a.Taxdate,112) <= @dateto 
                            and (a.doctotal-a.PaidSys)<>0 
                            and a.CANCELED ='N'
                            and isnull( c.u_AR_Person,'') like '%' +  @arperson  + '%'
                            and c.cardcode + c.cardname like '%' +  @customer  + '%'
                        group by 
                                case when convert(varchar,a.taxdate,112)< @datefrom then '00' else right(convert(varchar,a.TaxDate ,112),2) end  , 
                                d.GroupName,
                                c.cardcode,
                                c.cardname ,
                                e.memo ,
                                c.u_AR_Person,
                                c.cardfname
                            )as a 
                            group by iday,  
                                idivisi,
                                 cardcode,
                                 cardname ,
                                cardfname,
                                  slsgroup,
                                u_AR_Person
                        order  by iday,  
                                idivisi,
                                 cardcode,
                                 cardname ,
                                cardfname,
                                  slsgroup,
                                u_AR_Person
            """
            msgsql2 ="""
                        declare @customer varchar(50), @arperson varchar(50),@datefrom varchar(20),@dateto varchar(20)

                        set @arperson = '""" + arperson + """' 
                        set @customer = '""" + customer + """' 
                        set @datefrom = '""" + self.datefrom.strftime("%Y%m%d")  + """' 
                        set @dateto = '""" + self.dateto.strftime("%Y%m%d")  + """' 
                        
                      
                        select  iday,  
                                idivisi,
                                 cardcode,
                                 cardname ,
                                cardfname,
                                  slsgroup,
                                u_AR_Person,
                                sum(amount) amount
                        from (
                        select 
                                case when convert(varchar,a.DocDuedate,112)< @datefrom then '00' else right(convert(varchar,a.DocDuedate ,112),2) end  iday, 
                                d.GroupName
                                idivisi,
                                c.cardcode,
                                c.cardname ,
                                c.cardfname,
                                e.memo slsgroup,
                                c.u_AR_Person,
                                sum(a.doctotal-a.PaidSys) amount
                        from oinv a  
                        inner join ocrd c on a.cardcode = c.cardcode 
                        inner join ocrg d on c.groupcode = d.groupcode 
                        inner join oslp e on c.slpcode = e.slpcode 
                        where 
                            convert(varchar, a.DocDuedate,112) <= @dateto 
                            and (a.doctotal-a.PaidSys)<>0 
                            and a.CANCELED ='N'
                            and isnull( c.u_AR_Person,'') like '%' +  @arperson  + '%'
                            and c.cardcode + c.cardname like '%' +  @customer  + '%'
                        group by 
                               case when convert(varchar,a.DocDuedate,112)< @datefrom then '00' else right(convert(varchar,a.DocDuedate ,112),2) end , 
                                d.GroupName,
                                c.cardcode,
                                c.cardname ,
                                e.memo ,
                                c.u_AR_Person,
                                c.cardfname
                        union ALL
                        select 
                                case when convert(varchar,a.DocDuedate,112)< @datefrom then '00' else right(convert(varchar,a.DocDuedate ,112),2) end iday, 
                                d.GroupName
                                idivisi,
                                c.cardcode,
                                c.cardname ,
                                c.cardfname,
                                e.memo slsgroup,
                                c.u_AR_Person,
                                -1 * sum(a.doctotal-a.PaidSys) amount
                        from orin a  
                        inner join ocrd c on a.cardcode = c.cardcode 
                        inner join ocrg d on c.groupcode = d.groupcode 
                        inner join oslp e on c.slpcode = e.slpcode 
                        where 
                        convert(varchar, a.DocDuedate,112) <= @dateto 
                            and (a.doctotal-a.PaidSys)<>0 
                            and a.CANCELED ='N'
                            and isnull( c.u_AR_Person,'') like '%' +  @arperson  + '%'
                            and c.cardcode + c.cardname like '%' +  @customer  + '%'
                        group by 
                                case when convert(varchar,a.DocDuedate,112)< @datefrom then '00' else right(convert(varchar,a.DocDuedate ,112),2) end  , 
                                d.GroupName,
                                c.cardcode,
                                c.cardname ,
                                e.memo ,
                                c.u_AR_Person,
                                c.cardfname
                            )as a 
                            group by iday,  
                                idivisi,
                                 cardcode,
                                 cardname ,
                                cardfname,
                                  slsgroup,
                                u_AR_Person
                        order  by iday,  
                                idivisi,
                                 cardcode,
                                 cardname ,
                                cardfname,
                                  slsgroup,
                                u_AR_Person
            """
            if self.based_on =="tftop":
                msgsql = msgsql1
            else :
                msgsql = msgsql2
            data = pandas.io.sql.read_sql(msgsql,conn) 
            listfinal.append(data)
  
        


        df = pd.concat(listfinal) 

        if self.export_to =="xls":
            filename = filenamexls2 
            #report = df.groupby(["Group","AR Person"]).sum()
            df.to_excel(mpath + '/temp/'+ filenamexls2,index=False,engine='xlsxwriter') 
            datax = df.pivot_table(index=["cardcode" ,"cardname","idivisi","slsgroup","u_AR_Person"],columns=["iday"],aggfunc=np.sum,values=["amount"],fill_value=0,margins=True ).sort_index().to_excel(mpath + '/temp/'+ filenamexls2)
        
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

 