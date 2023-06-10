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


class ARTukarfaktur(models.Model):
	_name           = "ar.tf"
	_description    = "Tukar Faktur"
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
	name            = fields.Char("Nomor ID")
	coll_id         = fields.Many2one("ar.collector",string="Collector")
	jalur_id        = fields.Many2one("ar.jalur",string="Jalur")
	remarks         = fields.Char("Remarks")
	ar_id           = fields.Many2one("res.users",string="AR Person", default=lambda self: self.env.user.id )
	docdate         = fields.Date("Date",default=lambda s:fields.Date.today())
	tfline_ids      = fields.One2many("ar.invoice","tf_id",string="Jadwal Harian Detail")
	status          = fields.Selection(string="Document Status",selection=[("open","Open"),("postSAP","Post to SAP"),("closed","Closed")],default="open")   
	statustf        = fields.Selection(string="Status",selection=[("tf","Tukar Faktur"),("gr","Giro"),("ln","Lain Lain")],default="tf")       
	filexls         = fields.Binary("File Output")    
	filenamexls     = fields.Char("File Name Output")
	txtlog 			= fields.Text("Text Log")
# tambahan
	doctotal        = fields.Float("Total",default=0.0)
	def post2sap(self):

		CompanyDB 	= self.company_id.db_name
		UserName 	= self.company_id.sapuser
		Password 	= self.company_id.sappassword
		url 		= self.company_id.sapsl
 

		#print(mylist)

		appSession = requests.Session()

		#########################
		# LOGIN
		#########################

		urllogin = url + "Login"
		print(urllogin)

		payload = { "CompanyDB" :CompanyDB ,
					"UserName" : UserName,
					"Password" : Password
					}
		response = appSession.post(urllogin, json=payload,verify=False)
		txtlog = ""
		print(response.json())
#########################
# UPDATE TF
#########################
		for line in self.tfline_ids :
			urltf = url + "Invoices("  +  line.docentry  + ")"
			payload = {
						"DocDueDate" : line.docduedate.strftime("%Y-%m-%d") , 
						"U_LT_No" : line.tf_number ,
						"U_TF_date" : line.tf_date.strftime("%Y-%m-%d"),
						"U_Coll_Name" : line.tf_collector ,
						"U_Tagihan_date" : line.tf_date.strftime("%Y-%m-%d"),
						"U_RemDelay" : line.tf_remarks
						
					}               			
			rsp = appSession.patch(urltf,json=payload,verify=False)
			txtlog = txtlog + urltf + " >> " + str(rsp.status_code) +   "\n"
			 
			if rsp.status_code >=400 :
				print(urltf)
				txtlog =txtlog + str(payload) + "\n"
				print(txtlog =txtlog + str(rsp.json()) + "\n")
		self.txtlog = txtlog
