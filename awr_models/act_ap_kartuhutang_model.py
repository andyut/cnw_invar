# -*- coding: utf-8 -*-
 
import numpy as np
import pandas as pd
import pandas.io.sql
import requests
import os
import pytz
from odoo.exceptions import UserError
from odoo.modules import get_modules, get_module_path
from datetime import datetime
from odoo import models, fields, api
import base64
import pyodbc
from jinja2 import Environment, FileSystemLoader
import pdfkit


class CNWLapkartuhutangEmail(models.TransientModel):
	_name           = "cnw.awr28.kartuhutangemail"
	_description    =  "cnw.awr28.kartuhutangemail"
	 
	  
	email_subject   = fields.Char("Subject",default="Outstanding Payable")


	email_body      = fields.Html("Email Body", default="Outstanding Payable")
	email_to        = fields.Char("To",default="ar@indoguna.co.id")
	email_from      = fields.Char("from",default="ar@indoguna.co.id")

	


	filexls         = fields.Binary("File Output")    
	filenamexls     = fields.Char("File Name Output")

	hutang_ids		= fields.Many2many("jas.lap.mailaddress",string="Email Client")
	def check_list(self):
		mpath       = get_module_path('cnw_awr28') 
		cardname = ""
		hutang = self.env['cnw.awr28.kartuhutang'].browse(self._context.get('active_ids', []))


		#print("web/content/?model=" + self._name +"&id=" + str(self.id) + "&filename_field=filenamexls&field=filexls&download=true&filename=" + self.filenamexls)
		indate = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d")
		subject = "[" + self.env.user.company_id.name + "] Kartu Hutang" 
		strtable = ""
		
		totalfc = 0.0
		totalsy = 0.0
		for inv in hutang:
			strtable +="<tr>" 
			strtable +="<td>" + inv.transname + "</td> \n"  
			strtable +="<td>" + str(inv.docdate) + "</td> \n"
			strtable +="<td>" + str(inv.ponumber) + "</td> \n"
			strtable +="<td>" + str(inv.docnum) + "</td> \n"
			strtable +="<td>" + str(inv.docref) + "</td> \n" 

			
			strtable +="<td>" + inv.currency + "</td> \n" 
			strtable +="<td style='text-align: right;' >" + str("{:,.2f}".format(inv.balancefc)) + "</td> \n"
			strtable +="<td style='text-align: right;' >" + str("{:,.2f}".format(inv.balancesy)) + "</td> \n"

			totalsy += inv.balancesy
			totalfc += inv.balancefc
			
			strtable +="<t>"
			strtable +="</tr>"
			cardname = inv.cardname
		dataline=[]
		for email in self.hutang_ids :
			linedetail={}
			linedetail["name"]= email.name 
			linedetail["email"]=email.mailaddress 
			dataline.append(linedetail)

		env = Environment(loader=FileSystemLoader(mpath + '/template/'))
		template = env.get_template("email_hutang.html")     			
		template_var = {"cardname":cardname,  
						"body": self.email_body,
						"detail" :strtable  ,
						"ar_person": self.env.user.name,
						"ar_email" : self.env.user.x_igu_email,
						"totalfc" : "{:,.2f}".format(totalfc) ,
						"totalsy" : "{:,.2f}".format(totalsy) ,
						}
		html_out =  template.render(template_var)
		botmail =   self.env["cnw.botmail.master"].search([])
		url = "https://api.sendinblue.com/v3/smtp/email"
		subject = "[" + self.env.user.company_id.name + "] Outstanding Payable  "  + cardname
		payload = {
			"sender": {
				"name": "Information (no-reply)",
				"email": "indoguna-report@indoguna.co.id", 
			},
			"to": dataline ,
			"cc": [
						{
							"email":self.env.user.x_igu_email,
							"name": self.env.user.name
						}
					],
			 
			"htmlContent": html_out,
			"subject": subject, 
		}
		headers = {
			"Accept": "application/json",
			"Content-Type": "application/json",
			"api-key": botmail.botmail_id
		}

		response = requests.post(url, json=payload, headers=headers)
		print(response.json())



