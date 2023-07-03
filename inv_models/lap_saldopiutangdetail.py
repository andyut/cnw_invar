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
import pymssql  
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
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)

	name            = fields.Char("IDX")
	doctype			= fields.Char("Doc Type")
	comp_name 		= fields.Char("Company Name")
	docdate         = fields.Date ("Invoice Date")
	taxdate         = fields.Date ("TF")
	docduedate		= fields.Date ("Due")
	docnum          = fields.Char("Docnum")
	docentry 		= fields.Char("DocEntry")
	po          	= fields.Char("PO")
	numatcard       = fields.Char("SO")
	kwitansi        = fields.Char("KW")
	fp              = fields.Char("FP")
	cardcode        = fields.Char("CardCode")
	cardname        = fields.Char("Customer")
	cardgroup        = fields.Char("Customer Group")
	shiptocode		= fields.Char("ShipTo")
	amount          = fields.Float("Total")
	ppn         	= fields.Float("ppn")
	dpp         	= fields.Float("Amount")
	balance         = fields.Float("Balance")

# extra
	doctype 		= fields.Char("DocType")
	objtype 		= fields.Char("ObjType")
	tfdate			= fields.Date("TF Date")
	lt_no 			= fields.Char("TF No")
	remdelay 		= fields.Text("Customer Remarks")
	nogiro 			= fields.Char("No Giro")
	tglgiro			= fields.Date("Tgl Giro")
	checklist 		= fields.Char("CheckList")
	checklistdate	= fields.Date("Checklist Date")
	gr_no 			= fields.Char("GR No")
	arperson 		= fields.Char("AR")
	transtype 		= fields.Char("iType")
 
	topdays 		= fields.Float("ToP Days")
	topdesc 		= fields.Char("ToP Description")
	datediff 		= fields.Float("Late(Day(s))")
	denda 			= fields.Float("late charge",default=0.0)
	dendastatus		= fields.Selection(string="Status Denda " , selection=[("Y","Y"),("N","N")],default="N")
	txtlog			= fields.Text("debug mode")
	tfstatus 		= fields.Selection(string="TF Status", selection=[("Y","Y"),("N","N")] ,default="N")

	collector 		= fields.Char("Collector")
	notes1			= fields.Char("Notes1")

	salesperson 	= fields.Char("Sales")
	jadwal 			= fields.Char("Jadwal")
# print invoice
	filexls         = fields.Binary("File Output",default=" ")    
	filenamexls     = fields.Char("File Name Output",default="EmptyText.txt")
	
	def get_CetakanInvoice(self):
		mpath       = get_module_path('cnw_invar') 
		filenamepdf    = 'invoice_'+   self.docentry  +  self.env.user.name +  '.pdf'
		filenamepdf    = 'invoice_'+   self.docentry     +  self.env.user.name +   '.pdf'
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
		
		msgsql =  """exec [dbo].[IGU_ACT_INVOICE_HEADER]  '""" + self.docnum +  """','""" + self.docnum +  """','""" + self.docdate.strftime("%Y%m%d")  +  """','""" + self.docdate.strftime("%Y%m%d") +  """' """
		msgsql2 =  """exec [dbo].[IGU_ACT_INVOICE_DETAIL]  '""" + self.docnum +  """','""" + self.docnum  +  """','""" + self.docdate.strftime("%Y%m%d")  +  """','""" + self.docdate.strftime("%Y%m%d") +  """' """
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
 
		return {
			'name': 'Report',
			'type': 'ir.actions.act_url',
			'url': "web/content/?model=" + self._name +"&id=" + str(
			self.id) + "&filename_field=filenamexls&field=filexls&download=true&filename=" + self.filenamexls,
			'target': 'new',
			}
	
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
	export_to       = fields.Selection([ ('list','List 	'),('xlssummary', 'Excel Summary'),('xls', 'Excel'),('pdf', 'PDF'),],string='Export To', default='list')

	def get_saldopiutangdetail(self):