#########################
# LOGOUT SERVICE LAYER
#########################				
		urllogout = url + "Logout"
		rsplogout = appSession.post(urllogout,json=payload,verify=False)		

		self.status = "postSAP"		


	def print_pdf(self):
		mpath       = get_module_path('cnw_invar')
		filenamepdf = 'TukarFaktur' + self.ar_id.name + "_"   + self.coll_id.name + '_' +  self.docdate.strftime("%Y%m%d")   + '.pdf'
		filepath    = mpath + '/temp/'+ filenamepdf

		igu_title = "JADWAL TUKAR FAKTUR"
		igu_tanggal = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")
		igu_remarks = " Per Tanggal " + self.docdate.strftime("%Y-%m-%d")                    

		logo = mpath + "/template/logo" + self.company_id.code_base + ".png"
		options = {
					"page-size" : "A4" ,
					"orientation" : "landscape"
			}
		print_date  = datetime.now(pytz.timezone("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M:%S")


		host        = self.company_id.server
		database    = self.company_id.db_name
		user        = self.company_id.db_usr
		password    = self.company_id.db_pass 
		company 	= self.company_id.name
		
		conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';UID='+user+';PWD='+ password + ';TrustServerCertificate=yes')
		
		
 
		msgsql ="""
					declare @tf_no varchar(50)

					set @tf_no = '""" + self.name + """'


					select  b.cardcode + '-' + b.cardname ,
							convert(varchar,a.docdate,23) docdate, 
							a.docnum ,
							a.NumAtCard ,

							a.U_Kw_No ,
							a.U_RemDelay ,
							a.doctotal

					from oinv a
					inner join ocrd b on a.cardcode = b.cardcode 
					where a.U_LT_No = @tf_no

		"""
		data = pandas.io.sql.read_sql(msgsql,conn) 
		df = data

		detail = df.values.tolist() 
		env = Environment(loader=FileSystemLoader(mpath + '/template/'))        
		jalur = self.jalur_id.name if self.jalur_id.name else "-"
		template = env.get_template("tukarfaktur.html")            
		template_var = {"logo":logo,
						"igu_title" :igu_title,
						"igu_tanggal" :igu_tanggal ,
						"igu_remarks" :igu_remarks , 
						"tfno" :self.name  , 
						"arperson" : self.env.user.name , 
						"collector" :self.coll_id.name , 
						"jalur" :jalur , 
						"total" : self.doctotal,
						
						"detail": detail}
		filename = filenamepdf
		html_out = template.render(template_var)
		pdfkit.from_string(html_out,mpath + '/temp/'+ filenamepdf,options=options) 
	   # SAVE TO MODEL.BINARY 
		file = open(mpath + '/temp/'+ filename , 'rb')
		out = file.read()
		file.close()
		self.filexls =base64.b64encode(out)
		self.filenamexls = filename
		os.remove(mpath + '/temp/'+ filename )		
		return {
			'name': 'Report',
			'type': 'ir.actions.act_url',
			'url': "web/content/?model=" + self._name +"&id=" + str(
				self.id) + "&filename_field=filenamexls&field=filexls&download=true&filename=" + self.filenamexls,
			'target': 'new',
			}	
	def print2_pdf(self):
		mpath       = get_module_path('cnw_invar')
		filenamepdf = 'TukarFaktur2' + self.ar_id.name + "_"   + self.coll_id.name + '_' +  self.docdate.strftime("%Y%m%d")   + '.pdf'
		filepath    = mpath + '/temp/'+ filenamepdf

		igu_title = "JADWAL TUKAR FAKTUR"
		igu_tanggal = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")
		igu_remarks = " Per Tanggal " + self.docdate.strftime("%Y-%m-%d")                    

		logo = mpath + "/template/logo" + self.company_id.code_base + ".png"
		options = {
					"page-size" : "A4" ,
					"orientation" : "landscape"
			}
		print_date  = datetime.now(pytz.timezone("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M:%S")


		host        = self.company_id.server
		database    = self.company_id.db_name
		user        = self.company_id.db_usr
		password    = self.company_id.db_pass 
		company 	= self.company_id.name
		
		conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';UID='+user+';PWD='+ password + ';TrustServerCertificate=yes')
		
		
 
		msgsql ="""
					declare @tf_no varchar(50)

					set @tf_no = '""" + self.name + """'
					select  b.cardcode + '-' + b.cardname ,
							convert(varchar,a.U_kw_PrintDate,23) docdate,  

							a.U_Kw_No , 
							sum(a.doctotal) doctotal

					from oinv a
					inner join ocrd b on a.cardcode = b.cardcode 
					where a.U_LT_No = @tf_no
					group by b.cardcode + '-' + b.cardname ,
							convert(varchar,a.U_kw_PrintDate,23) ,  

							a.U_Kw_No 
					order by b.cardcode + '-' + b.cardname ,
							convert(varchar,a.U_kw_PrintDate,23) ,  

							a.U_Kw_No 

		"""
		data = pandas.io.sql.read_sql(msgsql,conn) 
		df = data

		detail = df.values.tolist() 
		env = Environment(loader=FileSystemLoader(mpath + '/template/'))        
		jalur = self.jalur_id.name if self.jalur_id.name else "-"
		template = env.get_template("tukarfakturkwitansi.html")            
		template_var = {"logo":logo,
						"igu_title" :igu_title,
						"igu_tanggal" :igu_tanggal ,
						"igu_remarks" :igu_remarks , 
						"tfno" :self.name  , 
						"arperson" : self.env.user.name , 
						"collector" :self.coll_id.name , 
						"jalur" :jalur , 
						"total" : self.doctotal,
						
						"detail": detail}
		filename = filenamepdf
		html_out = template.render(template_var)
		pdfkit.from_string(html_out,mpath + '/temp/'+ filenamepdf,options=options) 
	   # SAVE TO MODEL.BINARY 
		file = open(mpath + '/temp/'+ filename , 'rb')
		out = file.read()
		file.close()
		self.filexls =base64.b64encode(out)
		self.filenamexls = filename
		os.remove(mpath + '/temp/'+ filename )		
		return {
			'name': 'Report',
			'type': 'ir.actions.act_url',
			'url': "web/content/?model=" + self._name +"&id=" + str(
				self.id) + "&filename_field=filenamexls&field=filexls&download=true&filename=" + self.filenamexls,
			'target': 'new',
			}				
