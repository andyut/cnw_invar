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


class CNWLapSaldoHutangDetailEmail(models.TransientModel):
	_name           = "cnw.awr28.saldohutangdetailemail"
	_description    =  "cnw.awr28.saldohutangdetailemail"
	 
	  
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
		hutang = self.env['cnw.awr28.saldohutangdetail'].browse(self._context.get('active_ids', []))


		#print("web/content/?model=" + self._name +"&id=" + str(self.id) + "&filename_field=filenamexls&field=filexls&download=true&filename=" + self.filenamexls)
		indate = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d")
		subject = "[" + self.env.user.company_id.name + "] Konfirmasi Hutang " 
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
		subject = "[" + self.env.user.company_id.name + "] Konfirmasi Hutang   "  + cardname
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



class CNW_saldohutangdetail(models.Model):
	_name           = "cnw.awr28.saldohutangdetail"
	_description    = "cnw.awr28.saldohutangdetail"
	company_id      = fields.Char("Company")
	name            = fields.Char("TransID")
	ponumber 		= fields.Char("PO Number")
	transname       = fields.Char("Trans Name")
	account         = fields.Char("Account")
	docnum          = fields.Char("Doc Number")
	docdate         = fields.Date("Doc Date")
	etadate         = fields.Date("ETA Date")
	reqpaymentdate  = fields.Date("Request Payment Date")
	cardcode        = fields.Char("Partner Code")
	cardname        = fields.Char("Partner Name")
	docref          = fields.Char("Ref")
	taxnumber       = fields.Char("Tax No (NPWP)")
	fakturpajak     = fields.Char("Faktur Pajak")
	igroup          = fields.Char("Partner Group")
	currency        = fields.Char("Currency")
	balancefc       = fields.Float("Balance Foreign Currency",default=0.0)
	balancesy       = fields.Float("Balance Local Currency",default=0.0)
	

	


class CNW_saldohutangdetailget(models.TransientModel):
	_name           = "cnw.awr28.saldohutangdetail.get"
	_description    = "cnw.saldohutangdetail.get"
	company_id      = fields.Many2many('res.company', string="Company",required=True)
	 
	dateto          = fields.Date ("Date To", default=fields.Date.today()) 
	partner 		= fields.Char("Partner")
	account         = fields.Selection(string="Account", selection=[("2110001","2110001-HUTANG DAGANG"),("2175002","2175002-HUTANG ACTIVA")],default="2110001")
	filexls         = fields.Binary("File Output")    
	filenamexls     = fields.Char("File Name Output")
	
	export_to       = fields.Selection([ ('list','List 	'), ('xls', 'Excel'),('pdf', 'PDF'),],string='Export To', default='list')

	
	def view_saldohutangdetail(self): 
		mpath       	= get_module_path('cnw_awr28')
		filenamexls2    = 'SaldoHUtangDetail_'+   self.dateto.strftime("%Y%m%d")  + '.xlsx'
		filenamepdf    	= 'SaldoHUtangDetail_'+   self.dateto.strftime("%Y%m%d")  + '.pdf'
		filepath    = mpath + '/temp/'+ filenamexls2

		 
