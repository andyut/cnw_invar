# -*- coding: utf-8 -*-
from odoo import models, fields, api
 
class CNW_HOME(models.Model):
    _name           = "cnw.awr28.home"
    _description    = "cnw.awr28.home"
    name            = fields.Char ("Name",default="Home") 
 
    