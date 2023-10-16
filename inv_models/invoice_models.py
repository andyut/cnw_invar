# -*- coding: utf-8 -*-

from unicodedata import name
from odoo import models, fields, api
import base64 
import numpy as np
import pandas as pd
import requests  
import os
import pymssql
import pytz
from odoo.exceptions import UserError
from odoo.modules import get_modules, get_module_path
from datetime import datetime 
from jinja2 import Environment, FileSystemLoader
import pdfkit
import pyodbc  
import json
import numpy as np
import pandas as pd
import pandas.io.sql

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


import glob,os   

class ARInvoiceHome(models.Model):
	_name           = "ar.invoice.home"
	_description    = "Invoice Home Menu"
	name            = fields.Char("Home Menu")

	
class ARCollector(models.Model):
	_name           = "ar.collector"
	_description    = "Collector"
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
	name            = fields.Char("Collector Name")
	phone           = fields.Char("Collector Phone")

class ARJalur(models.Model):
	_name           = "ar.jalur"
	_description    = "Jalur list"
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
	name            = fields.Char("Jalur") 

class arperson(models.Model):
	_name           = "ar.arperson"
	_description    = "AR Person"
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
	name            = fields.Char("AR Name")
	phone           = fields.Char("AR Phone")

class ARGetTFprint(models.TransientModel):
	_name           = "ar.invoice.tfprint"
	_description    = "Invoice tfprint"
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
 
	dateto          = fields.Date("Date TF",default=lambda s:fields.Date.today())
	customer        = fields.Char("Business Partner",default="" )
	arperson        = fields.Char("AR Person",default="",required=True )
	collector_id	= fields.Many2one("ar.collector",string="Collector",required=True)
	printtype		= fields.Selection([ ('invoice', 'Invoice'),('kwitansi', 'kwitansi'),],string='Print Type', default='invoice')
	filexls         = fields.Binary("File Output")    
	filenamexls     = fields.Char("File Name Output")	
	def print_pdf(self):
		mpath       = get_module_path('cnw_invar')
		filenamepdf = 'TukarFaktur' + self.arperson + "_"   + self.collector_id.name + '_' +  self.dateto.strftime("%Y%m%d")   + '.pdf'
		filepath    = mpath + '/temp/'+ filenamepdf

		igu_title = "JADWAL TUKAR FAKTUR"
		igu_tanggal = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")
		igu_remarks = " Per Tanggal " + self.dateto.strftime("%Y-%m-%d")                    

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
		
		arperson = self.arperson if self.arperson else ""
		collector = self.collector_id.name if self.collector_id.name else ""
		customer = self.customer if self.customer else ""
		msgsql2 = """
					declare @tf_no 		varchar(50),
							@datefrom 	varchar(20),
							@dateto  	varchar(20) ,
							@arperson 	varchar(20) ,
							@collector 	varchar(20),
							@customer 	varchar(50)
 
					set @dateto = '""" + self.dateto.strftime("%Y%m%d")  + """'
					set @arperson = '""" + arperson + """'
					set @collector = '""" + collector + """'
					set @customer = '""" + customer + """'

					select  b.cardcode + '-' + b.cardname ,
							convert(varchar,a.U_kw_PrintDate,23) docdate,  

							a.U_Kw_No , 
							sum(a.doctotal) doctotal

					from oinv a
					inner join ocrd b on a.cardcode = b.cardcode 
					where isnull(U_TF_date,'')<>''
					and convert(varchar,a.U_TF_date,112) = @dateto
					and b.u_AR_person like '%' + @arperson + '%'
					and a.U_Coll_Name like '%' + @collector + '%'
					and b.cardcode + b.cardname like '%' + @customer + '%'
					group by b.cardcode + '-' + b.cardname ,
							convert(varchar,a.U_kw_PrintDate,23) ,  

							a.U_Kw_No 
					order by b.cardcode + '-' + b.cardname ,
							convert(varchar,a.U_kw_PrintDate,23) ,  

							a.U_Kw_No 		
		"""
		msgsql ="""
					declare @tf_no 		varchar(50),
							@datefrom 	varchar(20),
							@dateto  	varchar(20) ,
							@arperson 	varchar(20) ,
							@collector 	varchar(20),
							@customer 	varchar(50)
 
					set @dateto = '""" + self.dateto.strftime("%Y%m%d")  + """'
					set @arperson = '""" + arperson + """'
					set @collector = '""" + collector + """'
					set @customer = '""" + customer + """'


					select  b.cardcode + '-' + b.cardname ,
							convert(varchar,a.docdate,23) docdate, 
							a.docnum ,
							a.NumAtCard ,
							a.U_Kw_No ,
							a.U_RemDelay ,
							a.doctotal
					from oinv a
					inner join ocrd b on a.cardcode = b.cardcode 
					where isnull(U_TF_date,'')<>''
					and convert (varchar,a.U_TF_date,112) = @dateto
					and b.u_AR_person like '%' + @arperson + '%'
					and a.U_Coll_Name like '%' + @collector + '%'
					and b.cardcode + b.cardname like '%' + @customer + '%'

		"""
		if self.printtype=="invoice":
			data = pandas.io.sql.read_sql(msgsql,conn) 
		else:
			data = pandas.io.sql.read_sql(msgsql2,conn) 
		df = data

		detail = df.values.tolist() 
		env = Environment(loader=FileSystemLoader(mpath + '/template/'))        
		#jalur = self.jalur_id.name if self.jalur_id.name else "-"
		if self.printtype == "invoice":

			template = env.get_template("tukarfaktur2.html")   
		else:
			template = env.get_template("tukarfakturkwitansi2.html")  

		template_var = {"logo":logo,
						"igu_title" :igu_title,
						"igu_tanggal" :igu_tanggal ,
						"igu_remarks" :igu_remarks , 
						"tfno" :"" , 
						"arperson" : self.env.user.name , 
						"collector" :self.collector_id.name , 
						"jalur" :"-" , 
						"total" : 0,
						
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
	 		
class ARGetInvoice(models.TransientModel):
	_name           = "ar.invoice.wizard"
	_description    = "Invoice Wizard"
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
	datefrom        = fields.Date("Date From",default=lambda s:fields.Date.today())
	dateto          = fields.Date("Date To",default=lambda s:fields.Date.today())
	customer        = fields.Char("Business Partner",default="" )
	arperson        = fields.Char("AR Person",default=" " )
	unpaid        	= fields.Boolean("Un Paid",default=False)
	kwitansi        = fields.Boolean("Belum dibuat Kwitansi",default=False)

	def get_invoice_list(self):
		
		# host        = "192.168.1.13"
		# database    = "IGU_LIVE"
		# user        = "sa"
		# password    = "B1admin"

		host        = self.company_id.server
		database    = self.company_id.db_name
		user        = self.company_id.db_usr
		password    = self.company_id.db_pass          

		conn = pymssql.connect(host=host, user=user, password=password, database=database)    
			
		cursor = conn.cursor()  
		
		customer = self.customer if self.customer else ""
		arperson = self.arperson if self.arperson else ""

		msgsql = """
				declare 
					@datefrom varchar(10) , 
					@dateto varchar(10) ,
					@customer varchar(50),
					@arperson varchar(50),
					@company varchar(20)

							 
							set @datefrom = '"""+  self.datefrom.strftime("%Y%m%d")  + """'
							set @dateto = '"""+  self.dateto.strftime("%Y%m%d")  + """'
							set @customer = '""" + customer + """'
							set @arperson = '""" + arperson + """'
							set @company = '""" +  self.company_id.code_base + """'

				select  
							@company + CONVERT(VARCHAR,A.DOCENTRY) + '_' + CONVERT(VARCHAR,A.ObjType) AS id ,
							@company + CONVERT(VARCHAR,A.DOCENTRY) + '_' + CONVERT(VARCHAR,A.ObjType) AS name ,
							CONVERT(VARCHAR,a.docentry) DOCENTRY,
							CONVERT(VARCHAR,a.docnum) DOCNUM ,
							a.NumAtCard ,
							convert(varchar,a.docdate,23) docdate,
							convert(varchar,a.taxdate,23) taxdate,
							a.CANCELED ,
							a.cardcode ,
							'['+ a.cardcode + '] ' + a.cardname ,
							a.ShipToCode ,
							a.doctype ,
							a.U_Kw_No ,
							a.U_IDU_FPajak ,
							isnull(e.numatcard ,'')U_Cust_PO_No ,
							isnull(c.U_SlsEmpName ,''),
							isnull(b.U_AR_Person ,'') ,
							d.user_code + ' - ' + isnull(d.e_mail,'') usersign ,
							convert(varchar,a.CreateDate,23) createdate,
							a.doctime ,
							a.doctotal - a.vatsum dpp ,
							a.VatSum  ,
							a.DocTotal ,
							isnull(a.PaidSys ,0)PaidSys ,
							a.DocTotal - isnull(a.PaidSys ,0)  balance ,
							a.cardcode + a.cardname fullname ,
							g.vatgroup ,
							a.doctype + '-' + 'INV' doctype ,
							case isnull(a.U_Total_Print ,0)
								when 0 then 'Not Printed'
								when 1 then 'Print Orginal'
								else 'Copy(' + convert(varchar,a.U_Total_Print) + ')'
								end statusprint ,
							'Catatan TukarFaktur: ' + isnull(b.Notes,'')  + char(13)+'<br/>'+
                                                'Faktur Pengiriman  : ' + isnull(b.U_delivery_invoice,'N') + char(13)+'<br/>'+
                                                'Print Faktur  : ' + isnull(b.U_PrintFaktur,'Y') + char(13)+'<br/>'+
                                                'Print Kwitansi  :<b> ' + 
                                                                            case isnull(b.U_PrintKwitansi,'Y')
                                                                                    when 'N' then 'Tidak Print Kwitansi'
                                                                                    when 'Y' then 'Print Kwitansi'
                                                                                    when 'O' then 'Print Kwitansi Per Outlet'
                                                                                    when 'P' then 'Print Kwitansi Per PO '
                                                                            end + char(13)+'</b><br/>'+
                                                'Print Faktur Pajak  : ' + isnull(b.U_PrintFP,'N')+ char(13)+'<br/>'+
                                                'Tukar Faktur  : ' + isnull(b.U_PenagihanType,'Y') + char(13)+'<br/>' +
                                                ' ' inotes ,
							a.docduedate , 
							isnull(a.U_LT_No ,'') Tagihan, 
							isnull(a.U_Coll_Name ,'') tf_collector,
							isnull(a.U_RemDelay,'') tf_remarks ,
							ISNULL(B.U_Coll_Name,'-') as Collector,
							b.U_delivery_invoice ,
							b.U_PrintFaktur ,
							b.U_PrintKwitansi ,
							b.U_PrintFP ,
							b.U_PenagihanType						

				from OINV (nolock) A 
					inner join ocrd (nolock)  b on a.cardcode = b.cardcode  
					inner join ousr (nolock)  d on a.usersign = d.userid  
					INNER JOIN 
											(
												SELECT DISTINCT A.DOCENTRY , B.VATGROUP, a.objtype  FROM  DBO.OINV (nolock)  A 
													INNER JOIN DBO.INV1 (nolock)  B ON A.DOCENTRY = B.DOCENTRY 
												WHERE convert(varchar,a.docdate,112) between @datefrom and  @dateto
														and ( a.cardcode + a.cardname like '%' + ltrim(rtrim(isnull(@customer,''))) + '%')
												union all
												SELECT DISTINCT A.DOCENTRY , B.VATGROUP , a.objtype FROM  DBO.orin (nolock)  A 
													INNER JOIN DBO.rin1 (nolock)  B ON A.DOCENTRY = B.DOCENTRY 
												WHERE convert(varchar,a.docdate,112) between @datefrom and  @dateto
														and ( a.cardcode + a.cardname like '%' + ltrim(rtrim(isnull(@customer,''))) + '%')
											) G ON A.DOCENTRY = G.DOCENTRY and a.objtype = g.objtype 
					left outer join ordr (nolock)  e on a.u_igu_sodocentry = convert(varchar,e.docentry)
					left outer join oslp (nolock)  c on b.SlpCode = c.SlpCode 

				WHERE convert(varchar,a.docdate,112) between @datefrom and  @dateto
				and ( a.cardcode + a.cardname like '%' + ltrim(rtrim(isnull(@customer,''))) + '%')
				--and ( b.u_ar_person like '%' + replace(ltrim(rtrim(@arperson)),' ','')   + '%'  )

				union all

				select  
							@company + CONVERT(VARCHAR,A.DOCENTRY) + '_' + CONVERT(VARCHAR,A.ObjType) AS id ,
							@company + CONVERT(VARCHAR,A.DOCENTRY) + '_' + CONVERT(VARCHAR,A.ObjType) AS name ,
							CONVERT(VARCHAR,a.docentry) DOCENTRY,
							CONVERT(VARCHAR,a.docnum) DOCNUM ,
							a.NumAtCard ,
							convert(varchar,a.docdate,23) docdate,
							convert(varchar,a.taxdate,23) taxdate,
							a.CANCELED ,
							a.cardcode ,
							'['+ a.cardcode + '] ' + a.cardname ,
							a.ShipToCode ,
							a.doctype ,
							a.U_Kw_No ,
							a.U_IDU_FPajak ,
							isnull(A.numatcard ,'') U_Cust_PO_No ,
							isnull(c.U_SlsEmpName ,''),
							isnull(b.U_AR_Person ,'') ,
							d.user_code + '-' +  isnull(d.e_mail,'') usersign ,
							convert(varchar,a.CreateDate,23) createdate,
							a.doctime ,
							-1* ( a.doctotal - a.vatsum) dpp ,
							-1* a.VatSum  ,
							-1* a.DocTotal ,
							-1* isnull(a.PaidSys ,0)PaidSys ,
							-1* (a.DocTotal - isnull(a.PaidSys ,0))  balance,
							a.cardcode + a.cardname fullname  ,
							g.vatgroup ,
							a.doctype + '-' + 'CN' doctype,
							case isnull(a.U_Total_Print ,0)
								when 0 then 'Not Printed'
								when 1 then 'Print Orginal'
								else 'Copy(' + convert(varchar,a.U_Total_Print) + ')'
								end statusprint,
							'Catatan TukarFaktur: ' + isnull(b.Notes,'')  + char(13)+'<br/>'+
                                                'Faktur Pengiriman  : ' + isnull(b.U_delivery_invoice,'N') + char(13)+'<br/>'+
                                                'Print Faktur  : ' + isnull(b.U_PrintFaktur,'Y') + char(13)+'<br/>'+
                                                'Print Kwitansi  :<b> ' + 
                                                                            case isnull(b.U_PrintKwitansi,'Y')
                                                                                    when 'N' then 'Tidak Print Kwitansi'
                                                                                    when 'Y' then 'Print Kwitansi'
                                                                                    when 'O' then 'Print Kwitansi Per Outlet'
                                                                                    when 'P' then 'Print Kwitansi Per PO '
                                                                            end + char(13)+'</b><br/>'+
                                                'Print Faktur Pajak  : ' + isnull(b.U_PrintFP,'N')+ char(13)+'<br/>'+
                                                'Tukar Faktur  : ' + isnull(b.U_PenagihanType,'Y') + char(13)+'<br/>' +
                                                ' ' inotes,
							a.docduedate , 
							isnull(a.U_LT_No ,'') Tagihan, 
							isnull(a.U_Coll_Name ,'') tf_collector,
							isnull(a.U_RemDelay,'') tf_remarks,
							ISNULL(B.U_Coll_Name,'-') as Collector,
							b.U_delivery_invoice ,
							b.U_PrintFaktur ,
							b.U_PrintKwitansi ,
							b.U_PrintFP ,
							b.U_PenagihanType

				from orin (nolock) A 
					inner join ocrd (nolock) b on a.cardcode = b.cardcode  
					inner join ousr (nolock) d on a.usersign = d.userid  
					INNER JOIN 
											(
												SELECT DISTINCT A.DOCENTRY , B.VATGROUP, a.objtype  FROM  DBO.OINV (nolock)  A 
													INNER JOIN DBO.INV1 (nolock)  B ON A.DOCENTRY = B.DOCENTRY 
												WHERE convert(varchar,a.docdate,112) between @datefrom and @dateto
														and ( a.cardcode + a.cardname like '%' + ltrim(rtrim(isnull(@customer,''))) + '%')
												union all
												SELECT DISTINCT A.DOCENTRY , B.VATGROUP , a.objtype FROM  DBO.orin (nolock)  A 
													INNER JOIN DBO.rin1 B  (nolock)  ON A.DOCENTRY = B.DOCENTRY 
												WHERE convert(varchar,a.docdate,112) between @datefrom and @dateto
														and ( a.cardcode + a.cardname like '%' + ltrim(rtrim(isnull(@customer,''))) + '%')
											) G ON A.DOCENTRY = G.DOCENTRY and a.objtype = g.objtype 
					left outer join oslp (nolock)  c on b.SlpCode = c.SlpCode 
					
				WHERE convert(varchar,a.docdate,112) between @datefrom and  @dateto
				and ( a.cardcode + a.cardname like '%' + ltrim(rtrim(isnull(@customer,''))) + '%')
				--and ( b.u_ar_person like '%' + replace(ltrim(rtrim(@arperson)),' ','')   + '%'  )


 		
		"""
		print(msgsql)
		#cursor.execute( "exec DBO.IGU_INVOICELIST '"+ self.datefrom.strftime("%Y%m%d") + "','"+self.dateto.strftime("%Y%m%d")  +"','"+ customer + "','" + arperson + "','" +  self.company_id.code_base + "' "  )
		cursor.execute( msgsql )
		rowdata = cursor.fetchall() 
		conn.close()

		self.env["ar.invoice"].load(["id",
										"name",
										"docentry",
										"docnum",
										"numatcard" ,
										"docdate",
										"taxdate",
										"canceled", 
										"cardcode",
										"cardname",
										"shiptocode" ,
										"doctype",
										"kwitansi",
										"fp" ,
										"cust_ref" ,
										"salesperson" ,
										"arperson",
										"usersign" ,
										"sap_create",
										"doctime" ,
										"dpp" ,
										"ppn",
										"total" ,
										"paid",
										"balance"   ,
										"fullname",
										"vatgroup",
										'doctype',
										'printstatus',
										'inotes',
										'docduedate',
										'tf_number' ,  
										'tf_collector',
										'tf_remarks',
										"collector",
										"delivery_invoice",
										"printfaktur",
										"printkwitansi",
										"printfp",
										"penagihan_type"
										],rowdata)
		
		#view_do_list_tree = self.env['ir.model.data'].get_object_reference('ar_invoice','sp_do_list_tree')[1]

		if self.kwitansi:

			return {
				"type": "ir.actions.act_window",
				"res_model": "ar.invoice",  
				#"view_id":view_do_list_tree, 
				"view_mode":"tree,pivot",
				"context":{
							"search_default_notcanceled_in_sap":1},
				"act_window_id":"ar_invoice_wizard_action", 
				"domain": ["&","&"  ,
							("docdate", "<=", self.dateto),
							("docdate", ">=", self.datefrom) ,
							("fullname", "ilike", customer) , 
							("kwitansi", "=", False) , 
							("canceled", "=", "N") , 
							],}
		else:
			return {
				"type": "ir.actions.act_window",
				"res_model": "ar.invoice",  
				#"view_id":view_do_list_tree, 
				"view_mode":"tree,pivot",
				"context":{"search_default_notcanceled_in_sap":1},
				"act_window_id":"ar_invoice_wizard_action", 
				"domain": ["&","&"  ,
							("docdate", "<=", self.dateto),
							("docdate", ">=", self.datefrom) ,
							("fullname", "ilike", customer) , 
							("canceled", "=", "N") , 
							],}
			
		
		


class ARInvoice(models.Model):
	_name           = "ar.invoice"
	_description    = "AR Invoice"
	_order          = "company_id,name" 

	name            = fields.Char("IDX")
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
	docentry        = fields.Char("DocEntry")     
	docnum          = fields.Char("Inv")
	numatcard       = fields.Char("SO")
	docdate         = fields.Date("Doc Date" )
	taxdate         = fields.Date("Document Date" )
	docduedate		= fields.Date("Tukar Faktur / Jatuh Tempo " )

	canceled        = fields.Char("Canceled")
	cardcode        = fields.Char("BP Code")
	cardname        = fields.Char("Customer")
	fullname        = fields.Char("Full Name")
	address         = fields.Char("Billing Address")

	shiptocode      = fields.Char("OutLet")
	doctype         = fields.Char("DocType")
	kwitansi        = fields.Char("Kwitansi"  )
	fp              = fields.Char("FP"  )
	cust_ref        = fields.Char("Ref")
	salesperson     = fields.Char("Sales Person" )
	arperson        = fields.Char("AR Person"  )

	usersign        = fields.Char("SAP User Created")
	sap_create      = fields.Date("SAP Doc Created")
	doctime         = fields.Char("SAP Doc Time")
	dpp             = fields.Float("DPP",digits=(19,2),default=0)
	ppn             = fields.Float("PPN",digits=(19,2),default=0)
	total           = fields.Float("TOTAL",digits=(19,2),default=0)
	paid            = fields.Float("PAID",digits=(19,2),default=0)
	balance         = fields.Float("BALANCE",digits=(19,2),default=0 ) 
	vatgroup        = fields.Char("Tax")
	doctype         = fields.Char("iType")
	printstatus     = fields.Char("Print")
	inotes 			= fields.Html("TF Notes")
	collector 		= fields.Char("Collector")
# Odoo Extra Field Check list 
 
	act_checked     = fields.Boolean("Supervisor Check",default=False )   
	act_status      = fields.Char("Act Status",default=False)   
	act_statusdt    = fields.Datetime("Last Status Date",default=False )  
	act_notes       = fields.Char("Notes")   
	tf_date 		= fields.Date("Tukar Faktur Date")
	tg_date 		= fields.Date("Tagihan ")
	tf_number 		= fields.Char("Tukar Faktur")
	tf_type 		= fields.Char("TF Type")
	tf_collector	= fields.Char("TF Collector")
	tf_remarks		= fields.Char("TF Remarks")
 # Odoo Extra Field 
 
	#tf_id           = fields.Many2one("ar.tf",string="Tukar Faktur")

# eFAKTUR Extra Fields

	fp_filename     = fields.Char("File Faktur Pajak")
	fp_status       = fields.Char("Faktur Pajak Status",default="N")

	filexls         = fields.Binary("File Output")    
	filenamexls     = fields.Char("File Name Output")
## laporan status print

	delivery_invoice	= fields.Selection(string="Faktur Pengiriman", selection=[("Y","Yes"),("N","No")],default="N")
	printfaktur			= fields.Selection(string="Print Faktur", selection=[("Y","Yes"),("N","No")],default="Y")
	printkwitansi		= fields.Selection(string="Print Kwitansi", selection=[("Y","Yes"),("N","No"),("O","YPrint Per Outlet"),("P","Yes, Print Per PO")],default="N")
	printfp				= fields.Selection(string="Print FakturPajak", selection=[("Y","Yes"),("N","No")],default="N")
	penagihan_type		= fields.Selection(string="Tipe Penagihan", selection=[("Y","Tukar Faktur"),("N","Tidak Tukar Faktur")],default="N") 
	
	def fp_download(self):
		filename = self.fp_filename
		fp_path = self.env["ar.invoice.setting.fppath"].search([("company_id","=",self.company_id.id)]).name
		file = open( filename , 'rb')
		out = file.read()
		file.close()
		self.filexls =base64.b64encode(out)
		self.filenamexls = self.fp + ".pdf"
		#os.remove(mpath + '/temp/'+ filename )
		
		#print("web/content/?model=" + self._name +"&id=" + str(self.id) + "&filename_field=filenamexls&field=filexls&download=true&filename=" + self.filenamexls)
		return {
			'name': 'Report',
			'type': 'ir.actions.act_url',
			'url': "web/content/?model=" + self._name +"&id=" + str(
				self.id) + "&filename_field=filenamexls&field=filexls&download=true&filename=" + self.filenamexls,
			'target': 'new',
			}


class ARInvoiceFPFile (models.Model):
	_name           = "ar.invoice.fpfile"
	_description    = "Invoice Faktur PAjak file"
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
	name            = fields.Char("Nama File")
	fp              = fields.Char("FP")  
	doctype         = fields.Char("Doc Type")
	docnum          = fields.Char("Doc Num")
	docdate          = fields.Date("Doc Date")
	so              = fields.Char("SO Number")
	numatcard       = fields.Char("NumAtCard")
	cardcode        = fields.Char("Card Code")
	cardname        = fields.Char("Card Name")
	shiptocode      = fields.Char("ShipToCode") 
	dpp             = fields.Float("DPP") 
	vatsum          = fields.Float("PPn")
	total           = fields.Float("Total")
	istatus         = fields.Selection(string="Status",selection=[("Y","Y"),("N","N")],default="N")


	
class ARInvoiceFPCompanyPath (models.Model):
	_name           = "ar.invoice.setting.fppath"
	_description_   = "Description "
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
	name            = fields.Char("Path",required=True)
	status          = fields.Selection(string="Status" ,selection=[("Active","Active"),("Non","Non Active")],default="Active")


class ARInvoiceItem(models.Model):
	_name           = "ar.invoice.item"
	_description    = "AR Invoice Item"
	_order          = "company_id,name" 
	name            = fields.Char("IDX")
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
	invoice         = fields.Char("Invoice Number")
	numatcard       = fields.Char("SO number")
	canceled        = fields.Char("Canceled")
	partner_group   = fields.Char("Partner Group")
	cardcode        = fields.Char("Partner Code")
	outlet          = fields.Char("Outlet")
	partnercompany  = fields.Char("Partner Company")
	docdate         = fields.Date("Doc Date")
	imonth          = fields.Char("Imonth")
	iyear           = fields.Char("IYear")
	sales_in_trx    = fields.Char("Sales In Trx")
	slsgrp_in_trx   = fields.Char("Sales Group In Trx")
	itemcode        = fields.Char("Item Code")
	itemname        = fields.Char("Item Name")
	uom             = fields.Char("UoM")
	product_group   = fields.Char("Product Group")
	subgroup        = fields.Char("Sub Group")
	product_brand   = fields.Char("Brand")
	quantity        = fields.Float("Quantity",digits=(19,2))
	quantity_ar     = fields.Float("Quantity Customer",digits=(19,2))
	price           = fields.Float("Price",digits=(19,2))
	linetotal       = fields.Float("Line Total",digits=(19,2))
	margin          = fields.Float("Margin",digits=(19,2),groups="igu_actreport.igu_accounting_spv_viewer")

class ARUpdateFPFile(models.TransientModel):
	_name           = "ar.invoice.updatefp"
	_description    = "Invoice updatefp   Wizard"
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)

	def UpdateFP(self):
		self.env.cr.execute("""update public.ar_invoice ai
								set  fp_filename = aif."name"  ,
									fp_status  ='Y'
								from  public.ar_invoice_fpfile aif 
								where  replace(replace(ai.fp,'.',''),'-','') = aif.fp """)