class CNW_kartuhutang(models.Model):
	_name           = "cnw.awr28.kartuhutang"
	_description    = "cnw.awr28.kartuhutang"
	company_id      = fields.Char("Company")
	companycode		= fields.Char("Company Code")
	name            = fields.Char("TransID")
	transno         = fields.Char("Trans Number")
	refdate 		= fields.Date("Ref Date")
	transname 	 	= fields.Char("Trans Name")
	groupname 		= fields.Char("Group Name")
	cardcode 		= fields.Char("Vendor Code")
	cardname 		= fields.Char("Vendor Name")
	debit 			= fields.Float("Debit", digit=(19,2))
	credit 			= fields.Float("Credit", digit=(19,2))
	amount 			= fields.Float("Amount", digit=(19,2))
	currency 		= fields.Char("Currency",default='IDR')
	fcamount 		= fields.Float("Foreign Amount",default=0)
	balance 		= fields.Float("Balance / Reconsile",default=0)
	linememo		= fields.Char("Line Memo") 
	ref1 			= fields.Char("Ref1")
	ref2 			= fields.Char("ref2")
	


class CNW_kartuhutangget(models.TransientModel):
	_name           = "cnw.awr28.kartuhutang.get"
	_description    = "cnw.kartuhutang.get"
	company_id      = fields.Many2many('res.company', string="Company",required=True)
	 
	datefrom		= fields.Date ("Date From", default=fields.Date.today()) 
	dateto          = fields.Date ("Date To", default=fields.Date.today()) 
	partner 		= fields.Char("Partner")
	account         = fields.Selection(string="Account", selection=[("2110001","2110001-HUTANG DAGANG"),("2175002","2175002-HUTANG ACTIVA")],default="2110001")
	filexls         = fields.Binary("File Output")    
	filenamexls     = fields.Char("File Name Output")
	
	export_to       = fields.Selection([ ('list','List 	'), 
				     					('json','json Format'),
									     ('pdf','PDF Format'),
				     					('xls', 'Excel')],string='Export To', default='list')

	
	def view_kartuhutang(self): 
		mpath       	= get_module_path('cnw_awr28')
		filenamexls2    = 'kartuhutang_'+   self.dateto.strftime("%Y%m%d")  + '.xlsx'
		filenamepdf    	= 'kartuhutang_'+   self.dateto.strftime("%Y%m%d")  + '.pdf'
		filenamejson 	= 'kartuhutang_'+   self.dateto.strftime("%Y%m%d")  + '.json'
		filex 			=  'kartuhutang_'+   self.dateto.strftime("%Y%m%d")
		filepath    = mpath + '/temp/'+ filenamexls2

		 
#LOGO CSS AND TITLE
		logo        = mpath + '/template/logoigu.png' 
		cssfile     = mpath + '/template/style.css'        
		options = {
					'page-size': 'A4',
					'orientation': 'landscape',
					}
		igu_title = "Kartu Hutang Detail"
		igu_tanggal = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")
		igu_remarks = "Kartu Hutang Detail Per Tanggal " + self.dateto.strftime("%Y-%m-%d")   	                 

