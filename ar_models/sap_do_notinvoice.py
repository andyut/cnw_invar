# -*- coding: utf-8 -*-
import requests 
import xlsxwriter
import os
import pytz
from odoo.exceptions import UserError
from odoo.modules import get_modules, get_module_path
from datetime import datetime
from odoo import models, fields, api
import base64
import pymssql


class SAPDOBelumInvoice(models.TransientModel):
    _name           = "sap.belumfaktur"
    _description    = "sap.belumfaktur"
    company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
    dateto          = fields.Date ("Date To", default=lambda s:fields.Date.today())
    partner         = fields.Char("Business Partner",default=" ") 
    arperson        = fields.Char("AR Person",default="")
    tukarfaktur     = fields.Char("Jadwal Tukar Faktur",default="")
    export_to       = fields.Selection([ ('Summary', 'Summary'),
											('Items', 'Items'), ],string='Export To', default='Summary')    
    filexls         = fields.Binary("File Output")    
    filenamexls     = fields.Char("File Name Output")


    @api.multi
    def view_belumfaktur_xls(self): 
        #PATH FILE 
        mpath       = get_module_path('cnw_invar')
        filename    = 'OpenDO_' + self.env.user.company_id.code_base + "_"   + self.dateto.strftime("%Y%m%d")   + '.xlsx'
        filepath    = mpath + '/temp/'+ filename

        #SERVER CONFIGURATION
        host        = self.env.user.company_id.server
        database    = self.env.user.company_id.db_name
        user        = self.env.user.company_id.db_usr
        password    = self.env.user.company_id.db_pass

        partner = self.partner if self.partner else ""
        arperson = self.arperson if self.arperson else ""
        tukarfaktur = self.tukarfaktur if self.tukarfaktur else "" 

        #EXECUTE STORE PROCEDURE 
        conn = pymssql.connect(host=host, user=user, password=password, database=database)
        if self.export_to=="Summary":
            msgsql =  """
                        declare 
                                @dateto varchar(10) ,
                                @partner varchar(50) , 
                                @arperson varchar(50) ,
                                @tfnotes varchar(50)

                        set @dateto ='"""+  self.dateto.strftime("%Y%m%d") + """'
                        set @partner ='"""  + partner + """'
                        set @arperson ='"""  + arperson + """'
                        set @tfnotes ='"""  + tukarfaktur + """'           
                            SELECT DISTINCT 
                                    @dateto 'Date To',
                                    T0.DOCENTRY ,
                                    T3.DOCSTATUS, 
                                    CONVERT(vARCHAR,T1.docduedate,112) DOCDATE,
                                    CONVERT(vARCHAR,T3.DOCDATE,112) POTONGSTOCK,
                                    t3.docnum,
                                    T2.BEGINSTR+ CONVERT(VARCHAR,T1.DOCNUM) DO_NUMBER ,
                                    T1.CARDCODE, 
                                    T1.SHIPTOCODE , 
                                    t6.groupname memo,
                                    T1.CARDNAME ,
                                    T3.NUMATCARD,
                                    T4.U_SlsEmpName, 
                                    T3.DocTotal,
                                    T1.COMMENTS  ,
                                    isnull(t5.Notes,'') TF
                            FROM DLN1 T0 
                                INNER JOIN ORDR T1 ON T0.BASEENTRY = T1.DOCENTRY AND T0.BASETYPE=17 
                                INNER JOIN OCRD T5 ON T1.cardcode = t5.cardcode 
                                INNER JOIN OCRG T6 ON T5.groupcode = t6.groupcode 
                                INNER JOIN OSLP  T4 ON T5.SlpCode=T4.SlpCode
                                INNER JOIN NNM1 T2 ON T1.[Series] = T2.[Series] AND T0.[TargetType] not in (13,15)
                                INNER JOIN ODLN T3 ON T0.DOCENTRY = T3.DOCENTRY 
                            WHERE   
                                    T1.CARDCODE + ISNULL(T1.SHIPTOCODE ,'') + ISNULL(T1.CARDNAME,'')   LIKE '%'+ isnull(replace(@partner ,' ','%'),'')+ '%'
                                AND T3.DOCSTATUS ='O'
                                AND CONVERT(VARCHAR,T1.docduedate,112)>='20161231'
                                and CONVERT(VARCHAR,T1.docduedate,112)<=@dateto    
                                AND T5.U_AR_PERSON LIKE '%' + isnull(replace(@arperson ,' ','%'),'') + '%'         
                                AND isnull(T5.notes,'') LIKE '%' + isnull(replace(@tfnotes ,' ','%'),'') + '%'         
            
            """
        else :
            msgsql =  "exec [dbo].[IGU_DO_NOTINVOICE] '" +  self.dateto.strftime("%Y%m%d") + "','" + self.partner +"'"
            msgsql = """
                        declare 
                                @dateto varchar(10) ,
                                @partner varchar(50) ,
                                @arperson varchar(50) ,
                                @tfnotes varchar(50)

                        set @dateto ='"""+  self.dateto.strftime("%Y%m%d") + """'
                        set @partner ='"""  + partner + """'
                        set @arperson ='"""  + arperson + """'
                        set @tfnotes ='"""  + tukarfaktur + """'
                            SELECT DISTINCT 
                                    @dateto 'Date To',
                                    T0.DOCENTRY ,
                                    T3.DOCSTATUS, 
                                    CONVERT(vARCHAR,T1.DOCDATE,112) DOCDATE,
                                    t3.docnum,
                                    T2.BEGINSTR+ CONVERT(VARCHAR,T1.DOCNUM) DO_NUMBER ,
                                    T1.CARDCODE, 
                                    T1.SHIPTOCODE , 
                                    t6.groupname memo,
                                    T1.CARDNAME ,
                                    T3.NUMATCARD,
                                    T4.U_SlsEmpName, 
                                    T0.itemcode ,
                                    T0.dscription ,
                                    T0.Quantity ,
                                    T0.Price ,
                                    T0.vatgroup,
                                    T0.VATSUM PPn,
                                    T0.linetotal ,
                                     isnull(t5.Notes,'') tf
                            FROM DLN1 T0 
                                INNER JOIN ORDR T1 ON T0.BASEENTRY = T1.DOCENTRY AND T0.BASETYPE=17 
                                INNER JOIN OCRD T5 ON T1.cardcode = t5.cardcode 
                                INNER JOIN OCRG T6 ON T5.groupcode = t6.groupcode 
                                INNER JOIN OSLP  T4 ON T5.SlpCode=T4.SlpCode
                                INNER JOIN NNM1 T2 ON T1.[Series] = T2.[Series] AND T0.[TargetType] not in (13,15)
                                INNER JOIN ODLN T3 ON T0.DOCENTRY = T3.DOCENTRY 
                                
                            WHERE   
                                    T1.CARDCODE + ISNULL(T1.SHIPTOCODE ,'') + ISNULL(T1.CARDNAME,'')   LIKE '%'+ isnull(replace(@partner ,' ','%'),'')+ '%'
                                AND T3.DOCSTATUS ='O'
                                AND CONVERT(VARCHAR,T3.docdate,112)>='20161231'
                                and CONVERT(VARCHAR,T3.docdate,112)<=@dateto  
                                AND T5.U_AR_PERSON LIKE '%' + isnull(replace(@arperson ,' ','%'),'') + '%'         
                                AND isnull(T5.notes,'') LIKE '%' + isnull(replace(@tfnotes ,' ','%'),'') + '%'   
                                    
            """
        cursor = conn.cursor()
        
        cursor.execute(msgsql)

        rowdata = cursor.fetchall() 


        workbook = xlsxwriter.Workbook(filepath)
        workbook.formats[0].set_font_size(8)
        workbook.formats[0].set_font_name("Verdana")

        money_format = workbook.add_format({'num_format': '#,##0.00',
                                                'font_size':8,
                                                'font_name':'Verdana'}) 
        header_format = workbook.add_format({'bold': True, 
                                            'valign': 'top',
                                            'align': 'right',
                                            'font_size':16, 
                                            'font_name':'Verdana',})        
        header_format2 = workbook.add_format({'bold': True, 
                                            'valign': 'top',
                                            'align': 'right',
                                            'font_size':10, 
                                            'font_name':'Verdana',})        


        worksheet = workbook.add_worksheet()
        worksheet.write(0,0, "Printed at  " + datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S"))

        row = 5
        col = 0
        total_line = 0 

        for detail in rowdata:
            col = 0 
            total_line = len(detail)
            for cols in range(len(detail)):
                worksheet.write(row,col,(detail[col]))
                col+=1 
            row+=1

        # TEMPLATE HEADER 
        worksheet.write(0,total_line-1, self.env.user.company_id.name,header_format2)
        worksheet.write(1,total_line-1, "DO Belum Jadi Faktur",header_format)
        worksheet.write(2,total_line-1, " Per " + self.dateto.strftime("%Y-%m-%d")  ,header_format2)

        if self.export_to =="Summary":
            worksheet.add_table(4,0,row,total_line-1, {
                                                        'autofilter': 1,  
                                                        'total_row': 1,
                                                        'columns': [{'header': 'Date To'},
                                                                    {'header': 'Internal Number'},
                                                                    {'header': 'Doc Status'},
                                                                    {'header': 'Doc Date'},
                                                                    {'header': 'PotongStock Date'},
                                                                    {'header': 'DocNum'},
                                                                    {'header': 'Do Number'},
                                                                    {'header': 'BP Code'},
                                                                    {'header': 'Outlet'},
                                                                    {'header': 'Memo'},
                                                                    {'header': 'Customer Name'},
                                                                    {'header': 'Customer Ref'},
                                                                    {'header': 'Sales Person'},
                                                                    {'header': 'SO Total','total_function':'sum'},
                                                                    {'header': 'Remarks'},
                                                                    {'header' : 'Jadwal Tukar Faktur'}]}) 


        else:
            worksheet.add_table(4,0,row,total_line-1, {
                                                        'autofilter': 1,  
                                                        'total_row': 1,
                                                        'columns': [{'header': 'Date To'},
                                                                    {'header': 'Internal Number'},
                                                                    {'header': 'Doc Status'},
                                                                    {'header': 'Doc Date'},
                                                                    {'header': 'DocNum'},
                                                                    {'header': 'Do Number'},
                                                                    {'header': 'BP Code'},
                                                                    {'header': 'Outlet'},
                                                                    {'header': 'Memo'},
                                                                    {'header': 'Customer Name'},
                                                                    {'header': 'Customer Ref'},
                                                                    {'header': 'Sales Person'},
                                                                    {'header': 'Item Code'},
                                                                    {'header': 'Description'},
                                                                    {'header': 'Quantity'},
                                                                    {'header': 'Price','qty_function':'sum'},
                                                                    {'header': 'PPn Group'},
                                                                    {'header': 'PPn'},
                                                                    {'header': 'Qty x Price','total_function':'sum'},
                                                                    {'header' : 'Jadwal Tukar Faktur'}]})
        conn.close()
        workbook.close()
        
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

 
         
        
 