#LOGO CSS AND TITLE
		logo        = mpath + '/template/logoigu.png' 
		cssfile     = mpath + '/template/style.css'        
		options = {
					'page-size': 'A4',
					'orientation': 'landscape',
					}
		igu_title = "Saldo Hutang Detail"
		igu_tanggal = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")
		igu_remarks = "Saldo Hutang Detail Per Tanggal " + self.dateto.strftime("%Y-%m-%d")   	                 

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
			
			msgsql =""" DECLARE @DATETO varchar(10),
									@vendor varchar(50),
									@account varchar(20)
						SET NOCOUNT ON
							declare @table table ( 
													transid varchar(50) ,
													transname varchar(100) ,
													account varchar(50) ,
													docnum varchar(20) ,
													docdate varchar(20) ,
													eta varchar(20) ,
													reqpayment varchar(20) ,
													cardcode varchar(20) ,
													cardname varchar(100) ,
													ref1 varchar(100) ,
													taxnumber varchar(50) ,
													fakturpajak varchar(50) ,
													igroup varchar(20) ,
													currency varchar(10) ,
													balancefc numeric(19,6) ,
													balancesy numeric(19,6) ,po_number varchar(50))

							set @account = '""" + self.account + """'
							set @vendor = '""" + bp + """'
							set @dateto = '""" + self.dateto.strftime("%Y%m%d")  + """'

							insert into @table 
							select  A.TransId,
									'AP INVOICE' transName,
									a.account ,
									b.docnum ,
									convert(varchar,b.docdate,23) docdate ,
									convert(varchar,b.docduedate,23) ETA,
									convert(varchar,b.taxdate,23)  ReqPaymentDate,
									c.cardcode ,
									c.cardname  , 
									b.numatcard,
									c.LicTradNum taxnumber,
									b.U_IDU_FPajak, 
									d.groupname igroup ,
									b.DocCur ,
									a.BalFcCred - a.BalFcDeb ,
									a.BalScCred - a.BalScDeb ,
        							convert(varchar,bb.docnum)

							from JDT1 a
								inner join OPCH B On a.TransId = b.TransId and a.transtype = b.ObjType 
    							left outer  join opor Bb On b.U_IGU_SOdocEntry = bb.docentry
								inner join ocrd c on b.cardcode = c.cardcode 
								inner join ocrg d on c.groupcode = d.groupcode 
							where a.account = @account 
							and convert(varchar,a.refdate,112)<=@DATETO
							and a.BalScCred - a.BalScDeb <>0
							and c.cardcode + c.cardname like '%"""  +  bp + """%'
							union all
							select  A.TransId,
									'AP CreditNote' transName,
									a.account ,
									b.docnum ,
									convert(varchar,b.docdate,23) docdate ,
									convert(varchar,b.docduedate,23) ETA,
									convert(varchar,b.taxdate,23)  ReqPaymentDate,
									c.cardcode ,
									c.cardname  , 
									b.numatcard,
									c.LicTradNum taxnumber,
									b.U_IDU_FPajak, 
									d.groupname igroup ,
									b.DocCur ,
									a.BalFcCred - a.BalFcDeb ,
									a.BalScCred - a.BalScDeb ,
        							convert(varchar,bb.docnum)

							from JDT1 a
								inner join ORPC B On a.TransId = b.TransId and a.transtype = b.ObjType 
    							left outer  join opor Bb On b.U_IGU_SOdocEntry = bb.docentry
								inner join ocrd c on b.cardcode = c.cardcode 
								inner join ocrg d on c.groupcode = d.groupcode 
							where a.account = @account 
							and convert(varchar,a.refdate,112)<=@DATETO
							and a.BalScCred - a.BalScDeb <>0
							and c.cardcode + c.cardname like '%"""  +  bp + """%'
							union all
							select  A.TransId,
									'AP DOWNPAYMENT' transName,
									a.account ,
									b.docnum ,
									convert(varchar,b.docdate,23) docdate ,
									convert(varchar,b.docduedate,23) ETA,
									convert(varchar,b.taxdate,23)  ReqPaymentDate,
									c.cardcode ,
									c.cardname  , 
									b.numatcard,
									c.LicTradNum taxnumber,
									b.U_IDU_FPajak, 
									d.groupname igroup ,
									b.DocCur ,
									a.BalFcCred - a.BalFcDeb ,
									a.BalScCred - a.BalScDeb ,
        							convert(varchar,bb.docnum)

							from JDT1 a
								inner join ODPO B On a.TransId = b.TransId and a.transtype = b.ObjType 
    							left outer  join opor Bb On b.U_IGU_SOdocEntry = bb.docentry
								inner join ocrd c on b.cardcode = c.cardcode 
								inner join ocrg d on c.groupcode = d.groupcode 
							where a.account = @account 
							and convert(varchar,a.refdate,112)<=@DATETO
							and a.BalScCred - a.BalScDeb <>0
							and c.cardcode + c.cardname like '%"""  +  bp + """%'

							union all
							select  A.TransId,
									'OUTGOING PAYMENT' transName,
									a.account ,
									b.docnum ,
									convert(varchar,b.docdate,23) docdate ,
									convert(varchar,b.docduedate,23) ETA,
									convert(varchar,b.taxdate,23)  ReqPaymentDate,
									c.cardcode ,
									c.cardname  , 
									b.U_Trans_No,
									c.LicTradNum taxnumber,
									'' FakturPajak,
									d.groupname igroup ,
									b.DocCurr ,
									a.BalFcCred - a.BalFcDeb ,
									a.BalScCred - a.BalScDeb ,
									convert(varchar,b.docnum) + '-' + isnull(b.U_Trans_No,'') 

							from JDT1 a
								inner join OVPM B On a.TransId = b.TransId and a.transtype = b.ObjType 
								inner join ocrd c on b.cardcode = c.cardcode 
								inner join ocrg d on c.groupcode = d.groupcode 
							where a.account = @account 
							and convert(varchar,a.refdate,112)<=@DATETO
							and a.BalScCred - a.BalScDeb <>0
							and c.cardcode + c.cardname like '%"""  +  bp + """%'
							union all
							select  A.TransId,
									'JURNAL ENTRY' transName,
									a.account , 
									b.number ,
									convert(varchar,b.refdate,23) docdate ,
									convert(varchar,b.duedate,23) ETA,
									convert(varchar,b.taxdate,23)  ReqPaymentDate,
									c.cardcode ,
									c.cardname  , 
									b.U_Trans_No,
									c.LicTradNum taxnumber,
									'' FakturPajak,
									d.groupname igroup ,
									case isnull(a.FCCurrency,'')  when '' then 'IDR' ELSE a.FCCurrency end docur  ,
									a.BalFcCred - a.BalFcDeb  BalanceFC,
									a.BalScCred - a.BalScDeb BalanceSy ,
									isnull(b.U_Trans_No,'') 

							from JDT1 a
								inner join OJDT B On a.TransId = b.TransId and a.transtype = b.ObjType 
								inner join ocrd c on c.cardcode = a.shortname 
								inner join ocrg d on c.groupcode = d.groupcode 
							where a.account = @account 
							and convert(varchar,a.refdate,112)<=@DATETO
							and a.BalScCred - a.BalScDeb <>0
							and c.cardcode + c.cardname like '%"""  +  bp + """%'


							select '""" + comp.code_base + """' Company , * from @table order by cardcode, docdate , transname
				"""
			
			data = pandas.io.sql.read_sql(msgsql,conn) 
			listfinal.append(data)
  
		


		df = pd.concat(listfinal)  

		if self.export_to=="list":
			self.env.cr.execute ("""DELETE FROM cnw_awr28_saldohutangdetail WHERE create_uid =""" + str(self.env.user.id) + """ """ ) 
			
			datalist2 = df.values.tolist()

			for line in datalist2:
				self.env["cnw.awr28.saldohutangdetail"].create({
											"company_id"		: line[0],  
											"name" 				: line[1],  
											"transname"			: line[2],
											"account"			: line[3],
											"docnum"			: line[4],
											"docdate"			: line[5],
											"etadate"			: line[6],
											"reqpaymentdate"	: line[7],
											"cardcode"			: line[8],
											"cardname"			: line[9], 
											"docref"			: line[10],
											"taxnumber"			: line[11],
											"fakturpajak"		: line[12],
											"igroup"			: line[13],
											"currency"			: line[14],
											"balancefc"			: line[15],
											"balancesy"			: line[16],
											"ponumber" 			: line[17]
											})
			return {
				"type": "ir.actions.act_window",
				"res_model": "cnw.awr28.saldohutangdetail",  
				#"view_id":view_do_list_tree, 
				"view_mode":"tree,pivot",
				"act_window_id":"cnw_awr28_saldohutangdetail_action"}

		if self.export_to =="xls":
			filename = filenamexls2 
			#report = df.groupby(["Group","AR Person"]).sum()
			df.to_excel(mpath + '/temp/'+ filenamexls2,index=False,engine='xlsxwriter') 
  
		if self.export_to =="pdf":
				   
			filename = filenamepdf
			env = Environment(loader=FileSystemLoader(mpath + '/template/'))
			newdf2 = df[["company_id","ponumber","docnum","docdate","cardcode","cardname","docref","currency","balancefc","balancesy"]]
			template = env.get_template("saldoHutangDetail_Template.html")            
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

 