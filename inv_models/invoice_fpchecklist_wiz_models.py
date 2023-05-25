# -*- coding: utf-8 -*-

from operator import truediv
from odoo import models, fields, api
import os
from odoo.modules import get_modules, get_module_path
import base64
import pymssql
from PyPDF2 import PdfFileMerger 
from zipfile import ZipFile
import pytz
from datetime import datetime
import requests
from jinja2 import Environment, FileSystemLoader


class CNW_INVOICE_FPCHECKLIST_DETAIL (models.TransientModel):
	_name           = "cnw.invoice.fpchecklist.detail"
	_description    =  "cnw.invoice.fpchecklist.detail"
	name 			= fields.Char("Name" , required=True)
	email 			= fields.Char("Email Address", required=True)

	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
	fpchecklist_id 	= fields.Many2one("cnw.invoice.fpchecklist")

class CNW_INVOICE_FPCHECKLIST(models.TransientModel):
	_name           = "cnw.invoice.fpchecklist"
	_description    =  "cnw.invoice.fpchecklist "
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
	
	export_to       = fields.Selection([ ('pdf', 'Single PDF'),
						('zip', 'ZIP File') ],string='Download To', default='zip',required=True)

	is_email        = fields.Boolean("Send To Email", default=False)

	email_subject   = fields.Char("Subject",default="Here is your Tax File")


	email_body      = fields.Html("Email Body", default="Here is your Tax File")
	email_to        = fields.Char("To",default="ar@indoguna.co.id")
	email_from      = fields.Char("from",default="ar@indoguna.co.id")

	


	filexls         = fields.Binary("File Output")    
	filenamexls     = fields.Char("File Name Output")

	fp_detail_ids	= fields.Many2many("jas.lap.mailaddress",string="Email Client")

	def check_list(self):
		mpath       = get_module_path('cnw_invar') 
		filezip = 'FakturPajak_'+   self.company_id.code_base  + '_'+   datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d%H%M%S")  +  '.zip'
		filepdf = 'FakturPajak_'+   self.company_id.code_base  + '_'+   datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d%H%M%S")  +  '.pdf'
		fp_path = self.env["ar.invoice.setting.fppath"].search([("company_id","=",self.company_id.id)]).name
		cardname = ""
		invoicefp = self.env['ar.invoice'].browse(self._context.get('active_ids', []))
		#print(invoicefp)
		#print(type(invoice))
		if self.export_to=="zip":
			
			filename = filezip
			zip = ZipFile(mpath + "/temp/" + filezip,'w')
			for inv in invoicefp:
				#merger.append(pdf,import_bookmarks=False)
				cardname  = inv.cardname
				fp = inv.fp + ".pdf"
				zip.write(  inv.fp_filename,fp )
				#zip.write(fp_path + "/" +   inv.fp_filename,inv.fp_filename )
			zip.close()
		else:
			merger = PdfFileMerger()
			filename = filepdf
			for inv in invoicefp:
				merger.append(   inv.fp_filename,import_bookmarks=False)
				#merger.append(fp_path + "/" +    inv.fp_filename,import_bookmarks=False)
				cardname  = inv.cardname
			merger.write(mpath + "/temp/" + filepdf)
			merger.close()   

# Open Binary to Fields Binary 
		file = open(mpath + '/temp/'+ filename , 'rb')
		out = file.read()
		file.close()
		self.filexls =base64.b64encode(out)
		self.filenamexls = filename

		os.remove(mpath + '/temp/'+ filename )
# Close and delete Binary File 



		#print("web/content/?model=" + self._name +"&id=" + str(self.id) + "&filename_field=filenamexls&field=filexls&download=true&filename=" + self.filenamexls)
		if self.is_email ==True:
			indate = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d")
			subject = "Tax Data From " + self.env.user.company_id.name + " " + indate
			strtable = ""
			for inv in invoicefp:
				strtable +="<tr>"
				strtable +="<td>" + inv.numatcard + "</td> \n"
				strtable +="<td>" + str(inv.docdate) + "</td> \n"

				kwitansi = inv.kwitansi if inv.kwitansi else ""
				fp = inv.fp if inv.fp else "" 

				strtable +="<td>" + kwitansi + "</td> \n"
				strtable +="<td>" + fp + "</td> \n"
				strtable +="<td>" + str(inv.dpp) + "</td> \n"
				strtable +="<td>" + str(inv.ppn) + "</td> \n"
				strtable +="<td>" + str(inv.total) + "</td> \n"
				strtable +="<t>"
				strtable +="</tr>"
			dataline=[]
			for email in self.fp_detail_ids :
				linedetail={}
				linedetail["name"]= email.name 
				linedetail["email"]=email.mailaddress 
				dataline.append(linedetail)

			env = Environment(loader=FileSystemLoader(mpath + '/template/'))
			template = env.get_template("email_template.html")     			
			template_var = {"cardname":cardname,  
							"body": self.email_body,
							"detail" :strtable  ,
							"ar_person": self.env.user.name,
							"ar_email" : self.env.user.x_igu_email
							}
			html_out =  template.render(template_var)
			botmail =   self.env["cnw.botmail.master"].search([])
			url = "https://api.sendinblue.com/v3/smtp/email"

			payload = {
				"sender": {
					"name": "Indoguna (no-reply)",
					"email": "indoguna-report@indoguna.co.id", 
				},
				"to": dataline ,
				"cc": [
							{
								"email":self.env.user.x_igu_email,
								"name": self.env.user.name
							}
						],
				"attachment": [
					{
						"name": filename ,
						"content": self.filexls
					} ],
				"htmlContent": html_out,
				"subject": subject, 
			}
			headers = {
				"Accept": "application/json",
				"Content-Type": "application/json",
				"api-key": botmail.botmail_id
			}

			response = requests.post(url, json=payload, headers=headers)

		else :

			return {
				'name': 'Report',
				'type': 'ir.actions.act_url',
				'url': "web/content/?model=" + self._name +"&id=" + str(
					self.id) + "&filename_field=filenamexls&field=filexls&download=true&filename=" + self.filenamexls,
				'target': 'new',
				}

 


#zip = ZipFile('my_python_files.zip','w')