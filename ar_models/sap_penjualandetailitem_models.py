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

class SAP_penjualandetailitem(models.TransientModel):
    _name           = "cnw.penjualandetailitem"
    _description    = "cnw.penjualandetailitem"
    company_id      = fields.Many2many('res.company', string="Company",required=True)
    
    datefrom        = fields.Date ("Date From", default=fields.Date.today())
    dateto          = fields.Date ("Date To", default=fields.Date.today()) 
    customer        = fields.Char("Customer",default=" ")
    items           = fields.Char("Items",default=" ")
    igroups         = fields.Char("Item Group",default=" ")
    sales           = fields.Char("Sales Person / Group",default=" ")
    export_to       = fields.Selection([    ('xls', 'Excel-Detail'),
                                            ('xls-summary1', 'Summary Per Customer Per Month'),
                                            ('xls-summary2', 'Summary Per Customer Per Item Group'),
                                            ('xls-summary3', 'Summary Per Item Per Month'),
                                            ('xls-summary4', 'Summary Per Sales Per  Month'),
                                            ('xls-summary5', 'Summary Per Sales Per Customer Per Month'),
                                            ('xls-summary6', 'Excel-Summary'),
                                            ('hs_realisasi','HS Realisasi Import Per Item Code'),
                                            ('hs_realisasi_summary','HS Realisasi Import Per HS'),
                                            ],string='Export To', default='xls',required=True)
    filexls         = fields.Binary("File Output")    
    filenamexls     = fields.Char("File Name Output")
    
    @api.multi
    def view_penjualandetailitem(self): 
        mpath       = get_module_path('cnw_invar')
        filenamexls = 'penjualanItem_'+   self.dateto.strftime("%Y%m%d")  + '.xlsx'
        filenamepdf = 'penjualanItem_'+   self.dateto.strftime("%Y%m%d")  + '.pdf'
        filename    =""
        filepath    = mpath + '/temp/'
        logo        = mpath + '/awr_template/logoigu.png'
        listfinal   = []
        cssfile     = mpath + '/awr_template/style.css'

        #global Var

        
        pd.options.display.float_format = '{:,.2f}'.format
        
        partner     = self.customer if self.customer else ""
        items       = self.items if self.items else ""
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
                                    @partner	varchar(50),
                                    @item		varchar(50),
                                    @sales      varchar(50),
                                    @company    varchar(20)


                            set @datefrom ='""" +    self.datefrom.strftime("%Y%m%d")   + """'
                            set @dateto ='"""   +    self.dateto.strftime("%Y%m%d")   + """'
                            set @partner ='"""  +    partner + """'
                            set @item ='"""     +    items   + """'
                            set @sales ='"""    +    sales   + """'
                            SELECT  
                                    '""" + comp.code_base  + """' Company,
                                    a.docnum invoice,
                                    a.numatcard ,
                                    a.CANCELED canceled,
                                    c.GroupName partner_group,
                                    a.cardcode partnercode, 
                                    '[' + a.cardcode + '] '+ a.shiptocode outlet,
                                    b.cardname partnercompany,
                                    convert(varchar,a.docdate,23) docdate, 
                                    substring(convert(varchar,a.docdate,112) ,5,2) imonth,
                                    left(convert(varchar,a.docdate,112) ,4) iyear,
                                    upper(d.SlpName) sales_in_trx,
                                    d.Memo slsgrp_in_trx,
                                    g.itemcode ,
                                    '['+ g.itemcode + '] '+ g.itemname as itemname,
                                    g.InvntryUom uom,
                                    g.U_Group product_group ,
                                    isnull(convert(varchar,g.u_hs_Code),'') HSCode,
                                    g.U_Spegroup product_spegroup,
                                    g.U_SubGroup product_subgroup,
                                    g.U_Brand product_brand ,
                                    f.quantity ,
                                    isnull(f.U_Qty_AR ,0) qty_receive,
                                    ISNULL(F.U_Price_AR ,F.price) price,
                                    f.vatgroup PPnGroup,
                                    f.vatprcnt PPnPrcnt,
                                    f.vatsum PPn , 
                                    f.linetotal - case f.linetotal when 0 then 0 else   ((f.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) end   Total ,
                                    a.u_idu_fpajak ,
                                    a.U_Kw_No
                            from oinv (nolock) a 
                                inner join ocrd (nolock) b on a.cardcode = b.cardcode 
                                inner join ocrg (nolock) c on b.GroupCode =c.GroupCode 
                                inner join oslp (nolock) d on a.slpcode = d.slpcode
                                inner join oslp (nolock) e on b.slpcode = e.slpcode
                                inner join inv1 (nolock) f on a.docentry = f.docentry 
                                inner join oitm (nolock) g on f.itemcode = g.itemcode
                                inner join OWHS (nolock) h on f.whscode = h.whscode
                            where a.canceled = 'N' and ( a.doctotal -a.vatsum+a.DiscSum)<>0
                            and G.ITEMCODE + g.itemname  like '%' + isnull(ltrim(rtrim(@item)),'') + '%'
                            and b.cardcode + b.cardname + isnull(a.ShipToCode,'') like '%' +  isnull(ltrim(rtrim(@partner)),'') + '%'

                            AND convert(varchar,a.docdate,112) between @datefrom and @dateto
                            and upper(d.SlpName) LIKE '%' + isnull( ltrim(rtrim(@sales)),'') +'%'
                            union all
                            select  
                                    '""" + comp.code_base  + """' Company,
                                    a.docnum invoice,
                                    a.numatcard ,
                                    a.CANCELED canceled,
                                    c.GroupName partner_group,
                                    a.cardcode partnercode, 
                                    '[' + a.cardcode + '] '+ a.shiptocode outlet ,
                                    b.cardname partnercompany,
                                    convert(varchar,a.docdate,23) docdate, 
                                    substring(convert(varchar,a.docdate,112) ,5,2) imonth,
                                    left(convert(varchar,a.docdate,112) ,4) iyear,
                                    upper(d.SlpName) sales_in_trx,
                                    d.Memo slsgrp_in_trx,
                                    g.itemcode ,
                                    '['+ g.itemcode + '] '+ g.itemname as itemname,
                                    g.InvntryUom uom,
                                    g.U_Group product_group ,
                                    isnull(convert(varchar,g.u_hs_Code),'') HSCode,
                                    g.U_Spegroup product_spegroup,
                                    g.U_SubGroup product_subgroup,
                                    g.U_Brand product_brand ,
                                    -1 * f.quantity ,
                                    -1 * isnull(f.U_Qty_AR ,0) qty_ar,
                                    -1 * f.price ,
                                    f.vatgroup PPnGroup,
                                    f.vatprcnt PPnPrcnt,
                                    -1 * f.vatsum PPn , 
                                    -1 * (f.linetotal - case f.linetotal when 0 then 0 else   ((f.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) end )  total ,
                                    a.u_idu_fpajak ,
                                    a.U_Kw_No
                            from orin (nolock) a 
                                inner join ocrd (nolock) b on a.cardcode = b.cardcode 
                                inner join ocrg (nolock) c on b.GroupCode =c.GroupCode 
                                inner join oslp (nolock) d on a.slpcode = d.slpcode
                                inner join oslp (nolock) e on b.slpcode = e.slpcode
                                inner join rin1 (nolock) f on a.docentry = f.docentry 
                                inner join oitm (nolock) g on f.itemcode = g.itemcode
                                inner join OWHS (nolock)h on f.whscode = h.whscode
                            where a.canceled = 'N' and ( a.doctotal -a.vatsum+a.DiscSum)<>0
                            and G.ITEMCODE + g.itemname  like '%' + isnull(ltrim(rtrim(@item)),'') + '%'
                            and b.cardcode + b.cardname + isnull(a.ShipToCode,'') like '%' +  isnull(ltrim(rtrim(@partner)),'') + '%'
                            and upper(d.SlpName) LIKE '%' + isnull( ltrim(rtrim(@sales)),'') +'%'
                            AND convert(varchar,a.docdate,112) between @datefrom and @dateto

            """
            if self.export_to == "hs_realisasi":
                msg_sql ="""
                            declare 
                                    @datefrom	varchar(10),
                                    @dateto		varchar(10),
                                    @partner	varchar(50),
                                    @item		varchar(50),
                                    @sales      varchar(50),
                                    @company    varchar(20)


                            set @datefrom ='""" +    self.datefrom.strftime("%Y%m%d")   + """'
                            set @dateto ='"""   +    self.dateto.strftime("%Y%m%d")   + """'
                            set @partner ='"""  +    partner + """'
                            set @item ='"""     +    items   + """'
                            set @group ='"""     +    igroup   + """'
                            set @sales ='"""    +    sales   + """'                
                            SELECT 
                                Company,
                                hs_code ,
                                spegroup, 
                                igroup, 
                                subgroup, 
                                itemcode,
                                itemname,
                                cardcode,
                                customer ,
                                address,
                                phone, 
                                npwp,
                                    GroupCustomer,
                                    sum(quantity) quantity
                            FROM (
                            select '{{company}}' Company,
                                    isnull(convert(varchar,c.u_hs_code),'') hs_code ,
                                isnull(c.u_speGroup,'') spegroup, 
                                isnull(c.u_Group,'') igroup, 
                                isnull(c.u_SubGroup,'') subgroup, 
                                isnull(c.itemcode,'') itemcode,
                                isnull(c.itemname,'') itemname,
                                    d.cardcode , isnull(d.cardname,'') customer ,
                                    isnull(d.Address,'') address,
                                    isnull(d.Phone1,' ') + ' '+ isnull(d.Phone2,' ') phone, 
                                    isnull(d.LicTradNum ,'') npwp,
                                    isnull(e.GroupName ,'') GroupCustomer,
                                    sum(b.quantity) quantity
                                    
                                    
                            from OINV (nolock) A 
                                INNER JOIN INV1  (nolock) B ON A.DOCENTRY = B.DOCENTRY 
                                inner join ocrd  (nolock) d on a.cardcode = d.cardcode 
                                inner join ocrg  (nolock) e on d.groupcode = e.groupcode
                                inner join OITM  (nolock) C ON B.ItemCode = C.ItemCode

                            where convert(varchar,a.docdate,112) between @datefrom and  @dateto 
                            and  isnull(c.u_group ,'')  +    isnull(c.u_subgroup,'')  like '%' + isnull('{{param1}}','') + '%'
                            and c.itemcode + c.itemname like '%' + isnull('{{param2}}','') + '%'
                            and isnull(convert(varchar,c.u_hs_code),'')<>''
                            and a.canceled ='N'

                            group by 
                                    
                                    isnull(convert(varchar,c.u_hs_code),'')  ,
                                isnull(c.u_speGroup,''), 
                                isnull(c.u_Group,'') , 
                                isnull(c.u_SubGroup,'') , 
                                isnull(c.itemcode,'') ,
                                isnull(c.itemname,'') ,
                                    d.cardcode , isnull(d.cardname,'') ,
                                    isnull(d.Address,'') ,
                                    isnull(d.Phone1,' ') + ' '+  isnull(d.Phone2,' ') , 
                                    isnull(d.LicTradNum ,'') ,
                                    isnull(e.GroupName ,'')

                            union all
                            select '{{company}}' Company,
                                    isnull(convert(varchar,c.u_hs_code),'') hs_code ,
                                isnull(c.u_speGroup,'') spegroup, 
                                isnull(c.u_Group,'') igroup, 
                                isnull(c.u_SubGroup,'') subgroup, 
                                isnull(c.itemcode,'') itemcode,
                                isnull(c.itemname,'') itemname,
                                d.cardcode , isnull(d.cardname,'') customer ,
                                    isnull(d.Address,'') address,
                                    isnull(d.Phone1,' ') + ' '+ isnull(d.Phone2,' ') phone, 
                                    isnull(d.LicTradNum ,'') npwp,
                                    isnull(e.GroupName ,'') GroupCustomer,
                                    -1 * sum(b.quantity) quantity
                                    
                                    
                            from ORIN  (nolock)  A 
                                INNER JOIN RIN1  (nolock) B ON A.DOCENTRY = B.DOCENTRY 
                                inner join ocrd  (nolock)  d on a.cardcode = d.cardcode 
                                inner join ocrg  (nolock)  e on d.groupcode = e.groupcode
                                inner join OITM  (nolock)  C ON B.ItemCode = C.ItemCode

                            where convert(varchar,a.docdate,112) between  @datefrom and  @dateto 
                            and  isnull(c.u_group ,'')  +    isnull(c.u_subgroup,'')  like '%' + isnull('{{param1}}','') + '%'
                            and c.itemcode + c.itemname like '%' + isnull('{{param2}}','') + '%'
                            and c.u_group like '%SEAFOOD%'
                            and isnull(convert(varchar,c.u_hs_code),'')<>''
                            and a.canceled ='N'

                            group by 
                                    
                                    isnull(convert(varchar,c.u_hs_code),'')  ,
                                isnull(c.u_speGroup,''), 
                                isnull(c.u_Group,'') , 
                                isnull(c.u_SubGroup,'') , 
                                isnull(c.itemcode,'') ,
                                isnull(c.itemname,'') ,
                                    d.cardcode , isnull(d.cardname,'') ,
                                    isnull(d.Address,'') ,
                                    isnull(d.Phone1,' ') + ' '+  isnull(d.Phone2,' ') , 
                                    isnull(d.LicTradNum ,'') ,
                                    isnull(e.GroupName ,'')
                            )as a 

                            group by Company,
                                hs_code ,
                                spegroup, 
                                igroup, 
                                subgroup, 
                                itemcode,
                                itemname,
                                cardcode,
                                customer ,
                                address,
                                phone, 
                                npwp,
                                GroupCustomer                
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
            pivottbl = df.pivot_table(index=["Company","partnercompany"],columns=["imonth"],aggfunc=np.sum,  values=["Total"],fill_value="0",margins=True)
            pivottbl.to_excel(mpath + '/temp/'+ filenamexls)  
                     
        if self.export_to =="xls-summary2":
            filename = filenamexls 
            pivottbl = df.pivot_table(index=["Company","partnercompany","product_group"],columns=["imonth"],aggfunc=np.sum,  values=["Total"],fill_value="0",margins=True)
            pivottbl.to_excel(mpath + '/temp/'+ filenamexls)  
                     
        if self.export_to =="xls-summary3":
            filename = filenamexls 
            pivottbl = df.pivot_table(index=["product_group","itemname"],columns=["Company","imonth"],aggfunc=np.sum,  values=["Total"],fill_value="0",margins=True)
            pivottbl.to_excel(mpath + '/temp/'+ filenamexls)  
                     
        if self.export_to =="xls-summary4":
            filename = filenamexls 
            pivottbl = df.pivot_table(index=["sales_in_trx","partner_group"],columns=["Company","imonth"],aggfunc=np.sum,  values=["Total"],fill_value="0",margins=True)
            pivottbl.to_excel(mpath + '/temp/'+ filenamexls)  

        if self.export_to =="xls-summary5":
            filename = filenamexls 
            pivottbl = df.pivot_table(index=[ "sales_in_trx","partnercompany"],columns=["Company","imonth"],aggfunc=np.sum,  values=["Total"],fill_value="0",margins=True)
            pivottbl.to_excel(mpath + '/temp/'+ filenamexls)  
                                      
        if self.export_to =="xls-summary6":
            filename = filenamexls 
            pivottbl = df.pivot_table(index=[ "invoice","numatcard","canceled","partnercode","outlet","docdate"],aggfunc=np.sum,  values=["PPn","Total"],fill_value="0",margins=True)
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
