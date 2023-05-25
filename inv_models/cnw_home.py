# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SAPARHome(models.Model):
    _name           = "cnw.home"
    _description    = "CNW Executive home"
    name = fields.Char("Home0001", readonly="1")

