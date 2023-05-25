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




class CNWTfBK(models.TransientModel):
    _name           = "cnw.invar.tfbk"
    _description    = "Lap Tukar Faktur BK"
    company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)

    datefrom        = fields.Date("Date from",default=lambda s:fields.Date.today())
    dateto          = fields.Date("Date To",default=lambda s:fields.Date.today())
    customer        = fields.Char("Business Partner",default="")
    filexls         = fields.Binary("File Output")    
    filenamexls     = fields.Char("File Name Output")
    
    export_to       = fields.Selection([ ('xls', 'Excel') ],string='Export To', default='xls')

    def getTFBK(self):

#PATH & FILE NAME & FOLDER
        mpath       = get_module_path('cnw_invar')
        filenamexls2    = 'TFBK_'+   self.dateto.strftime("%Y%m%d")  + '.xlsx'
        filenamepdf    = 'TFBK_'+   self.dateto.strftime("%Y%m%d")  + '.pdf'
        filepath    = mpath + '/temp/'+ filenamexls2

 
#MULTI COMPANY 

        listfinal = []
        pandas.options.display.float_format = '{:,.2f}'.format
        for comp in self.company_id:

            host        = comp.server
            database    = comp.db_name
            user        = comp.db_usr
            password    = comp.db_pass 
            
            conn = pymssql.connect(host=host, user=user, password=password, database=database)
            bp = self.customer if self.customer else ""

            msgsql ="""
                            declare @table table ( idx int identity (1,1) , TRANSID int )

                            declare @datefrom varchar(10) ,@dateto varchar(10)   , @partner varchar(50) , @kwtno varchar(50)


                            set @datefrom ='""" +  self.datefrom.strftime("%Y%m%d") + """'
                            set @dateto = '""" +  self.dateto.strftime("%Y%m%d") + """'
                            set @partner = '""" +  bp + """'
                            set @kwtno = ''


                            SELECT 
                                    isnull(a.U_Kw_No,'-') kwitansi ,
                                    a.NumAtCard 'Invoice / SO Number',
                                    isnull(a.U_IDU_FPajak,'') FakturPajak ,
                                    cast( format(a.docdate,'dd-MMM-yy') as varchar)  invoiceDate,
                                    isnull(a.U_Cust_PO_No,'') PO ,
                                    isnull(a.U_Cust_PO_No,'') GR ,
                                    c.Address Store,
                                    c.U_Bill_Area Store_Code ,
                                    a.DocTotal Amount ,
                                    '430' VendorCode,
                                    isnull(c.U_Bill_Area,'BK') + 'GR' +  isnull(a.U_Cust_PO_No,'') 'Detail GR',
                                    D.Dscription REMARKS
                            FROM OINV A 
                            INNER JOIN OCRD B ON A.CARDCODE = B.CardCode
                            INNER JOIN INV1 D ON A.DOCENTRY  = D.DocEntry 
                            left outer join crd1 c on a.ShipToCode = c.address and b.cardcode = c.cardcode and c.AdresType ='S'

                            WHERE CONVERT(VARCHAR,A.DOCDATE,112) BETWEEN @DATEFROM AND @dateto
                            AND B.CARDCODE + B.CARDNAME LIKE '%' + ISNULL(@PARTNER,'') + '%'            
            """
            data = pandas.io.sql.read_sql(msgsql,conn) 
            listfinal.append(data)
  
        


        df = pd.concat(listfinal) 

        if self.export_to =="xls":
            filename = filenamexls2 
            #report = df.groupby(["Group","AR Person"]).sum()
            df.to_excel(mpath + '/temp/'+ filenamexls2,index=False,engine='xlsxwriter') 
        
        
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

 