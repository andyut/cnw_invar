# -*- coding: utf-8 -*-
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

class SAP_penjualandetailSAP(models.TransientModel):
    _name           = "cnw.penjualandetail"
    _description    = "cnw.penjualandetail"
    company_id      = fields.Many2many('res.company', string="Company",required=True)
    
    datefrom        = fields.Date ("Date From", default=fields.Date.today())
    dateto          = fields.Date ("Date To", default=fields.Date.today()) 
    customer        = fields.Char("Customer",default=" ") 
    sales           = fields.Char("Sales Person / Group",default=" ")
    export_to       = fields.Selection([    ('xls', 'Excel-Detail'),
                                            ('xls-summary1', 'Summary Per Customer Per Month'), 
                                            ('xls-summary2', 'Summary Per Day'),
                                            ('xls-summary3', 'Summary Per Group  Per Month'), 
                                            ],string='Export To', default='xls',required=True)
    filexls         = fields.Binary("File Output")    
    filenamexls     = fields.Char("File Name Output")
    
    @api.multi
    def view_penjualandetail(self): 
        mpath       = get_module_path('cnw_invar')
        filenamexls = 'penjualan_'+   self.dateto.strftime("%Y%m%d")  + '.xlsx'
        filenamepdf = 'penjualan_'+   self.dateto.strftime("%Y%m%d")  + '.pdf'
        filename    =""
        filepath    = mpath + '/temp/'
        logo        = mpath + '/awr_template/logoigu.png'
        listfinal   = []
        cssfile     = mpath + '/awr_template/style.css'

        #global Var

        
        pd.options.display.float_format = '{:,.2f}'.format
        
        partner     = self.customer if self.customer else "" 
        sales       = self.sales if self.sales else ""


        for comp in self.company_id:
            host        = comp.server
            database    = comp.db_name
            user        = comp.db_usr
            password    = comp.db_pass 
            
            conn = pymssql.connect(host=host, user=user, password=password, database=database)

            #msg_sql= "exec  [dbo].[IGU_SLS_penjualandetailitem]   '"+ self.datefrom.strftime("%Y%m%d")   + "','"+ self.dateto.strftime("%Y%m%d")   + "','','" + comp.code_base  + "'"
            msg_sql= """
                            declare 
                                    @datefrom	varchar(10),
                                    @dateto		varchar(10),
                                    @customer	varchar(50), 
                                    @sales      varchar(50),
                                    @company    varchar(20)


                            set @datefrom ='""" +    self.datefrom.strftime("%Y%m%d")   + """'
                            set @dateto ='"""   +    self.dateto.strftime("%Y%m%d")   + """'
                            set @customer ='"""  +    partner + """'  
                            set @sales ='"""    +    sales   + """'     
                            set @company ='""" +   comp.code_base   + """' 


                            SELECT
                                        @company Company,
                                        a.doctype + '-' + 'INV' doctype ,
                                        a.docnum ,
                                        a.NumAtCard ,
                                        convert(varchar,a.docdate,23) docdate,
                                        substring(convert(varchar,a.docdate,112) ,5,2) imonth,
                                        a.cardcode ,
                                        '['+ a.cardcode + '] ' + a.cardname partner ,
                                        a.ShipToCode ,
                                        a.doctype ,
                                        a.U_Kw_No ,
                                        a.U_IDU_FPajak ,
                                        isnull(e.numatcard ,'')U_Cust_PO_No ,
                                        isnull(c.U_SlsEmpName ,'') sales,
                                        isnull(b.U_AR_Person ,'') arperson, 
                                        convert(varchar,a.CreateDate,23) createdate,
                                        a.doctime ,
                                        a.doctotal - a.vatsum dpp ,
                                        a.VatSum  ,
                                        a.DocTotal ,
                                        isnull(a.PaidSys ,0)PaidSys ,
                                        a.DocTotal - isnull(a.PaidSys ,0)  balance , 
                                        g.vatgroup ,
                                        'Catatan TukarFaktur: ' + isnull(b.Notes,'')  + char(13)+'<br/>'+
                                                'Faktur Pengiriman  : ' + isnull(b.U_delivery_invoice,'N') + char(13)+'<br/>'+
                                                'Print Faktur  : ' + isnull(b.U_PrintFaktur,'Y') + char(13)+'<br/>'+
                                                'Print Kwitansi  :<b> ' + 
                                                                            case isnull(b.U_PrintKwitansi,'Y')
                                                                                    when 'N' then 'Tidak Print Kwitansi'
                                                                                    when 'Y' then 'Print Kwitansi'
                                                                                    when 'O' then 'Print Kwitansi Per Outlet'
                                                                                    when 'P' then 'Print Kwitansi Per PO '
                                                                            end + char(13)+'</b><br/>'+
                                                'Print Faktur Pajak  : ' + isnull(b.U_PrintFP,'N')+ char(13)+'<br/>'+
                                                'Tukar Faktur  : ' + isnull(b.U_PenagihanType,'Y') + char(13)+'<br/>' +
                                                ' '
                                        as notes ,
                                        A.DISCPRCNT , A.DISCSUM
                            from OINV (nolock) A 
                                inner join ocrd (nolock)  b on a.cardcode = b.cardcode  
                                inner join ousr (nolock)  d on a.usersign = d.userid  
                                INNER JOIN 
                                                        (
                                                            SELECT DISTINCT A.DOCENTRY , B.VATGROUP, a.objtype  FROM  DBO.OINV (nolock)  A 
                                                                INNER JOIN DBO.INV1 (nolock)  B ON A.DOCENTRY = B.DOCENTRY 
                                                            WHERE convert(varchar,a.docdate,112) between @datefrom and @dateto
                                                                    and ( a.cardcode + a.cardname like '%' + ltrim(rtrim(isnull(@customer,''))) + '%')
                                                            union all
                                                            SELECT DISTINCT A.DOCENTRY , B.VATGROUP , a.objtype FROM  DBO.orin (nolock)  A 
                                                                INNER JOIN DBO.rin1 (nolock)  B ON A.DOCENTRY = B.DOCENTRY 
                                                            WHERE convert(varchar,a.docdate,112) between @datefrom and @dateto
                                                                    and ( a.cardcode + a.cardname like '%' + ltrim(rtrim(isnull(@customer,''))) + '%')
                                                        ) G ON A.DOCENTRY = G.DOCENTRY and a.objtype = g.objtype 
                                left outer join ordr (nolock)  e on a.u_igu_sodocentry = convert(varchar,e.docentry)
                                left outer join oslp (nolock)  c on b.SlpCode = c.SlpCode 

                            WHERE convert(varchar,a.docdate,112) between @datefrom and @dateto
                            and a.canceled='N'
                            and ( a.cardcode + a.cardname like '%' + ltrim(rtrim(isnull(@customer,''))) + '%')
                            --and ( b.u_ar_person like '%' + replace(ltrim(rtrim(@arperson)),' ','')   + '%'  )

                            union all

                            select      @company Company,
                                        a.doctype + '-' + 'CN' doctype ,
                                        a.docnum ,
                                        a.NumAtCard ,
                                        convert(varchar,a.docdate,23) docdate,
                                        substring(convert(varchar,a.docdate,112) ,5,2) imonth,
                                        a.cardcode ,
                                        '['+ a.cardcode + '] ' + a.cardname ,
                                        a.ShipToCode ,
                                        a.doctype ,
                                        a.U_Kw_No ,
                                        a.U_IDU_FPajak ,
                                        isnull(a.numatcard ,'')U_Cust_PO_No ,
                                        isnull(c.U_SlsEmpName ,'') sales,
                                        isnull(b.U_AR_Person ,'') arperson, 
                                        convert(varchar,a.CreateDate,23) createdate,
                                        a.doctime ,
                                        -1 * a.doctotal - a.vatsum dpp ,
                                        -1 * a.VatSum  ,
                                        -1 * a.DocTotal ,
                                        -1 * isnull(a.PaidSys ,0)PaidSys ,
                                        a.DocTotal - isnull(a.PaidSys ,0)  balance , 
                                        g.vatgroup ,
                                        isnull(b.notes,'') notes,
                                        A.DISCPRCNT , -1 *  A.DISCSUM

                            from ORIN (nolock) A 
                                inner join ocrd (nolock) b on a.cardcode = b.cardcode  
                                inner join ousr (nolock) d on a.usersign = d.userid  
                                inner JOIN 
                                                        (
                                                            SELECT DISTINCT A.DOCENTRY , B.VATGROUP, a.objtype  FROM  DBO.OINV (nolock)  A 
                                                                INNER JOIN DBO.INV1 (nolock)  B ON A.DOCENTRY = B.DOCENTRY 
                                                            WHERE convert(varchar,a.docdate,112) between @datefrom and @dateto
                                                                    and ( a.cardcode + a.cardname like '%' + ltrim(rtrim(isnull(@customer,''))) + '%')
                                                            union all
                                                            SELECT DISTINCT A.DOCENTRY , B.VATGROUP , a.objtype FROM  DBO.orin (nolock)  A 
                                                                INNER JOIN DBO.rin1 B  (nolock)  ON A.DOCENTRY = B.DOCENTRY 
                                                            WHERE convert(varchar,a.docdate,112) between @datefrom and @dateto
                                                                    and ( a.cardcode + a.cardname like '%' + ltrim(rtrim(isnull(@customer,''))) + '%')
                                                        ) G ON A.DOCENTRY = G.DOCENTRY and a.objtype = g.objtype 
                                left outer join oslp (nolock)  c on b.SlpCode = c.SlpCode 
                                
                            WHERE convert(varchar,a.docdate,112) between @datefrom and @dateto
                            and ( a.cardcode + a.cardname like '%' + ltrim(rtrim(isnull(@customer,''))) + '%')
                            --and ( b.u_ar_person like '%' + replace(ltrim(rtrim(@arperson)),' ','')   + '%'  )
                            and a.canceled='N'
            """
             
            data = pandas.io.sql.read_sql(msg_sql,conn)
            listfinal.append(data)

        df = pd.concat(listfinal)
          
        if self.export_to =="xls":
            filename = filenamexls 
            df.loc['Total'] = df.select_dtypes(pd.np.number).sum().reindex(df.columns, fill_value='')
            df.to_excel(mpath + '/temp/'+ filenamexls)  

        if self.export_to =="xls-summary1":
            filename = filenamexls 
            pivottbl = df.pivot_table(index=["Company","partner"],columns=["imonth"],aggfunc=np.sum,  values=["dpp"],fill_value="0",margins=True)
            pivottbl.to_excel(mpath + '/temp/'+ filenamexls)  
                     
        if self.export_to =="xls-summary2":
            filename = filenamexls 
            pivottbl = df.pivot_table(index=["docdate",],columns=["Company"],aggfunc=np.sum,  values=["dpp","VatSum","DocTotal"],fill_value="0",margins=True)
            pivottbl.to_excel(mpath + '/temp/'+ filenamexls)  
                     
        if self.export_to =="xls-summary3":
            filename = filenamexls 
            pivottbl = df.pivot_table(index=["product_group","itemname"],columns=["Company","imonth"],aggfunc=np.sum,  values=["dpp"],fill_value="0",margins=True)
            pivottbl.to_excel(mpath + '/temp/'+ filenamexls)  
                     

                                      
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
