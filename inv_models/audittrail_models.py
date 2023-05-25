# -*- coding: utf-8 -*-

from odoo import models, fields, api
import base64
import pymssql

class ARAuditTrail(models.Model):
    _name           = "cnw.so.audittrail"
    _order			="id desc"
    _description    = "Invoice Home Menu"
    company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
    name            = fields.Char("audittrail Number")
    sonumber        = fields.Char("SO Number")
    cardcode        = fields.Char("Card Code")
    cardname        = fields.Char("Card Name")
    sales           = fields.Char("Sales Person")
    arperson        = fields.Char("AR Person")
    docref          = fields.Char("Doc Reference Number")
    docdate         = fields.Date("Document Date")
    doctype         = fields.Char("Document Type")
    position        = fields.Char("Teams / Groups")
    docstatus       = fields.Char("Status")
    docby           = fields.Char("Act By")
    docindate       = fields.Datetime("Act Date")
    notes           = fields.Char("Notes")
