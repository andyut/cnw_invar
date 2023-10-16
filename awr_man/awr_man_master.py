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


class AWR_MAN_MASTER(models.Model):
    _name           = "awr.man.setting"
    _description    = "awr.man.setting"
    name            = fields.Char("Name")
    itype           = fields.Selection([('pl','PL') ,
                                        ('bs','BS') ,],default="pl")
    iheader         = fields.Char("Header")
    idetail         = fields.Char("Detail")
    



class AWR_MAN_MASTER(models.Model):
    _name           = "awr.man.master"
    _description    = "awr.man.master"
    name            = fields.Char("Name")
    itype           = fields.Selection([('pl','PL') ,
                                        ('bs','BS') ,],default="pl")
    iyear           = fields.Selection([ ('2015', '2015'), 
                                        ('2016', '2016'),
                                        ('2017', '2017'),
                                        ('2018', '2018'),
                                        ('2019', '2019'),
                                        ('2020', '2020'),
                                        ('2021', '2021'),
                                        ('2022', '2022'),
                                        ('2023', '2023'),
                                        ('2024', '2024'),
                                        ('2025', '2025'),
                                        ('2026', '2026'),
                                        ('2027', '2027'),
                                        ('2028', '2028'),
                                        ('2029', '2029'),
                                        ('2030', '2030') ,
                                        ],string='Year',required=True )
    
    
    
class AWR_MAN_DETAIL(models.Model):
    _name           = "awr.man.detail"
    _description    = "awr.man.detail"
    company_id      = fields.Many2many('res.company', string="Company",required=True)
       
    iheader         = fields.Char("Header",required=True )
    idetail         = fields.Char("Detail",required=True )
    iyear           = fields.Selection([('2015', '2015'), 
                                        ('2016', '2016'),
                                        ('2017', '2017'),
                                        ('2018', '2018'),
                                        ('2019', '2019'),
                                        ('2020', '2020'),
                                        ('2021', '2021'),
                                        ('2022', '2022'),
                                        ('2023', '2023'),
                                        ('2024', '2024'),
                                        ('2025', '2025'),
                                        ('2026', '2026'),
                                        ('2027', '2027'),
                                        ('2028', '2028'),
                                        ('2029', '2029'),
                                        ('2030', '2030'),
                                        ],string='Year',required=True )

    jan             = fields.Float("Jan",default=0)
    feb             = fields.Float("feb",default=0)
    mar             = fields.Float("mar",default=0)
    apr             = fields.Float("apr",default=0)
    mei             = fields.Float("mei",default=0)
    jun             = fields.Float("jun",default=0)
    jul             = fields.Float("jul",default=0)
    ags             = fields.Float("ags",default=0)
    sep             = fields.Float("sep",default=0)
    okt             = fields.Float("okt",default=0)
    nov             = fields.Float("nov",default=0)
    des             = fields.Float("des",default=0)
    total           = fields.Float("Total per Year",default=0)

      