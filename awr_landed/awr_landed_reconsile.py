# -*- coding: utf-8 -*-
import requests 
import numpy as np
import pandas as pd
import pandas.io.sql
import pytz
from odoo.exceptions import UserError
from odoo.modules import get_modules, get_module_path
from datetime import datetime
from odoo import models, fields, api 
import pyodbc 


class CNW_landedcostReconsile(models.Model):
	_name           = "cnw.awr28.landedrecon"
	_description    = "cnw.awr28.landedrecon"
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
	name            = fields.Char("Name")

	refdate         = fields.Date("Ref Date")
	inumber         = fields.Char("JE Number")
	transno         = fields.Char("Trans Number")
	linememo        = fields.Char("LineMemo")
	debit           = fields.Float("Debit")
	credit          = fields.Float("Credit")
	balscdeb        = fields.Float("Bal Debit")
	balSccred        = fields.Float("Bal Credit")
	


	shortname       = fields.Char("Account Code")
	creditordebit   = fields.Char("codCredit")
	srcObjabs       = fields.Char("Docentry")
	srcobjtyp       = fields.Char("Trans Type")
	transid         = fields.Char("Trans ID")
	transrowid      = fields.Integer("Trans Row ID")
	reconcileamount = fields.Float("Reconsile Amount")


class CNW_landedcostReconsilewiz(models.TransientModel):
	_name           = "cnw.awr28.landedrecon.get"
	_description    = "cnw.awr28.landedrecon.get"
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)

	datefrom        = fields.Date ("Date From", default=fields.Date.today())
	dateto          = fields.Date ("Date To", default=fields.Date.today()) 
	account         = fields.Selection(string=	"Account", selection=[
											("2140001","2140001-BEA MASUK PPNBM"),
											("2140002","2140002-BY. SHIPMENT"),
											("2140003","2140003-BY. RECEIVING"),
											("2140004","2140004-BY. PIB/PNBP"),
											("2140005","2140005-BY. SURVEYOR"),
											("2140006","2140006-BY. FREIGHT"), 
											])
	remarks         = fields.Char("Description")

	def getlanded(self):
		return True