class ARTukarfakturDetail(models.Model):
	_name           = "ar.tf.line"
	_description    = "Jadwal Kolektor Detail"
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
	name            = fields.Char("Nomor ID")
	invoice_id      = fields.Many2one("ar.invoice",string="Invoice")
	docnum          = fields.Char("Invoice")
	docdate         = fields.Date("Doc Date Invoice")
	numatcard       = fields.Char("SO Number")
	kwitansi        = fields.Char("Kwitansi")
	partner_name    = fields.Char("Partner Name",related="invoice_id.cardname")
	partner_address = fields.Char("Partner Address",related="invoice_id.address")
	balance         = fields.Float("Balance",digits=(19,2),default=0)
	
	status          = fields.Selection(string="Status",selection=[("tf","Tukar Faktur"),("gr","Giro"),("ln","Lain Lain")],default="tf")   
	keterangan      = fields.Char("Keterangan",default=" ")


class ARTukarfakturWizard(models.TransientModel):
	_name           = "ar.tf.wizard"
	_description    = "Tukar Faktur"
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)  
	tfdate         	= fields.Date("TukarFaktur",default=lambda s:fields.Date.today()) 
	updatetf        = fields.Selection(string="Update",selection=[("tf","Update Tanggal Tukar Faktur"),("py","Update Tanggal Est Payment")],default="tf")       
 
 
	def UpdateTglTf(self):


 		 
		NomorTF  = self.env["cnw.numbering.wizard"].getnumbering('TF',self.docdate)    
		 
		listinvoice = self.env['ar.invoice'].browse(self._context.get('active_ids', []))
		doctotal = 0.0

#print(listinvoice)
#########################
# LOGIN
#########################
		CompanyDB 	= self.company_id.db_name
		UserName 	= self.company_id.sapuser
		Password 	= self.company_id.sappassword
		url 		= self.company_id.sapsl


		urllogin = url + "Login"
		print(urllogin)

		payload = { "CompanyDB" :CompanyDB ,
					"UserName" : UserName,
					"Password" : Password
					}
		
		response = appSession.post(urllogin, json=payload,verify=False)
		txtlog = ""
		#print(response.json())
		for invoice in listinvoice:
			
			paydate = self.tfdate + timedelta(days=invoice.topdays)
		
			appSession = requests.Session()


	#########################
	# UPDATE TF
	######################### 
			if invoice.objtype =="13":
				urltf = url + "Invoices("  + invoice.docentry + ")"
				payload = {
							"DocDueDate" : self.tfdate.strftime("%Y-%m-%d") , 
							"TaxDate" : paydate.strftime("%Y-%m-%d") , 
							"U_LT_No" : NomorTF ,
							"U_TF_date" : self.tfdate.strftime("%Y-%m-%d"), 
							"U_Tagihan_date" : self.tfdate.strftime("%Y-%m-%d"),
						}               			
				rsp = appSession.patch(urltf,json=payload,verify=False)
				txtlog = txtlog + urltf + " >> " + str(rsp.status_code) +   "\n"
			
				if rsp.status_code >=400 :
					print(urltf)
					txtlog =txtlog + str(payload) + "\n"
					print(txtlog =txtlog + str(rsp.json()) + "\n")

			if invoice.objtype =="14":
				urltf = url + "CreditNotes("  + invoice.docentry + ")"
				payload = {
							"DocDueDate" : self.tfdate.strftime("%Y-%m-%d") , 
							"TaxDate" : paydate.strftime("%Y-%m-%d") , 
							"U_LT_No" : NomorTF ,
							"U_TF_date" : self.tfdate.strftime("%Y-%m-%d"), 
							"U_Tagihan_date" : self.tfdate.strftime("%Y-%m-%d"),
						}               			
				rsp = appSession.patch(urltf,json=payload,verify=False)
				txtlog = txtlog + urltf + " >> " + str(rsp.status_code) +   "\n"
			
				if rsp.status_code >=400 :
					print(urltf)
					txtlog =txtlog + str(payload) + "\n"
					print(txtlog =txtlog + str(rsp.json()) + "\n")			 
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


