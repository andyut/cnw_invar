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


class AWR_AWR(models.Model):
	_name           = "cnw.awr28.awr"
	_description    = "cnw.awr28.awr"
	company_id		= fields.Many2one('res.company', string="Company",required=True)
	account_id 		= fields.Many2one("cnw.awr28.awr.coa",string="Account")
	name			= fields.Char("Keterangan")
	account			= fields.Char("Account" , related="account_id.name",store=True)
	header			= fields.Char("Header",related="account_id.iparent" ,store=True)
	idate 			= fields.Date("iDate",required=True)
	amount			= fields.Float("Amount",digit=(19,2),default=0)
	
	
class AWR_AWR_COA(models.Model):
	_name           = "cnw.awr28.awr.coa"
	_description    = "cnw.awr28.awr.coa"
	company_id		= fields.Many2many('res.company', string="Company",required=True)
	acctcode 		= fields.Char("Account Code")	
	acctname		= fields.Char("Account Name")
	name			= fields.Char("Name")
	iparent			= fields.Char("Header")