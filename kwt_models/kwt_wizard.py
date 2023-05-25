# -*- coding: utf-8 -*-

from odoo import models, fields, api
import base64
import pymssql
from datetime import datetime 
import pytz



class CNW_INVOICE_KWITANSI_WIZARD(models.TransientModel):
    _name           = "cnw.invoice.kwitansi.wizard"
    _description    =  "cnw.invoice.kwitansi.wizard "
    company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)

    def _getkwitansiNumber(self): 
        return self.env["ir.sequence"].next_by_code("cnw.invoice.kwitansi")

    name            = fields.Char("Kwitansi No",default=_getkwitansiNumber)
    docdate         = fields.Date("Checked Date",default=lambda s:fields.Date.today(), required=True) 
    cardcode        = fields.Char("Card Code")
    cardname        = fields.Char("Card Name")
    arperson        = fields.Char("AR Person")
    salesperson     = fields.Char("Sales Person")
    address1        = fields.Char("Address")
    creator         = fields.Char("Creator")

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


    def _getcalculation(self): 
        invoicelist = self.env['ar.invoice'].browse(self._context.get('active_ids', []))
        docftotal = 0.0
        for invoice in invoicelist: 
            docftotal += invoice.total
        return docftotal    
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

    amount          = fields.Float("Total",digit=(19,2),default=_getcalculation)
    terbilang       = fields.Char("Terbilang")
    notes           = fields.Char("Notes") 

    @api.onchange("amount")
    def hitungTerbilang(self):
        self.terbilang = self._getterbilang()

    def get_kwitansi(self):
        invoice = self.env['ar.invoice'].browse(self._context.get('active_ids', []))
  
        self.name = self.env["ir.sequence"].next_by_code("cnw.invoice.kwitansi")
        linv = len(invoice)
        idx = 0

        host        = self.env.user.company_id.server
        database    = self.env.user.company_id.db_name
        user        = self.env.user.company_id.db_usr
        password    = self.env.user.company_id.db_pass

        conn = pymssql.connect(host=host, user=user, password=password, database=database)        
        cursor = conn.cursor()
            
               
        
        for inv in invoice:
            inv.act_checked = True
            idx +=1
            inv.act_status = "Kwitansi by "  + self.env.user.name
            inv.act_statusdt = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S") 
            inv.act_notes = self.notes
            self.address1 = inv.address
            inv.kwitansi = self.name
            self.cardcode  = inv.cardcode 
            self.cardname = inv.cardname 
            self.arperson = inv.arperson 
            self.salesperson = inv.salesperson 
            if linv <= 3 :
                if idx ==1 :
                    self.invoiceso1 = inv.numatcard  
                    self.invoicedate1 = inv.docdate.strftime("%Y-%m-%d")
                    self.invoiceint1 = inv.docnum 
                    self.invoicetotal1 = "{0:,.2f}".format(inv.total)
                if idx ==2 :
                    self.invoiceso2 = inv.numatcard  
                    self.invoicedate2 = inv.docdate.strftime("%Y-%m-%d")
                    self.invoiceint2 = inv.docnum 
                    self.invoicetotal2 = "{0:,.2f}".format(inv.total) 
                if idx ==3 :
                    self.invoiceso3 = inv.numatcard   
                    self.invoicedate3 = inv.docdate.strftime("%Y-%m-%d")
                    self.invoiceint3 = inv.docnum 
                    self.invoicetotal3 = "{0:,.2f}".format(inv.total) 
            else :
                    self.invoiceso1 = "Perincian Terlampir" 
        
            msgsql = """ UPDATE oinv
                            set u_kw_no ='""" + self.name + """' ,
                                u_kw_printDate = '""" + self.docdate.strftime("%Y-%m-%d")  + """'
                        from oinv a
                         where a.docnum = '""" + inv.docnum + """'  
                    """     
            cursor.execute(msgsql)
            conn.commit()


        conn.close()
        invlist = []

        invlist.append(self.name)
        invlist.append(self.name)
        invlist.append(self.docdate)
        invlist.append(self.cardcode)
        invlist.append(self.cardname)
        invlist.append(self.arperson)
        invlist.append(self.salesperson)
        invlist.append(self.amount)
        invlist.append(self._getterbilang())
        invlist.append(self.notes) 

        invlist.append(self.invoiceso1)
        invlist.append(self.invoicedate1)
        invlist.append(self.invoiceint1)
        invlist.append(self.invoicetotal1)
        invlist.append(self.invoiceso2)
        invlist.append(self.invoicedate2)
        invlist.append(self.invoiceint2)
        invlist.append(self.invoicetotal2)
        invlist.append(self.invoiceso3)
        invlist.append(self.invoicedate3)
        invlist.append(self.invoiceint3)
        invlist.append(self.invoicetotal3)

        invlist.append(self.address1)
        iv =[]
        iv.append(invlist)
        #print(iv)
        self.env["cnw.invoice.kwitansi"].load(["id",
                                                    "name",
                                                    "docdate",
                                                    "cardcode",
                                                    "cardname",
                                                    "arperson",
                                                    "salesperson",
                                                    "amount",
                                                    "terbilang",
                                                    "notes",
                                                    "invoiceso1",
                                                    "invoicedate1",
                                                    "invoiceint1",
                                                    "invoicetotal1",
                                                    "invoiceso2",
                                                    "invoicedate2",
                                                    "invoiceint2",
                                                    "invoicetotal2",
                                                    "invoiceso3",
                                                    "invoicedate3",
                                                    "invoiceint3",
                                                    "invoicetotal3",
                                                    "address1",
                                                    ],iv)
        return {
            "type": "ir.actions.act_window",
            "res_model": "cnw.invoice.kwitansi",  
            #"view_id":view_do_list_tree, 
            "view_mode":"tree,form",
            "act_window_id":"cnw_invoice_kwitansi_action", 
            "domain": [("name", "=",self.name) ,],}                        

