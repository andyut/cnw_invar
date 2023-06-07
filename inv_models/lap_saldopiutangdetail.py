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
import pyodbc  
from jinja2 import Environment, FileSystemLoader
import pdfkit

 

class CNWLapSaldoPiutangDetailEmailDetail (models.TransientModel):
	_name           = "cnw.invar.saldopiutangdetailemail.detail"
	_description    =  "cnw.invar.saldopiutangdetailemail.detail"
	name 			= fields.Char("Name" , required=True)
	email 			= fields.Char("Email Address", required=True)

	 
	piutang_id 		= fields.Many2one("cnw.invar.saldopiutangdetailemail")

class CNWLapSaldoPiutangDetailEmail(models.TransientModel):
	_name           = "cnw.invar.saldopiutangdetailemail"
	_description    =  "cnw.invar.saldopiutangdetailemail"
	 
	  
	email_subject   = fields.Char("Subject",default="Your Unpaid Invoice for Indoguna")


	email_body      = fields.Html("Email Body", default="Here is your  Unpaid Invoice ")
	email_to        = fields.Char("To",default="ar@indoguna.co.id")
	email_from      = fields.Char("from",default="ar@indoguna.co.id")

	


	filexls         = fields.Binary("File Output")    
	filenamexls     = fields.Char("File Name Output")

	piutang_ids		= fields.Many2many("jas.lap.mailaddress",string="Email Client")
	def check_list(self):
		mpath       = get_module_path('cnw_invar') 
		cardname = ""
		piutang = self.env['cnw.invar.saldopiutangdetailmodels'].browse(self._context.get('active_ids', []))


		#print("web/content/?model=" + self._name +"&id=" + str(self.id) + "&filename_field=filenamexls&field=filexls&download=true&filename=" + self.filenamexls)
		indate = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d")
		subject = "[" + self.env.user.company_id.name + "] Your Unpaid Invoice " 
		strtable = ""
		#print("print sampe sini")
		total = 0.0
		for inv in piutang:
			strtable +="<tr>" 
			strtable +="<td>" + inv.doctype + "</td> \n"  
			strtable +="<td>" + str(inv.docdate) + "</td> \n"
			strtable +="<td>" + str(inv.docnum) + "</td> \n"
			strtable +="<td>" + str(inv.po) + "</td> \n"
			strtable +="<td>" + str(inv.numatcard) + "</td> \n" 

			kwitansi = inv.kwitansi if inv.kwitansi else ""
			fp = inv.fp if inv.fp else "" 

			strtable +="<td>" + kwitansi + "</td> \n"
			strtable +="<td>" + fp + "</td> \n" 
			strtable +="<td style='text-align: right;' >" + str("{:,.2f}".format(inv.dpp)) + "</td> \n"
			strtable +="<td style='text-align: right;' >" + str("{:,.2f}".format(inv.ppn)) + "</td> \n"
			strtable +="<td style='text-align: right;' >" + str("{:,.2f}".format(inv.amount)) + "</td> \n"
			strtable +="<td style='text-align: right;' >" + str("{:,.2f}".format(inv.balance)) + "</td> \n"
			total += inv.balance
			strtable +="<t>"
			strtable +="</tr>"
			cardname = inv.cardname
		dataline=[]
		for email in self.piutang_ids :
			linedetail={}
			linedetail["name"]= email.name 
			linedetail["email"]=email.mailaddress 
			dataline.append(linedetail)

		env = Environment(loader=FileSystemLoader(mpath + '/template/'))
		template = env.get_template("email_piutang.html")     			
		template_var = {"cardname":cardname,  
						"body": self.email_body,
						"detail" :strtable  ,
						"ar_person": self.env.user.name,
						"ar_email" : self.env.user.x_igu_email,
						"total" : "{:,.2f}".format(total)
						}
		html_out =  template.render(template_var)
		botmail =   self.env["cnw.botmail.master"].search([])
		url = "https://api.sendinblue.com/v3/smtp/email"

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

