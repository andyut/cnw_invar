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

class CNWCetakanInvoiceUser(models.Model):
	_name 			= "cnw.cetakan.invoice.user"
	_description 	        = "Cetakan Invoice User"
	company_id		= fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
	name 			= fields.Char("IDX")
	username		= fields.Char("User name")
	userwebid 		= fields.Char("User web ID")

class CNWCetakanInvoice(models.TransientModel):
	_name           = "cnw.cetakan.invoice"
	_description    = "Cetakan Invoice"
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)

	datefrom        = fields.Date("Date From",default=lambda s:fields.Date.today())
	dateto          = fields.Date("Date To",default=lambda s:fields.Date.today())
	inv_from        = fields.Char("Invoice No from",default="",required=True)
	inv_to          = fields.Char("Invoice No To",default="",required=True)
	
	userwebid		= fields.Many2one("cnw.cetakan.invoice.user",string="User SAP WEB")
	
	filexls         = fields.Binary("File Output",default=" ")    
	filenamexls     = fields.Char("File Name Output",default="EmptyText.txt")
	export_to       = fields.Selection([ ('download','Download PDF'),('pdf', 'PDF View'),],string='Export To', default='pdf')
	
	def get_CetakanInvoice(self):
		mpath       = get_module_path('cnw_invar') 
		filenamepdf    = 'invoice_'+   self.inv_from  + '_'+ self.inv_to    +  self.env.user.name +  '.pdf'
		filenamepdf    = 'invoice_'+   self.inv_from  + '_'+ self.inv_to    +  self.env.user.name +   '.pdf'
		filepath    = mpath + '/temp/'+ filenamepdf

	#LOGO CSS AND TITLE
		logo        = mpath + '/template/logo.png' 
		logo        = mpath + '/template/logo'+ self.company_id.code_base + '.png'
		#cssfile     = mpath + '/template/style.css'        
		options2 = { 
				'page-height':'16.5cm',
				'page-width':'21.5cm',
				'orientation': 'portrait',
				}
		options = { 
				'page-size':'A4', 
				'orientation': 'portrait',
				}
		print_date = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")
	#2008202239

	#MULTI COMPANY 

		listfinal = []
		listfinal2 = []
		pandas.options.display.float_format = '{:,.2f}'.format

		host        = self.company_id.server
		database    = self.company_id.db_name
		user        = self.company_id.db_usr
		password    = self.company_id.db_pass 
			
		conn = pymssql.connect(host=host, user=user, password=password, database=database)
		pd.options.display.float_format = '{:,.2f}'.format
		pandas.options.display.float_format = '{:,.2f}'.format
		
		msgsql =  """exec [dbo].[IGU_ACT_INVOICE_HEADER]  '""" + self.inv_from +  """','""" + self.inv_to +  """','""" + self.datefrom.strftime("%Y%m%d")  +  """','""" + self.dateto.strftime("%Y%m%d") +  """' """
		msgsql2 =  """exec [dbo].[IGU_ACT_INVOICE_DETAIL]  '""" + self.inv_from +  """','""" + self.inv_to +  """','""" + self.datefrom.strftime("%Y%m%d")  +  """','""" + self.dateto.strftime("%Y%m%d") +  """' """
		data = pandas.io.sql.read_sql(msgsql,conn) 
		data2 = pandas.io.sql.read_sql(msgsql2,conn) 
		listfinal.append(data)
		listfinal2.append(data2)
	
		
		conn.commit()


		df = pd.concat(listfinal)  
		df2 = pd.concat(listfinal2)  
		invoiceheader = df.values.tolist()
		invoicedetail = df2.values.tolist()
		
	# TEMPLATE CETAKAN INVOICE        
		#print(invoiceheader)
		#print(invoicedetail)
		# for inv_line in invoiceheader:
		#     self.env["cnw.so.audittrail"].create({
		#                                         "sonumber":inv_line[3],
		#                                         "cardcode":inv_line[5],
		#                                         "cardname":inv_line[6], 
		#                                         "sales":inv_line[19],
		#                                         "arperson":inv_line[15],
		#                                         "docref":inv_line[13],
		#                                         "docdate":inv_line[20],
		#                                         "doctype":"Cetak Invoice",
		#                                         "position":"INVOICE",
		#                                         "docstatus":"Cetak invoice",
		#                                         "docby":self.env.user.name ,
		#                                         "docindate":datetime.now()})
		filename = filenamepdf
		env = Environment(loader=FileSystemLoader(mpath + '/template/'))
		
		template = env.get_template("cetakan_invoice_template.html")            
		rek =  self.env.user.company_id.rek if  self.env.user.company_id.rek else "" 
		loc =  self.env.user.company_id.loc if  self.env.user.company_id.loc else "" 
		template_var = {"logo":logo, 
				"igu_tanggal" :print_date ,
				"rek":rek,
				"loc":loc,
				"header" :invoiceheader,
				"detail" :invoicedetail  }
		
		html_out = template.render(template_var)
		#print("OUtput html")
		#print (html_out)
		print(mpath + '/temp/'+ filename)
		pdfkit.from_string(html_out,mpath + '/temp/'+ filename,options=options) 
		
		# SAVE TO MODEL.BINARY 
		file = open(mpath + '/temp/'+ filename , 'rb')
		out = file.read()
		file.close()
		self.filexls =base64.b64encode(out)
		self.filenamexls = filename
		os.remove(mpath + '/temp/'+ filename )
		print("web/content/?model=" + self._name +"&id=" + str(self.id) + "&filename_field=filenamexls&field=filexls&download=true&filename=" + self.filenamexls)
		if self.export_to =="pdf":
			return {
					'type': 'ir.actions.do_nothing'
					}
		else:
			return {
				'name': 'Report',
				'type': 'ir.actions.act_url',
				'url': "web/content/?model=" + self._name +"&id=" + str(
				self.id) + "&filename_field=filenamexls&field=filexls&download=true&filename=" + self.filenamexls,
				'target': 'new',
				}
	