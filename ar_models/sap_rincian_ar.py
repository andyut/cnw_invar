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


class SAPRincianAR(models.TransientModel):
    _name           = "sap.rincianar"
    _description    = "sap.rincianar"
    company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
    datefrom        = fields.Date ("Date From", default=fields.Date.today())
    dateto          = fields.Date ("Date To", default=fields.Date.today())
    partner         = fields.Char("Partner Code /Name",default="") 
    item            = fields.Char("Items",default="bk-ap") 
    filexls         = fields.Binary("File Output")    
    filenamexls     = fields.Char("File Name Output")
    
    @api.multi
    def view_rincianar_xls(self): 
        mpath       = get_module_path('cnw_invar')
        filename    = 'rincian_ar_' + self.env.user.company_id.code_base + "_" +  self.datefrom.strftime("%Y%m%d")  +'_'+  self.dateto.strftime("%Y%m%d")  + '.xlsx'
        filepath    = mpath + '/temp/'+ filename

        host        = self.env.user.company_id.server
        database    = self.env.user.company_id.db_name
        user        = self.env.user.company_id.db_usr
        password    = self.env.user.company_id.db_pass
        
        conn = pymssql.connect(host=host, user=user, password=password, database=database)

        workbook = xlsxwriter.Workbook(filepath)
        workbook.formats[0].set_font_size(8)
        workbook.formats[0].set_font_name("Arial")

        money_format = workbook.add_format({'num_format': '#,##0.00',
                                                'font_size':8,
                                                'font_name':'Arial'}) 
        header_format = workbook.add_format({'bold': True, 
                                            'valign': 'top',
                                            'align': 'right',
                                            'font_size':16, 
                                            'font_name':'Arial',})        
        header_format2 = workbook.add_format({'bold': True, 
                                            'valign': 'top',
                                            'align': 'right',
                                            'font_size':10, 
                                            'font_name':'Arial',})        


        worksheet = workbook.add_worksheet()

        worksheet.write(0,0, "Printed at  " + datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S"))
        

        cursor = conn.cursor()
        
        partner = self.partner if self.partner else ""
        item = self.item if self.item else ""

        cursor.execute( "exec dbo.IGU_RINCIAN_AR  '"+  self.datefrom.strftime("%Y%m%d") + "','"+  self.dateto.strftime("%Y%m%d") + "','" + partner + "','" + item + "','1'" )

        rowdata = cursor.fetchall() 
        print("Row Data")
        print ("exec dbo.IGU_RINCIAN_AR  '"+  self.datefrom.strftime("%Y%m%d") + "','"+  self.dateto.strftime("%Y%m%d") + "','" + partner + "','" + item + "','1'" )
        row         = 5
        col         = 0 
        total_line  = 0

        for detail in rowdata:
            col = 0 
            total_line = len(detail)
            for col in range(len(detail)):
                worksheet.write(row,col,(detail[col]))
                col+=1 
            row+=1
            print ("Length detail : ")
            print(total_line)
        
        worksheet.write(0,total_line-1, self.env.user.company_id.name,header_format2)
        worksheet.write(1,total_line-1, "Rincian AR",header_format)
        worksheet.write(2,total_line-1, "From " + self.datefrom.strftime("%Y%m%d") + " To " + self.dateto.strftime("%Y%m%d") ,header_format2)

        worksheet.add_table(4,0,row,total_line-1, {
                                                    'autofilter': 1,  
                                                    'total_row': 1,
                                                    'columns': [{'header': 'Type'},
                                                                {'header': 'Internal Number'},
                                                                {'header': 'SO Number'},
                                                                {'header': 'Customer Ref'},
                                                                {'header': 'Doc Source'},
                                                                {'header': 'Faktur Pajak'},
                                                                {'header': 'Kwitansi'},
                                                                {'header': 'Date'},
                                                                {'header': 'Customer Group'},
                                                                {'header': 'Customer Name'},
                                                                {'header': 'Shipping'},
                                                                {'header': 'Month'},
                                                                {'header': 'Year'},
                                                                {'header': 'Product'},
                                                                {'header': 'Qty Order', 'total_function': 'sum'},
                                                                {'header': 'Qty Delivery', 'total_function': 'sum'},
                                                                {'header': 'Qty Invoice', 'total_function': 'sum'},
                                                                {'header': 'Price', 'total_function': 'sum'},
                                                                {'header': 'PPn', 'total_function': 'sum'},
                                                                {'header': 'Dpp', 'total_function': 'sum'},]})

        conn.close()
        workbook.close()     

        # Save to Model.Binary 
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


        
 