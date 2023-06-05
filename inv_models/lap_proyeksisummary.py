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




class CNWproyeksisummary(models.TransientModel):
    _name           = "cnw.invar.proyeksisummary"
    _description    = "Lap Tukar Faktur BK"
    company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)

    datefrom        = fields.Date("Date from",default=lambda s:fields.Date.today())
    dateto          = fields.Date("Date To",default=lambda s:fields.Date.today())
    arperson        = fields.Char("AR Person ",default="")
    customer        = fields.Char("customer",default="")
    filexls         = fields.Binary("File Output")    
    filenamexls     = fields.Char("File Name Output")
    
    export_to       = fields.Selection([ ('xls', 'Excel') ],string='Export To', default='xls')

    def getproyeksisummary(self):

#PATH & FILE NAME & FOLDER
        mpath       = get_module_path('cnw_invar')
        filenamexls2    = 'proyeksisummary_'+   self.dateto.strftime("%Y%m%d")  + '.xlsx'
        filenamepdf    = 'proyeksisummary_'+   self.dateto.strftime("%Y%m%d")  + '.pdf'
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

            msgsql ="""
                        declare @dateto varchar(20)


                        set @dateto = convert(varchar,getdate(),112)
                        set @dateto = '""" + self.dateto.strftime("%Y%m%d")  + """'  
 

                    select  'proyeksi' Header,
                            right(convert(varchar,a.DueDate ,112),2) iday, 
                            case 
                            when d.GroupCode in (100,102,120) then '01-CATERING'
                            when d.GroupCode in (103) then '02-HOREKA'
                            when d.GroupCode in (105) then '03-RETAIL'
                            when d.GroupCode in (106) then '04-PASTRY'
                            when d.GroupCode in (107,120) then '05-QSR'
                            when d.GroupCode in (109,110) then '06-WET'
                            when d.GroupCode in (114) then '07-ECOMMERCE'
                            when d.GroupCode in (108,116,117,118,121) then '08-GROUP'
                            else   '09-OTHERS'
                            end idivisi,
                            sum(a.debit-a.credit) amount
                    from jdt1 A
                    inner join ojdt B ON A.transid = b.transid 
                    inner join ocrd c on a.ShortName = c.cardcode 
                    inner join ocrg d on c.groupcode = d.groupcode 

                    where  convert(varchar,a.DueDate ,112) <=  @dateto 
                    and a.account ='1130001' and a.transtype in (13,14)
                    group by right(convert(varchar,a.DueDate ,112),2) ,
                            case 
                            when d.GroupCode in (100,102,120) then '01-CATERING'
                            when d.GroupCode in (103) then '02-HOREKA'
                            when d.GroupCode in (105) then '03-RETAIL'
                            when d.GroupCode in (106) then '04-PASTRY'
                            when d.GroupCode in (107,120) then '05-QSR'
                            when d.GroupCode in (109,110) then '06-WET'
                            when d.GroupCode in (114) then '07-ECOMMERCE'
                            when d.GroupCode in (108,116,117,118,121) then '08-GROUP'
                            else   '09-OTHERS'
                            end

                    union all 

                    select  'realisasi' Header,
                            right(convert(varchar,a.RefDate ,112),2) iday,
                            case 
                                when d.GroupCode in (100,102,120) then '01-CATERING'
                                when d.GroupCode in (103) then '02-HOREKA'
                                when d.GroupCode in (105) then '03-RETAIL'
                                when d.GroupCode in (106) then '04-PASTRY'
                                when d.GroupCode in (107,120) then '05-QSR'
                                when d.GroupCode in (109,110) then '06-WET'
                                when d.GroupCode in (114) then '07-ECOMMERCE'
                                when d.GroupCode in (108,116,117,118,121) then '08-GROUP'
                                else   '09-OTHERS'
                            end,
                            
                            sum(a.debit-a.credit)
                    from jdt1 A
                    inner join ojdt B ON A.transid = b.transid 
                    inner join ocrd c on a.ShortName = c.cardcode 
                    inner join ocrg d on c.groupcode = d.groupcode 

                    where  convert(varchar,a.DueDate ,112) <=  @dateto 
                    and a.account ='1130001' and a.transtype in (24)  /* and left(b.U_Trans_No,2) in ('BD','KD') */
                    group by right(convert(varchar,a.refdate ,112),2) ,
                            case 
                            when d.GroupCode in (100,102,120) then '01-CATERING'
                            when d.GroupCode in (103) then '02-HOREKA'
                            when d.GroupCode in (105) then '03-RETAIL'
                            when d.GroupCode in (106) then '04-PASTRY'
                            when d.GroupCode in (107,120) then '05-QSR'
                            when d.GroupCode in (109,110) then '06-WET'
                            when d.GroupCode in (114) then '07-ECOMMERCE'
                            when d.GroupCode in (108,116,117,118,121) then '08-GROUP'
                            else   '09-OTHERS'
                            end
            """
            data = pandas.io.sql.read_sql(msgsql,conn) 
            listfinal.append(data)
  
        


        df = pd.concat(listfinal) 

        if self.export_to =="xls":
            filename = filenamexls2 
            #report = df.groupby(["Group","AR Person"]).sum()
            #df.to_excel(mpath + '/temp/'+ filenamexls2,index=False,engine='xlsxwriter') 
            df.pivot_table(index=["iday" ],columns=["Header","idivisi"],aggfunc=np.sum,values=["amount"],fill_value=0,margins=True ).sort_index().to_excel(mpath + '/temp/'+ filenamexls2,index=False,engine='xlsxwriter')
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

 