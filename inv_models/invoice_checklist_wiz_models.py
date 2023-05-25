# -*- coding: utf-8 -*-

from odoo import models, fields, api
import base64
import pymssql




class CNW_INVOICE_CHECKLIST(models.TransientModel):
    _name           = "cnw.invoice.checklist"
    _description    =  "cnw.invoice.checklist "
    company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
    checklist_date  = fields.Datetime("Checked Date",default=lambda s:fields.Datetime.now(), required=True) 
    notes           = fields.Char("Notes") 

    def check_list(self):
        invoice = self.env['ar.invoice'].browse(self._context.get('active_ids', []))
  
 

        for inv in invoice:
            inv.act_checked = True
            inv.act_status = "By "  + self.env.user.name
            inv.act_statusdt = self.checklist_date
            inv.act_notes = self.notes

            self.env["cnw.so.audittrail"].create({
                                                "sonumber":inv.numatcard,
                                                "cardcode":inv.cardcode,
                                                "cardname":inv.cardname, 
                                                "sales":inv.salesperson,
                                                "arperson":inv.arperson,
                                                "docref":inv.docnum,
                                                "docdate":inv.docdate,
                                                "doctype":"INVOICE",
                                                "position":"INVOICE",
                                                "docstatus":"invoice Checklist",
                                                "docby":self.env.user.name ,
                                                "docindate":self.checklist_date})