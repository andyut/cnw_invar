# -*- coding: utf-8 -*-

from odoo import models, fields, api
import base64
from datetime import datetime
import pytz
import numpy as np
import pandas as pd
import pandas.io.sql
import pymssql
from odoo.exceptions import UserError
from odoo.modules import get_modules, get_module_path
import base64
from jinja2 import Environment, FileSystemLoader
import pdfkit
import os




class CNW_INVOICE_KWITANSI(models.Model):
    _name           = "cnw.invoice.kwitansi"
    _description    =  "cnw.invoice.kwitansi "
    company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
    name            = fields.Char("Kwitansi No")
    docdate         = fields.Date("Checked Date",default=lambda s:fields.Date.today(), required=True) 
    cardcode        = fields.Char("Card Code")
    cardname        = fields.Char("Card Name")
    arperson        = fields.Char("AR Person")
    salesperson     = fields.Char("Sales Person")
    address1        = fields.Char("Address")
    creator         = fields.Char("Creator")
    terbilang       = fields.Char("Terbilang")
    amount          = fields.Float("Total",digit=(19,2),default=0)
    notes           = fields.Char("Notes") 

    invoiceso1      = fields.Char("invoiceso1")
    invoicedate1     = fields.Char("invoicedate1")
    invoiceint1     = fields.Char("invoiceint1")
    invoicetotal1   = fields.Char("invoicetotal1")

    invoiceso2      = fields.Char("invoiceso2")
    invoicedate2     = fields.Char("invoicedate2")
    invoiceint2     = fields.Char("invoiceint2")
    invoicetotal2   = fields.Char("invoicetotal2")

    invoiceso3      = fields.Char("invoiceso3")
    invoicedate3     = fields.Char("invoicedate3")
    invoiceint3     = fields.Char("invoiceint3")
    invoicetotal3   = fields.Char("invoicetotal3")



    filexls         = fields.Binary("File Output")    
    filenamexls     = fields.Char("File Name Output")
    def _getterbilang(self):

        def Terbilang(bil):
            angka=("","Satu","Dua","Tiga","Empat","Lima","Enam","Tujuh",
                    "Delapan","Sembilan","Sepuluh","Sebelas")
            Hasil =" "
            n = int(bil)
            if n >= 0 and n <= 11:
                Hasil = Hasil + angka[n]
            elif n < 20:
                Hasil = Terbilang(n % 10) + " belas"
            elif n < 100:
                Hasil = Terbilang(n / 10) + " Puluh" + Terbilang(n % 10)
            elif n < 200:
                Hasil = "Seratus" + Terbilang(n - 100)
            elif n < 1000:
                Hasil = Terbilang(n / 100) + " Ratus" + Terbilang(n %100)
            elif n < 2000:
                Hasil = "Seribu" + Terbilang(n-1000)
            elif n < 1000000:
                Hasil = Terbilang(n / 1000) + " Ribu" + Terbilang(n % 1000)
            elif n < 1000000000:
                Hasil = Terbilang(n/1000000) + " Juta" + Terbilang(n % 1000000)
            else:
                Hasil = Terbilang(n / 1000000000) + " Milyar" + Terbilang(n % 1000000000)
            return Hasil
        return Terbilang(self.amount)

    @api.onchange("amount")
    def hitungTerbilang(self):
        self.terbilang = self._getterbilang()



    def print_kwitansi_detail(self):
        mpath       = get_module_path('cnw_invar') 
        filenamepdf    = 'kwitansidetail_'+   self.name  + '.pdf'
        filenamehtml    = 'kwitansidetail_'+   self.name   + '.html'
        filepath    = mpath + '/temp/'+ filenamepdf

        logo        = mpath + '/template/logo'+ self.company_id.code_base + '.png' 
        #cssfile     = mpath + '/template/style.css'        
        options = { 
                    'page-size':'A4',
                    'orientation': 'portrait',
                    }        
        print_date = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")                    

        listfinal = []
        listfinal2 = []
        pandas.options.display.float_format = '{:,.2f}'.format

        host        = self.company_id.server
        database    = self.company_id.db_name
        user        = self.company_id.db_usr
        password    = self.company_id.db_pass 
            
        conn = pymssql.connect(host=host, user=user, password=password, database=database)
        pd.options.display.float_format = '{:,.2f}'.format
        pandas.options.display.float_format = '{:,.2f}'.format
        
        msgsql =  """
                        declare @kwitansi varchar(20),
                                @company varchar(50)
                        set @company  = '""" + self.company_id.code_base +  """'
                        select  @company company,
                                a.numatcard,
                                a.docnum ,
                                convert(varchar,a.docdate,23) docdate,
                                a.u_kw_no kwitansi ,
                                a.u_idu_FPajak  fp,
                            a.doctotal
                        from oinv a where a.u_kw_no ='"""+ self.name + """'        
        """
        print(msgsql)
        data = pandas.io.sql.read_sql(msgsql,conn) 
        listfinal.append(data)
  
        
        conn.commit()

        df = pd.concat(listfinal)  
        kwitansi_detail = df.values.tolist()

        filename = filenamepdf
        env = Environment(loader=FileSystemLoader(mpath + '/kwt_models/'))

        template = env.get_template("kwitansidetail.html")         
        creator = self.creator if self.creator else "admin"    
        #print(kwitansi_detail)
        address1  = self.address1 if self.address1  else ""
        invoice_ttd = self.env.user.company_id.company_code if self.env.user.company_id.company_code else  self.env.user.name
        template_var = {"logo":logo, 
                        "igu_tanggal" :print_date ,
                        "kwitansi_no":self.name,
                        "cardcode":self.cardcode,
                        "docdate":self.docdate.strftime("%Y-%m-%d"),
                        "cardname":self.cardname,
                        "address":address1,
                        "terbilang":self.terbilang,
                        "amount":self.amount, 
                        "creator":invoice_ttd, 
                        "detail" :kwitansi_detail }


        filename = filenamepdf 
        html_out = template.render(template_var) 

         
        pdfkit.from_string(html_out,mpath + '/temp/'+ filename,options=options) 
        
       # SAVE TO MODEL.BINARY 
        file = open(mpath + '/temp/'+ filename , 'rb')
        out = file.read()
        file.close()
        self.filexls =base64.b64encode(out)
        self.filenamexls = filename
        os.remove(mpath + '/temp/'+ filename )
        print("web/content/?model=" + self._name +"&id=" + str(self.id) + "&filename_field=filenamexls&field=filexls&download=true&filename=" + self.filenamexls)
        return {
            'name': 'Report',
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=" + self._name +"&id=" + str(
                self.id) + "&filename_field=filenamexls&field=filexls&download=true&filename=" + self.filenamexls,
            'target': 'new',
            }


    def print_kwitansi(self):
        mpath       = get_module_path('cnw_invar') 
        filenamepdf    = 'kwitansi_'+   self.name  + '.pdf'
        filenamehtml    = 'kwitansi_'+   self.name   + '.html'
        filepath    = mpath + '/temp/'+ filenamepdf