class CNWLapSaldoPiutangDetailModels(models.Model):
	_name           = "cnw.invar.saldopiutangdetailmodels"
	_description    = "Saldo Piutang Detail Models view" 
	name            = fields.Char("IDX")
	doctype			= fields.Char("Doc Type")
	comp_name 		= fields.Char("Company Name")
	docdate         = fields.Date ("Date")
	taxdate         = fields.Date ("Document Date")
	docduedate		= fields.Date ("Document Date")
	docnum          = fields.Char("Docnum")
	docentry 		= fields.Char("DocEntry")
	po          	= fields.Char("PO")
	numatcard       = fields.Char("Sales Order")
	kwitansi        = fields.Char("Kwitansi")
	fp              = fields.Char("Faktur Pajak")
	cardcode        = fields.Char("Card Code")
	cardname        = fields.Char("Card Name")
	shiptocode		= fields.Char("ShipTo")
	amount          = fields.Float("Total")
	ppn         	= fields.Float("ppn")
	dpp         	= fields.Float("Amount")
	balance         = fields.Float("Balance")

# extra
	doctype 		= fields.Char("DocType")
	objtype 		= fields.Char("ObjType")
	tfdate			= fields.Date("TukarFaktur Date")
	lt_no 			= fields.Char("TF No")
	remdelay 		= fields.Text("Customer Remarks")
	nogiro 			= fields.Char("No Giro")
	tglgiro			= fields.Date("Tgl Giro")
	checklist 		= fields.Char("CheckList")
	checklistdate	= fields.Date("Checklist Date")
	gr_no 			= fields.Char("GR No")
	arperson 			= fields.Char("AR Person")
	transtype 		= fields.Char("TransType")

	top_count 		= fields.Float("TOP Count")
	top_desc 		= fields.Float("TOP Description")
	datediff 		= fields.Float("Date Diff")
	denda 			= fields.Float("Denda",default=0.0)
	denda_status	= fields.Selection("TOP Count")


class CNWLapSaldoPiutangDetail(models.TransientModel):
	_name           = "cnw.invar.saldopiutangdetail"
	_description    = "Saldo Piutang Detail"
	company_id      = fields.Many2many('res.company', string='Company', required=True )

	dateto          = fields.Date("Date To",default=lambda s:fields.Date.today())
	customer        = fields.Char("Business Partner",default="")
	arperson        = fields.Char("AR Person",default="")
	filexls         = fields.Binary("File Output",default=" ")    
	filenamexls     = fields.Char("File Name Output",default="EmptyText.txt")
	account         = fields.Selection(string="Account", selection=[
																	("1130001","1130001-PIUTANG DAGANG"),
																	("1135001","1135001-PIUTANG SEWA"),
																	("1135002","1135002-PIUTANG PENGIRIMAN BARANG"),
																	("1135003","1135003-PIUTANG PENITIPAN BARANG"),
																	("1135004","1135004-PIUTANG LAIN LAIN"),
																	("1135005","1135005-PIUTANG  HANDLING"),
																	("1137001","1137001-PIUTANG PPH23"),
																	("","ALL"),],
																	default="1130001")	
	export_to       = fields.Selection([ ('list','List 	'),('xlssummary', 'Excel Summary'),('xls', 'Excel'),('pdf', 'PDF'),],string='Export To', default='pdf')

	def get_saldopiutangdetail(self):

#PATH & FILE NAME & FOLDER
		mpath       = get_module_path('cnw_invar')
		filenamexls2    = 'SaldoPiutangDetail_'+   datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d%H%M%S") + '.xlsx'
		filenamepdf    = 'SaldoPiutangDetail_'+   datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d%H%M%S")  + '.pdf'
		filepath    = mpath + '/temp/'+ filenamexls2

		 
