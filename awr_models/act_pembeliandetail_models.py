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


class CNW_PEMBELIANDETAIL(models.TransientModel):
    _name           = "cnw.awr28.pembeliandetail"
    _description    = "cnw.pembeliandetail"
    company_id      = fields.Many2many('res.company', string="Company",required=True)
    
    datefrom        = fields.Date ("Date From", default=fields.Date.today())
    dateto          = fields.Date ("Date To", default=fields.Date.today()) 
    filexls         = fields.Binary("File Output")    
    filenamexls     = fields.Char("File Name Output")
    
    @api.multi
    def view_pembeliandetail(self): 
        mpath       = get_module_path('cnw_awr28')
        filename    = 'pembelian_'+   self.dateto.strftime("%Y%m%d")  + '.xlsx'
        filepath    = mpath + '/temp/'+ filename
        listfinal = []
        erptype = 1
        for comp in self.company_id:
            host        = comp.server
            database    = comp.db_name
            user        = comp.db_usr
            password    = comp.db_pass
            print (host,database,user,password)
            
            #conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';UID='+user+';PWD='+ password + ';TrustServerCertificate=yes')
            conn = pymssql.connect(host=host, user=user, password=password, database=database)
            cursor = conn.cursor()
            
            cursor.execute( "exec [dbo].[IGU_ACT_PEMBELIANDETAIL] '" +  self.datefrom.strftime("%Y%m%d") + "', '" +  self.dateto.strftime("%Y%m%d") + "','" + comp.code_base +"'")

            rowdata = cursor.fetchall()  
            listfinal += rowdata
            if comp.erp_type =="tradeerp":
                erptype=2
                
        label=["Company",
                "TransNum",
                "Trans Type",
                "CreatedBy",
                "base_ref",
                "docnum",
                "Canceled",
                "NumAtCard",
                "Comments",
                "U_IGU_PIBNo",
                "U_IGU_PIB_Nop",
                "U_PI_No",
                "U_Container",
                "u_vessel",
                "docdate",
                "imonth",
                "cardcode",
                "cardname",
                "groupname",
                "U_group",
                "U_subgroup",
                "HSCode",
                "U_spegroup",
                "itemcode",
                "dscription",
                "quantity",
                "doccur",
                "docrate",
                "price",
                "calcprice",
                "transvalue",
                "Transaction Name", 
                ]
        label2=["Company",
                "rcv_No",
                "rcv_POCNo",
                "rcv_DtRcvQty",
                "imonth",
                "iyear",
                "rcv_Supplier",
                "Supplier",
                "spl_NationCode",
                "rcv_Remark",
                "rcv_SJNo",
                "rcv_BLNo",
                "rcv_BookingNo",
                "rcv_ContainerNo",
                "rcv_LCNo",
                "rcv_CurrCode",
                "rcv_CurRate",
                "rcv_Material",
                "ITEMNAME",
                "GETGROUP",
                "rcv_InQty",
                "rcv_UPrice",
                "rcv_currAmt",
                "rcv_InAmount",
                "biaya_per_item",
                "pembelian_plus_biaya", 
                ]
        #print (listfinal)
        if erptype ==1:
            df = pd.DataFrame.from_records(listfinal,columns=label,coerce_float=True)
        else:
            df = pd.DataFrame.from_records(listfinal,columns=label2,coerce_float=True)

        df.to_excel(mpath + '/temp/'+ filename )  
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

 