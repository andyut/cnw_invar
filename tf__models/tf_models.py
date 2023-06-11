# -*- coding: utf-8 -*-

from odoo import models, fields, api
import base64 
import numpy as np
import pandas as pd
import requests  
import os
import pytz
from odoo.exceptions import UserError
from odoo.modules import get_modules, get_module_path
from datetime import datetime, date, timedelta
from jinja2 import Environment, FileSystemLoader
import pdfkit
import pyodbc  
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import numpy as np
import pandas as pd
import pandas.io.sql

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

 
class ARTukarfakturWizard(models.TransientModel):
	_name           = "ar.tf.wizard"
	_description    = "Tukar Faktur"
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)  
	tfdate         	= fields.Date("TukarFaktur",default=lambda s:fields.Date.today()) 
	updatetf        = fields.Selection(string="Update",selection=[("tf","Update Tanggal Tukar Faktur"),("py","Update Tanggal Est Payment")],default="tf")       
	
	@api.multi
	def UpdateTglTf(self):

		print("mulai update tf date")
 		 
		NomorTF  = self.env["cnw.numbering.wizard"].getnumbering('TF',self.tfdate)    
		 
		listinvoice = self.env['cnw.invar.saldopiutangdetailmodels'].browse(self._context.get('active_ids', []))
		doctotal = 0.0
		print(listinvoice)
#print(listinvoice)
#########################
# LOGIN
#########################
		CompanyDB 	= self.company_id.db_name
		UserName 	= self.company_id.sapuser
		Password 	= self.company_id.sappassword
		url 		= self.company_id.sapsl

		appSession = requests.Session()

		urllogin = url + "Login"
		print(urllogin)

		payload = { "CompanyDB" :CompanyDB ,
					"UserName" : UserName,
					"Password" : Password
					}
		
		response = appSession.post(urllogin, json=payload,verify=False)
		txtlog = "" 
		for invoice in listinvoice:
			print(invoice)
			invoice.txtlog= str(invoice)
			invoice.lt_no = NomorTF
			
			if self.updatetf =="tf" :
				invoice.docduedate = self.tfdate
				paydate = self.tfdate + timedelta(days=invoice.topdays)
				invoice.taxdate = paydate
			else:
				invoice.taxdate = self.tfdate

	#########################
	# UPDATE TF
	######################### 
			print("invoice type : ")
			print(invoice.objtype)
			if invoice.objtype =="13":
				urltf = url + "Invoices("  + invoice.docentry + ")"
				payload = {
							"DocDueDate" : invoice.docduedate.strftime("%Y-%m-%d") , 
							"TaxDate" : invoice.taxdate.strftime("%Y-%m-%d") , 
							"U_LT_No" : NomorTF ,
							"U_TF_date" : invoice.docduedate.strftime("%Y-%m-%d"), 
							"U_Tagihan_date" : invoice.docduedate.strftime("%Y-%m-%d"),
						}               			
				rsp = appSession.patch(urltf,json=payload,verify=False)
				txtlog = txtlog + urltf + " >> " + str(rsp.status_code) +   "\n"
				invoice.txtlog= txtlog  
					
				if rsp.status_code >=400 :
					print(urltf)
					txtlog =txtlog + str(payload) + "\n"
					print(txtlog )

			if invoice.objtype =="14":
				urltf = url + "CreditNotes("  + invoice.docentry + ")"
				payload = {
							"DocDueDate" : invoice.docduedate.strftime("%Y-%m-%d") , 
							"TaxDate" : invoice.taxdate.strftime("%Y-%m-%d") , 
							"U_LT_No" : NomorTF ,
							"U_TF_date" : invoice.docduedate.strftime("%Y-%m-%d"), 
							"U_Tagihan_date" : invoice.docduedate.strftime("%Y-%m-%d"),
						}                 			
				rsp = appSession.patch(urltf,json=payload,verify=False)
				txtlog = txtlog + urltf + " >> " + str(rsp.status_code) +   "\n"
				print(txtlog) 
				invoice.txtlog= txtlog 
				if rsp.status_code >=400 :
					print(urltf)
					txtlog =txtlog + str(payload) + "\n"
					print(txtlog )			 

			self.env["cnw.so.audittrail"].create({
												"sonumber":invoice.numatcard,
												"cardcode":invoice.cardcode,
												"cardname":invoice.cardname,  
												"arperson":invoice.arperson,
												"docref":NomorTF,
												"docdate":self.tfdate,
												"doctype":"INVOICE",
												"position":"TUKARFAKTUR",
												"docstatus":"AR TF",
												"docby":self.env.user.name ,
												"docindate":self.tfdate})

#########################
# LOGOUT SERVICE LAYER
#########################				
		urllogout = url + "Logout"
		rsplogout = appSession.post(urllogout,json=payload,verify=False)		

		self.status = "postSAP"		


		
            # self.env["cnw.so.audittrail"].create({
            #                                     "sonumber":inv.numatcard,
            #                                     "cardcode":inv.cardcode,
            #                                     "cardname":inv.cardname, 
            #                                     "sales":inv.salesperson,
            #                                     "arperson":inv.arperson,
            #                                     "docref":inv.docnum,
            #                                     "docdate":inv.docdate,
            #                                     "doctype":"INVOICE",
            #                                     "position":"INVOICE",
            #                                     "docstatus":"invoice Checklist",
            #                                     "docby":self.env.user.name ,
            #                                     "docindate":self.checklist_date})


