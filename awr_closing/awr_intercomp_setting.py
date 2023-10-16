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
 

class AWR_InterCompSetting(models.Model):
    _name           = "cnw.intercomp.setting"
    _description    = "cnw.intercomp.setting"
    
    name            = fields.Char("Name")
    codename        = fields.Char("Code Name")
    npwp            = fields.Char("NPWP")
    nourut          = fields.Char("No Urut")
    company         = fields.Char("Company")
    dbname          = fields.Char("DB Name")
    host            = fields.Char("Host")
    dbuser          = fields.Char("DB User")
    dbpass          = fields.Char("Pass")

