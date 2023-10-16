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
import uuid 

 

class CNW_ARTFPrint(models.TransientModel):
	_name           = "ar.tf.print"
	_description    = "Cetakan Invoice"
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
 
	dateto          = fields.Date("Date To",default=lambda s:fields.Date.today(), required=True)
	arperson        = fields.Char("AR Person",default="",required=True)
	collector 		= fields.Selection(string="Collector",
										selection=[("","All"),
													("YANTO","YANTO"),
													("WAWAN","WAWAN"),
													("JHON","JHON"),
													("IMAM","IMAM"),
													("SUSILO","SUSILO"),
													("IRFAN","IRFAN"),
													("JEFRI","JEFRI"),
													("BIBIT","BIBIT"),
													("FUAD","FUAD"),
													("ILYAS","ILYAS"),
													("FERRY","FERRY"),
													("AFFEN","AFFEN"),
													("BUDI","BUDI"),
													("BAYU","BAYU"),
													("TYO","TYO"),
													("YOHANES","YOHANES"),
													("RIDWAN","RIDWAN"),
													("NO COLLECTOR","NO COLLECTOR"),
													("POS","POS"),
													("AMIR","AMIR"),
													("AMIR","AMIR"), ],default="")
	 
	filexls         = fields.Binary("File Output",default=" ")    
	filenamexls     = fields.Char("File Name Output",default="EmptyText.txt")
	export_to       = fields.Selection([ ('tf','Print TF'),('tfkw', 'Print TF Kwitansi'),],string='Print To', default='tf')
	
	def get_CetakanTF(self):
		collector = self.collector if self.collector else ""
		#url = "http://192.168.250.19:8080/jasperserver/flow.html?_flowId=viewReportFlow&standAlone=true&_flowId=viewReportFlow&ParentFolderUri=%2Freports%2FIGU%2FAR&reportUnit=%2Freports%2FIGU%2FAR%2Finvoice_print_c4_odoo&j_username=jasperadmin&j_password=jasperadmin&decorate=no&prm_datefrom="+ self.datefrom.strftime("%Y-%m-%d")  +"&prm_dateto="+ self.dateto.strftime("%Y-%m-%d")  + "&prm_inv_from=" + self.inv_from  + "&prm_inv_to=" + self.inv_to  + "&prm_ppn=&output=pdf"
		if self.export_to =="tf" :

			url = "http://192.168.250.19:8080/jasperserver/flow.html?_flowId=viewReportFlow&standAlone=true&_flowId=viewReportFlow&ParentFolderUri=%2Freports%2FIGU%2FAR&reportUnit=%2Freports%2FIGU%2FAR%2FTF2&j_username=jasperadmin&j_password=jasperadmin&decorate=no&dateto="+ self.dateto.strftime("%Y%m%d") + "&arperson="+ self.arperson + "&collector=" + collector + "&output=pdf"
		else :
			url = "http://192.168.250.19:8080/jasperserver/flow.html?_flowId=viewReportFlow&standAlone=true&_flowId=viewReportFlow&ParentFolderUri=%2Freports%2FIGU%2FAR&reportUnit=%2Freports%2FIGU%2FAR%2F05_tfkw&j_username=jasperadmin&j_password=jasperadmin&decorate=no&dateto="+ self.dateto.strftime("%Y%m%d") + "&arperson="+ self.arperson + "&collector=" + collector + "&output=pdf"

		return {
					"type": "ir.actions.act_url",
					"url": url,
					"target": "new",
				}                
