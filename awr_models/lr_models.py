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
#import pyodbc
import pymssql


class CNW_LR(models.TransientModel):
    _name           = "cnw.awr28.lritem"
    _description    = "cnw.lritem"
    company_id      = fields.Many2many('res.company', string="Company",required=True)
    
    datefrom        = fields.Date ("Date From", default=fields.Date.today())
    dateto          = fields.Date ("Date To", default=fields.Date.today()) 
    partner         = fields.Char("Partner")
    item            = fields.Char("Items / Code")
    filexls         = fields.Binary("File Output")    
    filenamexls     = fields.Char("File Name Output")
    
    @api.multi
    def view_lritem(self): 
        mpath       = get_module_path('cnw_awr28')
        filename    = 'lritem_'+   self.dateto.strftime("%Y%m%d")  + '.xlsx'
        filepath    = mpath + '/temp/'+ filename
        listfinal   = []

        partner     = self.partner if self.partner else ""
        item        = self.item  if self.item else ""
        
        for comp in self.company_id:
            host        = comp.server
            database    = comp.db_name
            user        = comp.db_usr
            password    = comp.db_pass
            #print (host,database,user,password)
            
            #conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';UID='+user+';PWD='+ password + ';TrustServerCertificate=yes')
            conn        = pymssql.connect(host=host, user=user, password=password, database=database)
            #cursor = conn.cursor(as_dict=True)
            
            #cursor.execute( "exec [dbo].[IGU_LR_PERITEM] '" +  self.datefrom.strftime("%Y%m%d") + "', '" +  self.dateto.strftime("%Y%m%d") + "','"+ comp.code_base + "'")
            msg_sql     = "exec [dbo].[IGU_LR_PERITEM] '" +  self.datefrom.strftime("%Y%m%d") + "', '" +  self.dateto.strftime("%Y%m%d") + "','"+ partner + "','"+ item + "','"+ comp.code_base + "'"
            msg_sql     = """
                                declare 
                                    @DateFrom varchar(10) ,
                                    @dateTo varchar(10) ,
                                    @partner varchar(50),
                                    @item varchar(50) ,
                                    @company varchar(50) 

                                set @DateFrom  ='""" +  self.datefrom.strftime("%Y%m%d") + """'
                                set @DateTo = '""" +  self.dateto.strftime("%Y%m%d") + """'
                                set @partner = '""" +  partner + """'
                                set @item ='""" + item + """'
                                set @company ='""" + comp.name + """'

                                select 
                                        @company company, 
                                        imonth,
                                        iyear,  
                                        cardcode,
                                        cardname ,
                                        shiptocode,
                                        groupname , 
                                        U_Group1 , 
                                        salesperson,
                                        salesgroup,
                                        itemcode ,
                                        itemname,
                                        uom,
                                        product_group , 
                                        product_subgroup, 
                                        hscode,
                                        SpeGroup, 
                                        sum(quantity) quantity, 
                                        sum(total) total,
                                        sum(margin)margin ,
                                        0 percents

                                from 
                                (
                                select  
                                        'Indoguna Utama' company, 
                                        substring(convert(varchar,a.docdate,112) ,5,2) imonth,
                                        left(convert(varchar,a.docdate,112) ,4) iyear,  
                                        b.cardcode,
                                        b.cardname ,
                                        a.shiptocode,
                                        
                                        c.groupname , 
                                        c.U_Group1,
                                        e.slpname salesperson,
                                        e.memo salesgroup,
                                        g.itemcode ,
                                        '['+ g.itemcode + '] '+ g.itemname as itemname,
                                        g.InvntryUom uom,
                                        g.U_Group product_group , 
                                        g.U_SubGroup product_subgroup, 
                                        isnull(convert(varchar,g.u_hs_Code),'') HSCode,
                                        g.u_speGroup SpeGroup, 
                                        sum( f.quantity) quantity , 
                                        sum( f.linetotal - case f.linetotal when 0 then 0 else   ((f.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) end )  total,
                                        sum( f.GrssProfit ) margin  

                                from oinv (nolock) a 
                                    inner join ocrd (nolock) b on a.cardcode = b.cardcode 
                                    inner join ocrg (nolock) c on b.GroupCode =c.GroupCode 
                                    inner join oslp (nolock) d on a.slpcode = d.slpcode
                                    inner join oslp (nolock) e on b.slpcode = e.slpcode
                                    inner join inv1 (nolock) f on a.docentry = f.docentry 
                                    inner join oitm (nolock) g on f.itemcode = g.itemcode
                                    inner join OWHS (nolock) h on f.whscode = h.whscode
                                where 
                                    a.canceled = 'N' and ( a.doctotal -a.vatsum+a.DiscSum)<>0 
                                    AND CONVERT(VARCHAR,A.DOCDATE,112) between @DateFrom and @dateTo 
                                    and  a.doctotal -a.vatsum+a.DiscSum <>0
                                    and c.groupname + b.cardcode + isnull(b.cardname,'') like '%' + isnull(@partner,'%') + '%'
                                    and g.U_Group + isnull(g.U_SubGroup,'')  + g.itemcode +  g.itemname like '%' + isnull(@item,'%') + '%'
                                group by  
                                        substring(convert(varchar,a.docdate,112) ,5,2)  ,
                                        left(convert(varchar,a.docdate,112) ,4)  ,  
                                        b.cardcode,
                                        b.cardname ,
                                        a.shiptocode,
                                        c.groupname ,  
                                        c.U_Group1,
                                        g.u_speGroup , 
                                        e.slpname ,
                                        e.memo  ,
                                        g.itemcode ,
                                        '['+ g.itemcode + '] '+ g.itemname    ,
                                        g.InvntryUom  ,
                                        g.U_Group   , 
                                        g.U_SubGroup  ,isnull(convert(varchar,g.u_hs_Code),'') ,
                                        g.u_speGroup  
                                union all
                                select  
                                        'Indoguna Utama' company, 
                                        substring(convert(varchar,a.docdate,112) ,5,2) imonth,
                                        left(convert(varchar,a.docdate,112) ,4) iyear,  
                                        b.cardcode,
                                        b.cardname ,
                                        a.shiptocode,
                                        c.groupname ,  
                                        c.U_Group1,
                                        e.slpname salesperson,
                                        e.memo salesgroup,
                                        g.itemcode ,
                                        '['+ g.itemcode + '] '+ g.itemname as itemname,
                                        g.InvntryUom uom,
                                        g.U_Group product_group , 
                                        g.U_SubGroup product_subgroup, isnull(convert(varchar,g.u_hs_Code),'') ,
                                        g.u_speGroup SpeGroup, 
                                        -1 * sum( f.quantity) quantity , 
                                        -1 * sum( f.linetotal - case f.linetotal when 0 then 0 else   ((f.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) end )  total,
                                        -1 * sum( f.GrssProfit ) margin 
                                        

                                from orin (nolock) a 
                                    inner join ocrd b (nolock) on a.cardcode = b.cardcode 
                                    inner join ocrg c (nolock) on b.GroupCode =c.GroupCode 
                                    inner join oslp d (nolock) on a.slpcode = d.slpcode
                                    inner join oslp e (nolock) on b.slpcode = e.slpcode
                                    inner join rin1 f (nolock) on a.docentry = f.docentry 
                                    inner join oitm g (nolock) on f.itemcode = g.itemcode
                                    inner join OWHS h (nolock) on f.whscode = h.whscode
                                where a.canceled = 'N' --and ( a.doctotal -a.vatsum+a.DiscSum)<>0  
                                    AND CONVERT(VARCHAR,A.DOCDATE,112) between @DateFrom and @dateTo
                                    and c.groupname + b.cardcode + isnull(b.cardname,'') like '%' + isnull(@partner,'%') + '%'
                                    and g.U_Group + isnull(g.U_SubGroup,'')  + g.itemcode +  g.itemname like '%' + isnull(@item,'%') + '%'
                                    --and  a.doctotal -a.vatsum+a.DiscSum <>0
                                group by  
                                        b.cardcode,
                                        b.cardname ,
                                        a.shiptocode,
                                        c.groupname ,  
                                        c.U_Group1,
                                        e.slpname ,
                                        e.memo  ,
                                        substring(convert(varchar,a.docdate,112) ,5,2)  ,
                                        left(convert(varchar,a.docdate,112) ,4)  ,  
                                        g.itemcode ,
                                        '['+ g.itemcode + '] '+ g.itemname    ,
                                        g.InvntryUom  ,
                                        g.U_Group   , 
                                        g.U_SubGroup  ,isnull(convert(varchar,g.u_hs_Code),'') ,
                                        g.u_speGroup 
                                )as a 
                                group by Company, 
                                        imonth,
                                        iyear,  cardcode,
                                        cardname ,
                                        shiptocode,
                                        groupname , 
                                        U_Group1,
                                          salesperson,
                                        salesgroup,SpeGroup,
                                        itemcode ,
                                        itemname,
                                        uom,
                                        product_group , 
                                        product_subgroup,
                                        hsCode,
                                        speGroup
                                            
            
            """

            data        = pandas.io.sql.read_sql(msg_sql,conn)
            listfinal.append(data)


 
        #print (listfinal)
#        df = pd.DataFrame.from_records(listfinal,columns=label,coerce_float=True)
        #df = pd.DataFrame.from_dict(listfinal)
        df = pd.concat(listfinal)
        df.to_excel(mpath + '/temp/'+ filename ,index=False)  
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

 