#PATH & FILE NAME & FOLDER
		mpath       = get_module_path('cnw_invar')
		filex  		= 'SaldoPiutangDetail_'+   datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y%m%d%H%M%S")
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
		bp = self.customer if self.customer else "" 
		
		for comp in self.company_id:

			host        = comp.server
			database    = comp.db_name
			user        = comp.db_usr
			password    = comp.db_pass 
			company = comp.name
			 
			#conn = pymssql.connect(host=host, user=user, password=password, database=database)

			conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';UID='+user+';PWD='+ password + ';TrustServerCertificate=yes')
			

			msgsql ="""
						declare @datefrom varchar(20), @dateto varchar(20) ,@arperson varchar(20)
						declare @cardname varchar(50), @account varchar(10)
						set nocount on
						declare @table table (   docentry int ,
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
                                                ObjType varchar(100),
                                                U_TF_date varchar(100),
                                                U_LT_No  varchar(100),
                                                U_RemDelay varchar(200),
                                                U_No_Giro varchar(200),
                                                U_Tgl_Jt_Tempo_Giro varchar(100),
                                                U_IGU_Checklist varchar(100),
                                                U_IGU_checklistdate varchar(100),
                                                U_Cust_GR_No varchar(100),
												arperson varchar(50),
                                                transtype varchar(100),
												topcount int ,
												topdesc varchar(200),
												datediff numeric(19,2),
												denda numeric(19,2),
												dendastatus varchar(5),
												tfstatus varchar(5),
												groupname varchar(50),
												collector varchar(50) ,
												salesperson varchar(50) ,
												jadwal varchar(100)
												)

						set @dateto = '""" + self.dateto.strftime("%Y%m%d")     + """'
						set @cardname = '""" + bp + """'
					    set @ACCOUNT = '""" + account    + """'
						set @arperson = '""" + arperson     + """'

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
                                a.ObjType ObjType,
                                 ISNULL(a.U_TF_date,'') tf_date,
                                a.U_LT_No Penagihan_No,
                                a.U_RemDelay DelayRemarks,
                                a.U_No_Giro ,
                                a.U_Tgl_Jt_Tempo_Giro ,
                                a.U_IGU_Checklist ,
                                a.U_IGU_checklistdate ,
                                a.U_Cust_GR_No,
								b.U_AR_Person ,
								'Invoice' transtype ,
								d.ExtraDays topcount,
								d.PymntGroup ,
								DATEDIFF(day, a.DOCDUEDATE,GETDATE()),
								case when DATEDIFF(day, a.DOCDUEDATE,GETDATE()) >0 then  (a.doctotal - a.paidsys)* 0.01 else 0 end denda,
								case when DATEDIFF(day, a.DOCDUEDATE,GETDATE()) >0 then 'Y' else 'N' end  istatus ,
								case when isnull(a.U_LT_No ,'')<>'' then 'Y' else 'N' end tfstatus,
                                c.GroupName custgroup ,
								case when isnull(a.u_coll_name,'')='' then b.u_Coll_Name else a.U_Coll_Name end  collector ,
								e.slpName + ' ' + isnull(E.u_slsEmpName,'') salesname ,
								isnull(b.notes,'') jadwal


								

						from oinv a
						inner join ocrd b on a.cardcode = b.cardcode 
						inner join ocrg c on b.GroupCode = c.GroupCode 
						inner join octg d on b.GroupNum = d.GroupNum
						inner join oslp e on e.slpcode = b.slpcode
						where a.canceled='N' and a.DocStatus='O' 
						and (a.ctlAccount like '%' +  @Account +  '%'   )
						and a.cardcode + a.cardname like '%' +  @cardname + '%'
						and isnull(B.U_AR_Person,'')  like '%' +  @arperson + '%'
						and (a.DocTotal - a.paidsys)<>0 
						and convert(varchar,a.docdate,112) <= @dateto


						insert into @table 
						select  
                                a.docentry ,  
								convert(varchar,a.docdate,23) docdate , 
								convert(varchar,a.taxdate,23) taxdate , 
								convert(varchar,a.docduedate,23) Docduedate , 
								a.docnum , 
								isnull(a.numatCard,a.docnum)numatCard ,
								a.U_Kw_No ,
								isnull(a.U_IDU_FPajak,a.u_fp_no)  U_IDU_FPajak,
								a.cardcode, 
								b.cardname,
								a.shiptocode,
								-1 * a.DocTotal , 
								-1 * (a.DocTotal - a.paidsys) balance,
								ISNULL(A.U_CUST_PO_NO,'') po ,
								-1 * (a.doctotal - a.vatsum ) amount, 
								-1 * a.vatsum ppn ,
                                a.DocType doctype,
                                a.ObjType docsubtype,
                                ISNULL(a.U_TF_date,'') tf_date,
                                a.U_LT_No Penagihan_No,
                                a.U_RemDelay DelayRemarks,
                                a.U_No_Giro ,
                                a.U_Tgl_Jt_Tempo_Giro ,
                                a.U_IGU_Checklist ,
                                a.U_IGU_checklistdate ,
                                a.U_Cust_GR_No,
								b.U_AR_Person ,
								'CN' transtype ,
								d.ExtraDays topcount,
								d.PymntGroup ,
								DATEDIFF(day, a.DOCDUEDATE,GETDATE()),
								case when DATEDIFF(day, a.DOCDUEDATE,GETDATE()) >0 then  (a.doctotal - a.paidsys)* 0.01 else 0 end denda,
								case when DATEDIFF(day, a.DOCDUEDATE,GETDATE()) >0 then 'Y' else 'N' end  istatus ,
								case when isnull(a.U_LT_No ,'')<>'' then 'Y' else 'N' end tfstatus,
                                c.GroupName custgroup,
								case when isnull(a.u_coll_name,'')='' then b.u_Coll_Name else a.U_Coll_Name end   collector,
								e.slpName + ' ' + isnull(e.u_slsEmpName,'') salesname ,
								isnull(b.notes,'') jadwal
						from orin a
						inner join ocrd  b on a.cardcode = b.cardcode 
						inner join ocrg c on b.GroupCode = c.GroupCode 
						inner join octg d on b.GroupNum = d.GroupNum
						inner join oslp e on e.slpcode = b.slpcode
						where a.canceled='N' and a.DocStatus='O' 
						and  (a.ctlAccount like '%' +  @Account +  '%'   )
						and a.cardcode + a.cardname  like '%' +  @cardname + '%'
						and isnull(B.U_AR_Person,'')  like '%' +  @arperson + '%'
						and (a.DocTotal - a.paidsys)<>0
						and convert(varchar,a.docdate,112) <= @dateto

						insert into @table 
						select  a.transid , 
								convert(varchar,a.refdate,23) docdate , 
								convert(varchar,a.taxdate,23) taxdate , 
								convert(varchar,a.duedate,23) duedate , 
								e.number Docnum  , 
								e.number numatCard,
								isnull(e.u_trans_no,'') +'-' + a.LineMemo U_Kw_No ,
								'' U_IDU_FPajak ,
								a.ShortName, 
								b.cardname,
								b.shiptodef,
								(a.BalScDeb - a.BalScCred ), 
								(a.BalScDeb - a.BalScCred) balance,
								''  po ,
								(a.BalScDeb - a.BalScCred) amount, 
								0 ppn ,
                                'R'  doctype,
                                a.ObjType   docsubtype,
                                convert(varchar,a.duedate,23) tf_date,
                                ''  Penagihan_No,
                                ''  DelayRemarks,
                                '' U_No_Giro ,
                                convert(varchar,a.duedate,23) U_Tgl_Jt_Tempo_Giro ,
                                '' U_IGU_Checklist ,
                                convert(varchar,a.duedate,23) U_IGU_checklistdate ,
                                '' U_Cust_GR_No,
								b.U_AR_Person ,
								'UnReconsile' trasntype,
								d.ExtraDays topcount,
								d.PymntGroup ,
								DATEDIFF(day, a.refdate,a.refdate),
								0,
								'N',
								'N',
                                c.GroupName custgroup,
								isnull(b.u_coll_name,'') collector,
								f.slpName + ' ' + isnull(f.u_slsEmpName,'') salesname ,
								isnull(b.notes,'') jadwal

								

						from JDT1 a
						inner join ocrd b on a.ShortName = b.cardcode and a.TransType in (24,30)
						inner join ocrg c on b.GroupCode = c.GroupCode 
						inner join octg d on b.GroupNum = d.GroupNum
                        inner join ojdt e on a.transid = e.transid 
						inner join oslp f on f.slpcode = b.slpcode
						where  b.cardcode + b.cardname like '%' +  @cardname + '%'
						and isnull(B.U_AR_Person,'')  like '%' +  @arperson + '%'
						and  (a.Account like '%' +  @Account +  '%'   )
						and (a.BalScDeb - a.BalScCred)<>0 
						and convert(varchar,a.refdate,112) <= @dateto

						select  *,'""" + comp.name + """' company from @table    
						order by docdate ,docnum              
			"""
			print(msgsql)
			data = pandas.io.sql.read_sql(msgsql,conn) 
			listfinal.append(data)
  
		


		df = pd.concat(listfinal)  

		if self.export_to=="list":
			self.env.cr.execute ("""DELETE FROM cnw_invar_saldopiutangdetailmodels WHERE create_uid =""" + str(self.env.user.id) + """ """ ) 
			
			datalist2 = df.values.tolist()

			for line in datalist2:
				self.env["cnw.invar.saldopiutangdetailmodels"].create({
											"docentry" 			: line[0],  
											"docdate" 			: line[1],  
											"taxdate" 			: line[2],  
											"docduedate" 		: line[3],  
											"docnum" 			: line[4],  
											"numatcard" 		: line[5],  
											"kwitansi" 			: line[6],  
											"fp" 				: line[7],  
											"cardcode" 			: line[8],  
											"cardname" 			: line[9],  
											"shiptocode" 		: line[10],  
											"amount" 			: line[11],  
											"balance" 			: line[12],  
											"po" 				: line[13],  
											"dpp" 				: line[14],  
											"ppn" 				: line[15],  
											"doctype" 			: line[16],  
											"objtype" 			: line[17],  
											"tfdate" 			: line[18],  
											"lt_no" 			: line[19],  
											"remdelay" 			: line[20],  
											"nogiro" 			: line[21],  
											"tglgiro" 			: line[22],  
											"checklist" 		: line[23],  
											"checklistdate" 	: line[24],  
											"gr_no" 			: line[25],  
											"arperson" 			: line[26],  
											"transtype" 		: line[27],  
											"topdays" 			: line[28],  
											"topdesc" 			: line[29],  
											"datediff" 			: line[30],  
											"denda" 			: line[31],  
											"dendastatus"		: line[32],  
											"tfstatus"			: line[33],  
											"cardgroup"			: line[34],
											"collector"			: line[35],
											"salesperson"		: line[36],
											"jadwal"			: line[37],
											"comp_name"			: line[38],

											})
			return {
				"type": "ir.actions.act_window",
				"res_model": "cnw.invar.saldopiutangdetailmodels",  
				#"view_id":view_do_list_tree, 
				"view_mode":"tree,calendar,pivot",
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
				   
			proyeksi = self.env["cnw.invar.jasper"].search([("name","=","saldopiutangdetail")])
			input_file 		= mpath + '/temp/' +  filex + ".jrxml" 
			data_file 		= mpath + '/temp/' +  filex + ".json" 
			output_file 	= mpath + '/temp/' +  filenamepdf
			filename 		= filenamepdf 


			jasperwapi = self.company_id.webapi

		## JRXML FILE 
			with open(input_file, "wb") as binary_file:
				
				# Write bytes to file
				binary_file.write(base64.b64decode(proyeksi.filejasper))
			binary_file.close()

		############################

		## JSON FILE 			
			
			jsondata = df.to_json(orient="records" )
				
			with open(data_file,'w+') as f:
				f.write(jsondata)
			#f.close()
		############################



			appSession 	= requests.Session()
			payload = { "inputfile" : input_file,
					"outputfile" 	: output_file ,
					"datafile" 		: data_file,
					"extension" : 'pdf'
					}
			url = jasperwapi + "report"
			print(payload)
			response = appSession.post(url, json=payload,verify=False)
			print(response.text)

			os.remove(input_file )
			os.remove(data_file )
		
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
		

 