class ARScanFPFile(models.TransientModel):
	_name           = "ar.invoice.scanfp"
	_description    = "Invoice Scan FP Wizard"
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)

	def ScanFP(self):
		fp_path = self.env["ar.invoice.setting.fppath"].search([("company_id","=",self.company_id.id)]).name

		print("path file ")
		print(fp_path)
		datax=[]
		for filex in os.listdir(fp_path):
			if filex.endswith(".pdf"):
				x =[]
				# datax.append("I" + filex[16:32] ,
				# 			"name":filex ,
				# 			"fp":filex[16:32],
				# 			)
				x.append("I" + filex[16:32] )
				fullpathname = fp_path + "/" + filex
				x.append(fullpathname)
				x.append(filex[16:32])							
				datax.append(x)
		
		#print(datax)
		self.env.cr.execute ("""truncate table ar_invoice_fpfile  """ ) 
		for i in datax:

			self.env["ar.invoice.fpfile"].create({	"id" : i[0]	,
													"name" : i[1],
													"fp" : i[2] })
		

 
		
		## insert into odoo model



class ARGetInvoiceItem(models.TransientModel):
	_name           = "ar.invoice.item.wizard"
	_description    = "Invoice Item Wizard"
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
	datefrom        = fields.Date("Date From",default=lambda s:fields.Date.today())
	dateto          = fields.Date("Date To",default=lambda s:fields.Date.today())
	customer        = fields.Char("Business Partner",default=" " )
	item            = fields.Char("Item Code / Description",default=" " )

	def get_invoice_list(self):
		
		# host        = "192.168.1.13"
		# database    = "IGU_LIVE"
		# user        = "sa"
		# password    = "B1admin"

		host        = self.company_id.server
		database    = self.company_id.db_name
		user        = self.company_id.db_usr
		password    = self.company_id.db_pass                   

		conn = pymssql.connect(host=host, user=user, password=password, database=database)    
			
		cursor = conn.cursor() 
		customer = self.customer if self.customer else ""
		item = self.item if self.item else ""

		cursor.execute( "exec DBO.IGU_INVOICE_LIST_ITEM '"+ self.datefrom.strftime("%Y%m%d") + "','"+self.dateto.strftime("%Y%m%d")  +"','"+ customer  + "','" + item + "','" +  self.company_id.code_base + "'  " )
		rowdata = cursor.fetchall() 
		conn.close()
		self.env["ar.invoice.item"].load(["id",
										"name",
										"invoice",
										"numatcard",
										"canceled",
										"partner_group",
										"cardcode" ,
										"outlet",
										"partnercompany", 
										"docdate",
										"imonth",
										"iyear" ,
										"sales_in_trx",
										"slsgrp_in_trx",
										"itemcode" ,
										"itemname" ,    
										"uom" ,
										"product_group",
										"subgroup" ,
										"product_brand",
										"quantity" ,
										"quantity_ar" ,
										"price",
										"linetotal" ,
										"margin"    
										],rowdata)
		#print (rowdata)
		#view_do_list_tree = self.env['ir.model.data'].get_object_reference('ar_invoice','sp_do_list_tree')[1]
		return {
			"type": "ir.actions.act_window",
			"res_model": "ar.invoice.item",  
			#"view_id":view_do_list_tree, 
			"view_mode":"tree,pivot",
			"act_window_id":"ar_invoice_item_action", 
			"domain": ["&", "&",'&',
						("docdate", "<=", self.dateto),
						("docdate", ">=", self.datefrom) ,
						("outlet", "ilike", self.customer) ,
						("itemname", "ilike", self.item) ,],}
		
		