#MULTI COMPANY 

		listfinal = []
		pandas.options.display.float_format = '{:,.2f}'.format

		for comp in self.company_id:

			host        = comp.server
			database    = comp.db_name
			user        = comp.db_usr
			password    = comp.db_pass 
			 
			#conn = pymssql.connect(host=host, user=user, password=password, database=database)
			conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';UID='+user+';PWD='+ password + ';TrustServerCertificate=yes')
			
			bp = self.partner if self.partner else ""
			
			msgsql =""" declare @datefrom varchar(20) ,
								@dateto varchar(20) ,
								@vendor varchar(50) ,
								@account varchar(20),
								@company varchar(100)

							set @datefrom = '""" + self.datefrom.strftime("%Y-%m-%d") + """'
							set @dateto =  '""" + self.dateto.strftime("%Y-%m-%d") + """'
							set @vendor =''
							set @account = '"""+ self.account + """' 
							set @company =  '""" + comp.code_base + """'
 

							select '""" + comp.code_base + """' Company ,
									'000-OPENING BALANCE' TransNumber ,
									@datefrom refdate, 
									'00-OPENING BALANCE' TransName ,
										d.groupname ,
										c.cardcode ,
										c.cardname ,
										sum(a.debit) debit ,
										sum(a.credit) credit ,
										sum(a.credit - a.debit) amount ,
										case when isnull(a.fcCurrency,'IDR') ='IDR' then 'IDR' else a.fccurrency end currency,
										sum(case when isnull(a.fcCurrency,'IDR') = 'IDR' then a.credit - a.debit  else  a.fccredit - a.fcdebit end ) FCAmount ,
										sum(a.BalScCred - a.BalScDeb) balance,
										'Opening Balance AP 'linememo ,
										' - ' ref1 , 
										' - '  ref2
							from jdt1 a 
							inner join ojdt b on a.Transid = b.transid 
							inner join ocrd c on a.shortname  = c.cardcode 
							inner join ocrg d on c.groupcode = d.groupcode
							left outer join [@igu_transtype] e on a.transtype = e.code 
							where a.account = @account 
							and convert(varchar,a.refdate ,23 )  < @datefrom  
							group by 
										d.groupname ,
										c.cardcode ,
										c.cardname ,
										case when isnull(a.fcCurrency,'IDR') ='IDR' then 'IDR' else a.fccurrency end 
							union ALL

							select      '""" + comp.code_base + """' Company ,
										isnull(b.u_trans_no,b.number) TransNumber,
										convert(varchar,a.refdate,23) refdate ,
										convert(varchar,a.transtype) + '-' + isnull(e.name,'') transName,
										d.groupname ,
										c.cardcode ,
										c.cardname ,
										a.debit ,
										a.credit ,
										a.credit - a.debit amount ,
										case when isnull(a.fcCurrency,'IDR') ='IDR' then 'IDR' else a.fccurrency end currency,
										case when isnull(a.fcCurrency,'IDR') = 'IDR' then a.credit - a.debit  else  a.fccredit - a.fcdebit end FCAmount ,
										a.BalScCred - a.BalScDeb balance,
										a.linememo ,
										a.ref1 , a.ref2
							from jdt1 a 
							inner join ojdt b on a.Transid = b.transid 
							inner join ocrd c on a.shortname  = c.cardcode 
							inner join ocrg d on c.groupcode = d.groupcode
							left outer join [@igu_transtype] e on a.transtype = e.code 
							where a.account = @account 
							and convert(varchar,a.refdate ,23 ) between @datefrom and @dateto
 
				"""
			
			data = pandas.io.sql.read_sql(msgsql,conn) 
			listfinal.append(data)
  
		


		df = pd.concat(listfinal)  

		if self.export_to=="list":
			self.env.cr.execute ("""DELETE FROM cnw_awr28_kartuhutang WHERE create_uid =""" + str(self.env.user.id) + """ """ ) 
			
			datalist2 = df.values.tolist()

			for line in datalist2:
				self.env["cnw.awr28.kartuhutang"].create({
											"companycode"		: line[0],   
											"transno"			: line[1],  
											"refdate"			: line[2],  
											"transname"			: line[3],  
											"groupname"			: line[4],  
											"cardcode"			: line[5],  
											"cardname"			: line[6],  
											"debit"				: line[7],  
											"credit"			: line[8],  
											"amount"			: line[9],  
											"currency"			: line[10],  
											"fcamount"			: line[11],  
											"balance"			: line[12],  
											"linememo"			: line[13],  
											"ref1"				: line[14],  
											"ref2"				: line[15] 
											})
			return {
				"type": "ir.actions.act_window",
				"res_model": "cnw.awr28.kartuhutang",  
				#"view_id":view_do_list_tree, 
				"view_mode":"tree,pivot",
				"act_window_id":"cnw_awr28_kartuhutang_action"}

		if self.export_to =="xls":
			filename = filenamexls2 
			#report = df.groupby(["Group","AR Person"]).sum()
			df.to_excel(mpath + '/temp/'+ filenamexls2,index=False,engine='xlsxwriter') 
		if self.export_to =="json":
			filename = filenamejson
			df.to_json(mpath + '/temp/'+ filenamejson,orient="records")
		if self.export_to =="pdf":
				   
			filename = filenamepdf
			env = Environment(loader=FileSystemLoader(mpath + '/template/'))
			newdf2 = df[["cardcode","cardname","refdate","transno","debit","credit","currency","fcamount","linememo"]]
			template = env.get_template("kartuhutang_Template.html")            
			template_var = { 
							"igu_title" :igu_title,
							"igu_tanggal" :igu_tanggal ,
							"igu_remarks" :igu_remarks ,
							"detail": newdf2.to_html(float_format='{:20,.2f}'.format,index=False)}
			
			html_out = template.render(template_var)
			pdfkit.from_string(html_out,mpath + '/temp/'+ filenamepdf,options=options,css=cssfile) 
	 
		
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

 