#LOGO CSS AND TITLE
		logo        = mpath + '/template/logoigu.png' 
		#logo        = mpath + '/template/logo'+ self.company_id.code_base + '.png'
		cssfile     = mpath + '/template/style.css'        
		options = {
					'page-size': 'A4',
					'orientation': 'portrait',
					}
		igu_title = "Piutang Detail"
		igu_tanggal = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")
		igu_remarks = " Per Tanggal " + self.dateto.strftime("%Y-%m-%d")                    

#MULTI COMPANY 

		listfinal = []
		pandas.options.display.float_format = '{:,.2f}'.format
		company = ""
		account = self.account if self.account else ""
		arperson = self.arperson if self.arperson else ""
		for comp in self.company_id:

			host        = comp.server
			database    = comp.db_name
			user        = comp.db_usr
			password    = comp.db_pass 
			company = comp.name
			 
			#conn = pymssql.connect(host=host, user=user, password=password, database=database)

			conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';UID='+user+';PWD='+ password + ';TrustServerCertificate=yes')
			
			bp = self.customer if self.customer else ""

			msgsql ="""
						declare @datefrom varchar(20), @dateto varchar(20) ,@arperson varchar(20)
						declare @cardname varchar(50), @account varchar(10)

						declare @table table (  docentry int ,
												docdate varchar(10),			
												documentdate varchar(10),						
                                                docduedate varchar(10)	,						
												docnum varchar(20) ,
												numatcard varchar(200)  ,
												kwitansi varchar(200) ,
												fp varchar(50) ,
												cardcode varchar(20),
												cardname varchar(100),
												shipto 	varchar(100),
												amount numeric(19,6) ,
												balance numeric(19,6),
												po varchar(100) ,
												dpp numeric(19,6) ,
												ppn numeric(19,6),
                                                DocType varchar(100),
                                                DocSubType varchar(100),
                                                U_TF_date varchar(100),
                                                U_LT_No  varchar(100),
                                                U_RemDelay varchar(200),
                                                U_No_Giro varchar(200),
                                                U_Tgl_Jt_Tempo_Giro varchar(100),
                                                U_IGU_Checklist varchar(100),
                                                U_IGU_checklistdate varchar(100),
                                                U_Cust_GR_No varchar(100),
												arperson varchar(50),
                                                transtype varchar(100))
 
						set     @DateTo   = '""" + self.dateto.strftime("%Y-%m-%d")  + """'
						set     @CardCode = '""" + bp + """'
						set     @account  = '""" + account + """'
						set     @arperson = '""" + arperson + """'

						insert into @table 
						select  
                                a.docentry ,  
								convert(varchar,a.docdate,23) docdate , 
								convert(varchar,a.taxdate,23) taxdate , 
								convert(varchar,a.docduedate,23) Docduedate , 
								a.docnum , 
								a.numatCard,
								a.U_Kw_No ,
								a.U_IDU_FPajak ,
								a.cardcode, 
								b.cardname,
								a.shiptocode,
								a.DocTotal , 
								a.DocTotal - a.paidsys balance,
								ISNULL(A.U_CUST_PO_NO,'') po ,
								a.doctotal - a.vatsum amount, 
								a.vatsum ppn ,
                                a.DocType doctype,
                                a.DocSubType docsubtype,
                                a.U_TF_date tf_date,
                                a.U_LT_No Penagihan_No,
                                a.U_RemDelay DelayRemarks,
                                a.U_No_Giro ,
                                a.U_Tgl_Jt_Tempo_Giro ,
                                a.U_IGU_Checklist ,
                                a.U_IGU_checklistdate ,
                                a.U_Cust_GR_No,
								b.U_AR_Person ,
								'Invoice' transtype
								

						from oinv a
						inner join ocrd b on a.cardcode = b.cardcode 
						where a.canceled='N' and a.DocStatus='O' 
						and a.ctlAccount = @Account 
						and a.cardcode + a.cardname like '%' +  @cardname + '%'
						and isnull(B.U_AR_Person,'')  like '%' +  @arperson + '%'
						and (a.DocTotal - a.paidsys)<>0 
						and convert(varchar,a.docdate,112) <= @dateto


						insert into @table 
						select  
                                a.docentry ,
                                convert(varchar,a.docdate,23) docdate , 
								convert(varchar,a.taxdate,23) taxdate , 
								convert(varchar,a.docduedate,23) docduedate , 
								a.docnum , 
								a.numatCard,
								a.U_Kw_No ,
								a.U_IDU_FPajak ,
								a.cardcode, 
								b.cardname,
								a.shiptocode,
								-1 * (a.DocTotal) , 
								-1 * (a.DocTotal - a.paidsys) ,
								ISNULL(A.U_CUST_PO_NO,''),
								-1 * (a.doctotal - a.vatsum) amount, 
								-1 * (a.vatsum) ppn,
                                a.DocType doctype,
                                a.DocSubType docsubtype,
                                a.U_TF_date tf_date,
                                a.U_LT_No Penagihan_No,
                                a.U_RemDelay DelayRemarks,
                                a.U_No_Giro ,
                                a.U_Tgl_Jt_Tempo_Giro ,
                                a.U_IGU_Checklist ,
                                a.U_IGU_checklistdate ,
                                a.U_Cust_GR_No,
								b.U_AR_Person ,
								'CN' doctype
						from orin a
						inner join ocrd  b on a.cardcode = b.cardcode 
						where a.canceled='N' and a.DocStatus='O' 
						and a.ctlAccount = @Account 
						and a.cardcode + a.cardname  like '%' +  @cardname + '%'
						and isnull(B.U_AR_Person,'')  like '%' +  @arperson + '%'
						and (a.DocTotal - a.paidsys)<>0
						and convert(varchar,a.docdate,112) <= @dateto

						insert into @table 
						select  a.transid , 
								convert(varchar,a.refdate,23) docdate , 
								convert(varchar,a.taxdate,23) taxdate , 
								convert(varchar,a.duedate,23) duedate , 
								c.number Docnum  , 
								c.number numatCard,
								isnull(c.u_trans_no,'') +'-' + a.LineMemo U_Kw_No ,
								'' U_IDU_FPajak ,
								a.ShortName, 
								b.cardname,
								b.shiptodef,
								(a.BalScDeb - a.BalScCred ), 
								(a.BalScDeb - a.BalScCred) balance,
								''  po ,
								(a.BalScDeb - a.BalScCred) amount, 
								0 ppn ,
                                ''  doctype,
                                ''   docsubtype,
                                '' tf_date,
                                ''  Penagihan_No,
                                ''  DelayRemarks,
                                '' U_No_Giro ,
                                '' U_Tgl_Jt_Tempo_Giro ,
                                '' U_IGU_Checklist ,
                                '' U_IGU_checklistdate ,
                                '' U_Cust_GR_No,
								b.U_AR_Person ,
								'UnReconsile' trasntype
								

						from JDT1 a
						inner join ocrd b on a.ShortName = b.cardcode and a.TransType in (24,30)
                        inner join ojdt c on a.transid = c.transid 
						where  b.cardcode + b.cardname like '%' +  @cardname + '%'
						and isnull(B.U_AR_Person,'')  like '%' +  @arperson + '%'
						and a.Account = @Account 
						and (a.BalScDeb - a.BalScCred)<>0 
						and convert(varchar,a.refdate,112) <= @dateto

						select  *,'""" + comp.code_base + """' company from @table    
						order by docdate ,docnum             
			"""
			#print(msgsql)
			data = pandas.io.sql.read_sql(msgsql,conn) 
			listfinal.append(data)
  
		


		df = pd.concat(listfinal)  

		if self.export_to=="list":
			self.env.cr.execute ("""DELETE FROM cnw_invar_saldopiutangdetailmodels WHERE create_uid =""" + str(self.env.user.id) + """ """ ) 
			
			datalist2 = df.values.tolist()

			for line in datalist2:
				self.env["cnw.invar.saldopiutangdetailmodels"].create({
											"docentry" 			: line[1],  
											"docdate" 			: line[1],  
											"taxdate" 			: line[1],  
											"docduedate" 			: line[1],  
											"docnum" 			: line[1],  
											"numatcard" 			: line[1],  
											"kwitansi" 			: line[1],  
											"fp" 			: line[1],  
											"cardcode" 			: line[1],  
											"cardname" 			: line[1],  
											"shiptocode" 			: line[1],  
											"amount" 			: line[1],  
											"balance" 			: line[1],  
											"po" 			: line[1],  
											"dpp" 			: line[1],  
											"ppn" 			: line[1],  
											"doctype" 			: line[1],  
											"objtype" 			: line[1],  
											"tfdate" 			: line[1],  
											"lt_no" 			: line[1],  
											"remdelay" 			: line[1],  
											"nogiro" 			: line[1],  
											"tglgiro" 			: line[1],  
											"checklist" 			: line[1],  
											"checklistdate" 			: line[1],  
											"gr_no" 			: line[1],  
											"arperson" 			: line[1],  
											"transtype" 			: line[1],  
											 
											})
			return {
				"type": "ir.actions.act_window",
				"res_model": "cnw.invar.saldopiutangdetailmodels",  
				#"view_id":view_do_list_tree, 
				"view_mode":"tree,pivot",
				"act_window_id":"cnw_invar_saldopiutangdetailmodels_action"}

		if self.export_to =="xls":
			filename = filenamexls2 
			#report = df.groupby(["Group","AR Person"]).sum()
			df.to_excel(mpath + '/temp/'+ filenamexls2,index=False,engine='xlsxwriter') 

		if self.export_to =="xlssummary":
			filename = filenamexls2 
			#report = df.groupby(["Group","AR Person"]).sum()
			newdf2 = df[["shipto","docdate","docnum","numatcard","kwitansi","po","amount","balance"]]
			newdf2.to_excel(mpath + '/temp/'+ filenamexls2,index=False,engine='xlsxwriter') 


		if self.export_to =="pdf":
				   
			filename = filenamepdf
			env = Environment(loader=FileSystemLoader(mpath + '/template/'))
			 
			
			newdf2b =  df[["docnum","docdate","numatcard","kwitansi","fp", "balance","cardcode","cardname"]].values.tolist() 
			
			icardcode = ""
			icardname = ""
			total = 0.0
			for iline in newdf2b :
				icardcode = iline[6]
				icardname = iline[7]
				total	  += iline[5]

			
			template = env.get_template("saldopiutangDetail.html")            
			template_var = {"logo":logo,
							"igu_title" :igu_title,
							"igu_tanggal" :igu_tanggal ,
							"igu_remarks" :igu_remarks ,
							"cardname" :icardname ,
							"cardcode" :icardcode ,
							"total" : total,
							"detail": newdf2b}
			
			html_out = template.render(template_var)
			pdfkit.from_string(html_out,mpath + '/temp/'+ filenamepdf,options=options) 
	 
		 
		
	   # SAVE TO MODEL.BINARY 
		file = open(mpath + '/temp/'+ filename , 'rb')
		out = file.read()
		file.close()
		self.filexls =base64.b64encode(out)
		self.filenamexls = filename
		os.remove(mpath + '/temp/'+ filename )
		if self.export_to !="pdf":
			return {
				'name': 'Report',
				'type': 'ir.actions.act_url',
				'url': "web/content/?model=" + self._name +"&id=" + str(
					self.id) + "&filename_field=filenamexls&field=filexls&download=true&filename=" + self.filenamexls,
				'target': 'new',
				}
		else :
			return {
				'type': 'ir.actions.do_nothing'
				}
		

 