# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CNWUseresGroup(models.Model):
    _inherit    ="res.users"
    cnw_sap_salesgroup      = fields.Char("Sales Group",defaults="HOREKA")
    cnw_sap_sales           = fields.Char("SAP SALES")