#LOGO CSS AND TITLE
        logo        = mpath + '/template/logo'+ self.company_id.code_base + '.png' 
        #cssfile     = mpath + '/template/style.css'        
        options = { 
                    'page-size':'A5',
                    'orientation': 'landscape',
                    }
        options2 = { 
                    'page-size':'A4', 
                    'orientation': 'portrait',
                    }
        print_date = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")
#2008202239


#MULTI COMPANY 
 

        env = Environment(loader=FileSystemLoader(mpath + '/kwt_models/'))
        
        template = env.get_template("kwitansi.html")       
        arperson = self.arperson if self.arperson else 'None'
        invoiceso1 = self.invoiceso1 if self.invoiceso1 else ""
        invoicedate1 = self.invoicedate1 if self.invoicedate1 else ""
        invoiceint1 = self.invoiceint1 if self.invoiceint1 else ""
        invoicetotal1 = self.invoicetotal1 if self.invoicetotal1 else ""

        invoiceso2 = self.invoiceso2 if self.invoiceso2 else ""
        invoicedate2 = self.invoicedate2 if self.invoicedate2 else ""
        invoiceint2 = self.invoiceint2 if self.invoiceint2 else ""
        invoicetotal2 = self.invoicetotal2 if self.invoicetotal2 else ""

        invoiceso3 = self.invoiceso3 if self.invoiceso3 else ""
        invoicedate3 = self.invoicedate3 if self.invoicedate3 else ""
        invoiceint3 = self.invoiceint3 if self.invoiceint3 else ""
        invoicetotal3 = self.invoicetotal3 if self.invoicetotal3 else ""
        invoice_ttd = self.env.user.company_id.company_code if self.env.user.company_id.company_code else  self.env.user.name
        transferto = self.env.user.company_id.rek if self.env.user.company_id.rek else ""
        loc = self.env.user.company_id.loc if self.env.user.company_id.loc else ""
        template_var    = { "company":self.company_id.name, 
                            "logo":logo,
                            "cardcode" :self.cardcode,
                            "cardname" :self.cardname, 
                            "kwt_no":self.name,
                            "terbilang" : self.terbilang,  
                            "datetime" : datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S") , 
                            "remarks" :self.notes , 
                            "amount" :"{0:,.2f}".format(self.amount),  
                            "transferto" :transferto , 
                            "arperson" :arperson, 
                            "location" : loc ,
                            "spv_ttd" :invoice_ttd , 
                            "invoiceso1" :invoiceso1 , 
                            "invoicedate1" :invoicedate1 , 
                            "invoiceint1" :invoiceint1 , 
                            "invoicetotal1" :invoicetotal1 ,
                            "invoiceso2" :invoiceso2, 
                            "invoicedate2" :invoicedate2 , 
                            "invoiceint2" :invoiceint2 , 
                            "invoicetotal2" :invoicetotal2 , 
                            "invoiceso3" :invoiceso3, 
                            "invoicedate3" :invoicedate3 , 
                            "invoiceint3" :invoiceint3 , 
                            "invoicetotal3" :invoicetotal3, 
                            "docdate":self.docdate, }


        html_out = template.render(template_var)
      
        pdfkit.from_string(html_out,mpath + '/temp/'+ filenamepdf,options=options) 
        
       # SAVE TO MODEL.BINARY 
        file = open(mpath + '/temp/'+ filenamepdf , 'rb')
        out = file.read()
        file.close()
        self.filexls =base64.b64encode(out)
        self.filenamexls = filenamepdf
        os.remove(mpath + '/temp/'+ filenamepdf )
        return {
            'name': 'Report',
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=" + self._name +"&id=" + str(
                self.id) + "&filename_field=filenamexls&field=filexls&download=true&filename=" + self.filenamexls,
            'target': 'new',
            }