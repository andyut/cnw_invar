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
                        declare @datefrom varchar(10) ,
                        @dateto varchar(10)

                        set @datefrom = '""" + self.datefrom.strftime("%Y%m%d")  + """'
                        set @dateto = '""" + self.dateto.strftime("%Y%m%d")  + """'

                        DECLARE   @table TABLE  ( idx int identity(1,1),
                                                    tanggal varchar(20),
                                                    hari varchar(20),
                                                    wet numeric (19,6),
                                                    catering numeric (19,6),
                                                    horeka numeric (19,6),
                                                    retail numeric (19,6),
                                                    pastry numeric (19,6),
                                                    qsr numeric (19,6),
                                                total_proyeksi numeric (19,6),
                                                total_realisasi numeric (19,6),
                                                percentase numeric (19,6),
                                                realisasi_horekadll numeric (19,6),
                                                realisasi_wet numeric (19,6),
                                                realisasi_cabangdll numeric(19,6),
                                                total_penerimaan numeric(19,6),
                                                realisasi_cabang_wet numeric(19,6),
                                                realisasi_cabang_group numeric(19,6),
                                                realisasi_cabang_total numeric(19,6) 
                                                )
                        INSERT INTO @TABLE
                        SELECT 
                                tanggal ,
                                hari ,
                                sum (WET ) WET,
                                sum (CATERING ) CATERING,
                                sum (HOREKA )HOREKA ,
                                sum (RITEL ) RITEL,
                                sum (PASTRY  ) PASTRY,
                                sum (QSR  ) QSR,
                                sum (TOTAL_PROYEKSI )TOTAL_PROYEKSI ,
                                sum (TOTAL_REALISASI )TOTAL_REALISASI ,
                                sum (PERSENTASE  ) PERSENTASE,
                                sum (realisasi_horeka ) realisasi_horeka,
                                sum (realisasi_wet ) realisasi_wet,
                                sum (realisasi_cabang )realisasi_cabang ,
                                sum (realisasi_total )realisasi_total ,
                                sum (TOTAL_cabang_WET )TOTAL_cabang_WET ,
                                sum (TOTAL_cabang_GROUP ) TOTAL_cabang_GROUP,
                                sum (TOTAL_cabang ) TOTAL_cabang
                        FROM 
                        (
                        select  
                                case when 
                                        convert(Varchar,a.docduedate,112) < @datefrom then '00' 
                                    else 
                                        right(convert(Varchar,a.docduedate,112),2)  
                                end tanggal,
                                case when 
                                        convert(Varchar,a.docduedate,112) < @datefrom then 'OVERDUE' 
                                else 
                                        format(convert(datetime,a.docduedate),'dddd','id-id') 
                                end hari , 
                                SUM(CASE WHEN c.u_group2 ='WET' THEN (a.doctotal  - a.paidsys) else 0 end ) WET ,
                                SUM(CASE WHEN c.u_group2 ='CATERING' THEN (a.doctotal  - a.paidsys) else 0 end) CATERING ,
                                SUM(CASE WHEN c.u_group2 ='HOREKA' THEN (a.doctotal  - a.paidsys) else 0 end) HOREKA ,
                                SUM(CASE WHEN c.u_group2 ='RITEL' THEN (a.doctotal  - a.paidsys) else 0 end) RITEL ,
                                SUM(CASE WHEN c.u_group2 ='PASTRY' THEN (a.doctotal  - a.paidsys) else 0 end) PASTRY ,
                                SUM(CASE WHEN c.u_group2 ='QSR' THEN (a.doctotal  - a.paidsys) else 0 end) QSR ,
                                SUM(CASE WHEN c.u_group2 IN ('WET','CATERING','HOREKA','RITEL','PASTRY','QSR') THEN  (a.doctotal  - a.paidsys) else 0 end) TOTAL_PROYEKSI,  
                                0 TOTAL_REALISASI ,
                                0 PERSENTASE ,
                                0 realisasi_horeka ,
                                0 realisasi_wet ,
                                0 realisasi_cabang ,
                                0 realisasi_total ,
                                0 TOTAL_cabang_WET ,
                                0 TOTAL_cabang_GROUP ,
                                0 TOTAL_cabang 
                        from oinv a 
                        inner join ocrd b on a.cardcode = b.cardcode
                        inner join ocrg c on b.groupcode = c.groupcode
                        where convert(Varchar,a.docduedate,112) <= @dateto
                        AND A.CANCELED= 'N'
                        AND A.DocStatus = 'O'
                        group by case when 
                                        convert(Varchar,a.docduedate,112) < @datefrom then '00' 
                                    else 
                                        right(convert(Varchar,a.docduedate,112),2)  
                                end, 
                                case when 
                                        convert(Varchar,a.docduedate,112) < @datefrom then 'OVERDUE' 
                                else 
                                        format(convert(datetime,a.docduedate),'dddd','id-id') 
                                end 
                        

                        UNION ALL
                        select  
                                right(convert(Varchar,a.refdate,112),2)  iday,
                                format(convert(datetime,a.refdate),'dddd','id-id') hari , 
                                0, 
                                0, 
                                0, 
                                0, 
                                0, 
                                0, 
                                0, 
                                -1 * SUM(CASE WHEN c.u_group2 IN ('WET','CATERING','HOREKA','RITEL','PASTRY','QSR')  THEN (a.debit - a.credit ) else 0 end) TOTAL_REALISASI ,
                                0 , 
                                -1 * SUM(CASE WHEN c.u_group2 IN ('CATERING','HOREKA','RITEL','PASTRY','QSR')  THEN (a.debit - a.credit ) else 0 end) HOREKA ,
                                -1 * SUM(CASE WHEN c.u_group2 IN ('WET')  THEN (a.debit - a.credit ) else 0 end) WET,
                                -1 * SUM(CASE WHEN c.u_group2 NOT IN ('WET','CATERING','HOREKA','RITEL','PASTRY','QSR')  THEN (a.debit - a.credit ) else 0 end) IGROUP ,
                                -1* sum(a.debit - a.credit ) TOTALPENERIMAAN,
                                0,
                                0,
                                0
                        from 
                        jdt1 a 
                        INNER JOIN ocrd b on a.ShortName = b.cardcode 
                        INNER JOIN ocrg c on b.groupcode = c.groupcode 
                        INNER JOIN ojdt d on a.transid  = d.TransId
                        where  convert(Varchar,a.refdate,112) between @datefrom and @dateto
                        and a.account = '1130001' and a.TransType in (30,24)
                        AND LEFT(D.U_Trans_No,2) IN ('BD','KD')
                        group by    right(convert(Varchar,a.refdate,112),2),
                                    format(convert(datetime,a.refdate),'dddd','id-id') 

                        UNION ALL
                        select  
                                right(convert(Varchar,a.refdate,112),2)  iday,
                                format(convert(datetime,a.refdate),'dddd','id-id') hari , 
                                0, 
                                0, 
                                0, 
                                0, 
                                0, 
                                0, 
                                0, 
                                0 TOTAL_REALISASI ,
                                0 , 
                                0 HOREKA ,
                                0 WET,
                                0 IGROUP ,
                                0 TOTALPENERIMAAN,
                                -1 * SUM(CASE WHEN c.u_group2 IN ('WET')  THEN (a.debit - a.credit ) else 0 end) wet ,
                                -1 * SUM(CASE WHEN c.u_group2 not IN ('WET')  THEN (a.debit - a.credit ) else 0 end) cabang ,
                                -1 * SUM  (a.debit - a.credit )  total 
                        from 
                        PTIMS.DBO.jdt1 a 
                        INNER JOIN PTIMS.DBO.ocrd b on a.ShortName = b.cardcode 
                        INNER JOIN PTIMS.DBO.ocrg c on b.groupcode = c.groupcode 
                        INNER JOIN PTIMS.DBO.ojdt d on a.transid  = d.TransId
                        where  convert(Varchar,a.refdate,112) between @datefrom and @dateto
                        and a.account = '1130001' and a.TransType in (30,24)
                        AND LEFT(D.U_Trans_No,2) IN ('BD','KD')
                        group by    right(convert(Varchar,a.refdate,112),2),
                                    format(convert(datetime,a.refdate),'dddd','id-id') 


                        UNION ALL
                        select  
                                right(convert(Varchar,a.refdate,112),2)  iday,
                                format(convert(datetime,a.refdate),'dddd','id-id') hari , 
                                0, 
                                0, 
                                0, 
                                0, 
                                0, 
                                0, 
                                0, 
                                0 TOTAL_REALISASI ,
                                0 , 
                                0 HOREKA ,
                                0 WET,
                                0 IGROUP ,
                                0 TOTALPENERIMAAN,
                                -1 * SUM(CASE WHEN c.u_group2 IN ('WET')  THEN (a.debit - a.credit ) else 0 end) wet ,
                                -1 * SUM(CASE WHEN c.u_group2 not IN ('WET')  THEN (a.debit - a.credit ) else 0 end) cabang ,
                                -1 * SUM  (a.debit - a.credit )  total 
                        from 
                        PTSCA.DBO.jdt1 a 
                        INNER JOIN PTSCA.DBO.ocrd b on a.ShortName = b.cardcode 
                        INNER JOIN PTSCA.DBO.ocrg c on b.groupcode = c.groupcode 
                        INNER JOIN PTSCA.DBO.ojdt d on a.transid  = d.TransId
                        where  convert(Varchar,a.refdate,112) between @datefrom and @dateto
                        and a.account = '1130001' and a.TransType in (30,24)
                        AND LEFT(D.U_Trans_No,2) IN ('BD','KD')
                        group by    right(convert(Varchar,a.refdate,112),2),
                                    format(convert(datetime,a.refdate),'dddd','id-id') 

                        UNION ALL
                        select  
                                right(convert(Varchar,a.refdate,112),2)  iday,
                                format(convert(datetime,a.refdate),'dddd','id-id') hari , 
                                0, 
                                0, 
                                0, 
                                0, 
                                0, 
                                0, 
                                0, 
                                0 TOTAL_REALISASI ,
                                0 , 
                                0 HOREKA ,
                                0 WET,
                                0 IGROUP ,
                                0 TOTALPENERIMAAN,
                                -1 * SUM(CASE WHEN c.u_group2 IN ('WET')  THEN (a.debit - a.credit ) else 0 end) wet ,
                                -1 * SUM(CASE WHEN c.u_group2 not IN ('WET')  THEN (a.debit - a.credit ) else 0 end) cabang ,
                                -1 * SUM  (a.debit - a.credit )  total 
                        from 
                        PTCKI.DBO.jdt1 a 
                        INNER JOIN PTCKI.DBO.ocrd b on a.ShortName = b.cardcode 
                        INNER JOIN PTCKI.DBO.ocrg c on b.groupcode = c.groupcode 
                        INNER JOIN PTCKI.DBO.ojdt d on a.transid  = d.TransId
                        where  convert(Varchar,a.refdate,112) between @datefrom and @dateto
                        and a.account = '1130001' and a.TransType in (30,24)
                        AND LEFT(D.U_Trans_No,2) IN ('BD','KD')
                        group by    right(convert(Varchar,a.refdate,112),2),
                                    format(convert(datetime,a.refdate),'dddd','id-id') 

                        UNION ALL
                        select  
                                right(convert(Varchar,a.refdate,112),2)  iday,
                                format(convert(datetime,a.refdate),'dddd','id-id') hari , 
                                0, 
                                0, 
                                0, 
                                0, 
                                0, 
                                0, 
                                0, 
                                0 TOTAL_REALISASI ,
                                0 , 
                                0 HOREKA ,
                                0 WET,
                                0 IGROUP ,
                                0 TOTALPENERIMAAN,
                                -1 * SUM(CASE WHEN c.u_group2 IN ('WET')  THEN (a.debit - a.credit ) else 0 end) wet ,
                                -1 * SUM(CASE WHEN c.u_group2 not IN ('WET')  THEN (a.debit - a.credit ) else 0 end) cabang ,
                                -1 * SUM  (a.debit - a.credit )  total 
                        from 
                        PTBWN.DBO.jdt1 a 
                        INNER JOIN PTBWN.DBO.ocrd b on a.ShortName = b.cardcode 
                        INNER JOIN PTBWN.DBO.ocrg c on b.groupcode = c.groupcode 
                        INNER JOIN PTBWN.DBO.ojdt d on a.transid  = d.TransId
                        where  convert(Varchar,a.refdate,112) between @datefrom and @dateto
                        and a.account = '1130001' and a.TransType in (30,24)
                        AND LEFT(D.U_Trans_No,2) IN ('BD','KD')
                        group by    right(convert(Varchar,a.refdate,112),2),
                                    format(convert(datetime,a.refdate),'dddd','id-id') 
                        )

                        AS A 
                        GROUP BY  tanggal ,
                                hari 
                        ORDER BY tanggal ,
                                hari 

                        update @table 
                            set percentase = ( total_realisasi) / total_proyeksi * 100
                        where total_proyeksi<>0

                        SELECT * FROM @TABLE ORDER BY TANGGAL
            """
            data = pandas.io.sql.read_sql(msgsql,conn) 
            listfinal.append(data)
  
        


        df = pd.concat(listfinal) 

        if self.export_to =="xls":
            filename = filenamexls2 
            #report = df.groupby(["Group","AR Person"]).sum()
            #df.to_excel(mpath + '/temp/'+ filenamexls2,index=False,engine='xlsxwriter') 
            #df.pivot_table(index=["iday" ],columns=["Header","idivisi"],aggfunc=np.sum,values=["amount"],fill_value=0,margins=True ).sort_index().to_excel(mpath + '/temp/'+ filenamexls2,engine='xlsxwriter')
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

 