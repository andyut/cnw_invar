# -*- coding: utf-8 -*-
import requests 
import xlsxwriter
import os
import pytz

from odoo.exceptions import UserError
from odoo.modules import get_modules, get_module_path
from datetime import datetime
from odoo import models, fields, api
import base64
import pymssql 

 

class SAPPartner_TFRemarks(models.TransientModel):
	_name           = "cnwls.bp.tfnotes"

	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
	tfnotes         = fields.Char("TF Notes",required=True)

	def update_TFRemarks(self):

		bps= self.env["sap.bp"].browse(self.env.context.get("active_ids"))        


# INIT SERVICES LAYER
		appSession = requests.Session()
		companyDB = self.env.user.company_id.db_name
		UserName =  self.env.user.company_id.sapuser
		Password =  self.env.user.company_id.sappassword

		url = self.env.user.company_id.sapsl

# SERVICES LAYER LOGIN		


		urllogin = url + "Login"
		print("LOGIN SL :")


		payload = { "CompanyDB" :companyDB,
					"UserName" : UserName ,
					"Password" : Password
					}
		print(payload)
		response = appSession.post(urllogin, json=payload,verify=False)

		print(response.text)

# SERVICES LAYER PATCH
		for partner_id in bps:

			print("update SL :")
			urlPartner = url + "BusinessPartners('" + partner_id.cardcode + "')" 

			payload = {
						"Notes": self.tfnotes 
						}

			response = appSession.patch(urlPartner,json=payload,verify=False)

			print(response.text)
			partner_id.notes = self.tfnotes 




		urllogout =  url + "Logout"


		response = appSession.post(urllogout,verify=False)        

class SAPPartner(models.Model):
	_name           = "sap.bp"
	_description    = "SAP Business Partner"
	name            = fields.Char("Internal Code")
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
	cardcode        = fields.Char("BP Code", default="BP Code")
	cardname        = fields.Char("BP Name" ,default="BP Name")
	bpname          = fields.Char("BP Full Name")
	cardfname       = fields.Char("BP Foreign Name",default="BP Foreign Name")
	partnerdesc     = fields.Char("Partner Long Desc",compute="_getdesc",store=True)
	groupname       = fields.Char("Group Name",default="Group Name")
	lictradnum      = fields.Char("Tax ID / NPWP")
	alamatnpwp      = fields.Char("Alamat NPWP", default="Alamat NPWP")
	ar_person       = fields.Char("AR Person", default="")
	salesperson     = fields.Char("Sales Person",default="Sales Person")
	salesgroup      = fields.Char("Sales Group",default="Sales Group")
	lock_limit      = fields.Char("Lock Limit in Day(s)")
	lock_bp         = fields.Char("Lock BP")
	paymentgroup    = fields.Char("Payment Group")
	creditline      = fields.Float("Credit Limit",digit=(19,6),default=0.0)
	balance         = fields.Float("Total Balance",digit=(19,6),default=0.0)
	b60             = fields.Float("Before 60 Days",digit=(19,6),default=0.0)
	a60             = fields.Float("After 60 Days",digit=(19,6),default=0.0)
	delivery        = fields.Float("Open Delivery",digit=(19,6),default=0.0)
	ordersbal       = fields.Float("Open Order",digit=(19,6),default=0.0)
	phone1          = fields.Char("Phone 1",default="")
	phone2          = fields.Char("Phone 2",default="")
	cellular        = fields.Char("Cellular",default="")    
	fax             = fields.Char("Fax",default="")
	e_mail          = fields.Char("E-Mail",default="")
	intrntsite      = fields.Char("Website",default="")
	notes           = fields.Char("TF Notes",default="")
	cntctprsn       = fields.Char("Contact Person", default="")
	billaddress     = fields.Char("Billing Address",default="")
	address         = fields.Char("Address",default="")
	mailaddress     = fields.Char("Mail Address",default="")
	contact_ids     = fields.One2many("sap.bp.contact","bp_id",string="Contact")
	outlet_ids      = fields.One2many("sap.bp.outlet","bp_id",string="Outlet")
	invoice_ids     = fields.One2many("sap.bp.invoice","bp_id", string="Last Invoice")
	penjualan_ids   = fields.One2many("sap.bp.penjualan","bp_id", string="Penjualan")
	payment_ids     = fields.One2many("sap.bp.payment","bp_id",string="Last Payment")
	special_price   = fields.One2many("sap.bp.specialprice","bp_id",string="Special Price")

	freetext        = fields.Text("Free Text")
#follow up 
	laststatus      = fields.Char("Last Status")
	laststatus_date = fields.Datetime("Last Status Date")   
	followup_type   = fields.Selection(selection=[("mail","E-Mail"),("phone","Phone"),("whatsapp","Whatsapp"),("others","Other")],string="Type")
	followup_by     = fields.Selection(selection=[("ar","Follow Up By AR"),("sales","Follow Up By Sales"),("debt_collector","Follow Up By Debt Collector (Iwan)")],string="Follow Up By",default="ar")

	followup_ids    = fields.One2many("cnw.cflwup.followup","customer_id","Follow Up" )


#extra fields

	nik             = fields.Char("NIK")
	kartukeluarga   = fields.Char("Kartu Keluarga")
	siup            = fields.Char("SIUP")
	tdp             = fields.Char("TDP")
	skd             = fields.Char("SKD")
	nib             = fields.Char("NIB")
	akte_pendirian  = fields.Char("Akte Pendirian")
	parent_bp       = fields.Char("Parent / Group BP")
	va              = fields.Char("Virtual Rekening")
	va_status       = fields.Char("VA Printed?")


#print status
	invoicing 		= fields.Char("Invoicing")
	printfp 		= fields.Char("Print FP")
	printinvoice	= fields.Char("Print Invoice")
	printkwitansi	= fields.Char("Print Kwitansi")
	@api.multi
	def _getdesc(self):
		self.partnerdesc = "[" + self.cardcode + "] " + self.cardname

	def refresh_contact(self):
		return True
	def f_refresh(self):
		
		host        = self.env.user.company_id.server
		database    = self.env.user.company_id.db_name
		user        = self.env.user.company_id.db_usr
		password    = self.env.user.company_id.db_pass

		conn = pymssql.connect(host=host, user=user, password=password, database=database)

		if self.cardcode:
			partner = self.cardcode
		else:
			partner =""
		outlet_ids =[]
		print(self.cardcode)
		cursor = conn.cursor()
		cursor.execute( """ exec  [dbo].[IGU_ACT_BUSINESSPARTNER] '%""" + partner + "%' """ )

	def refresh_specialprice(self):
		host        = self.env.user.company_id.server
		database    = self.env.user.company_id.db_name
		user        = self.env.user.company_id.db_usr
		password    = self.env.user.company_id.db_pass
		
		conn = pymssql.connect(host=host, user=user, password=password, database=database)
		if self.cardcode:
			partner = self.cardcode
		else:
			partner =""
		cursor = conn.cursor()
		cursor.execute( "exec dbo.IGU_BPSpecialPrice '"+ partner + "','"+ self.name  +"' " )

		rowdata = cursor.fetchall() 
		self.env["sap.bp.specialprice"].load(["id",
										"name",
										"itemcode",
										"it	emname",
										"specialprice",
										"usr_created",
										"date_created",
										"usr_updated",
										"date_updated",
										"bp_id"],rowdata)

		#self.env.cr.commit()
		#print rowdata
		#outlet =self.env["sap.bp.outlet"].search([("bp_id","=",self.id)])
		#print outlet

		#outlet_ids =[]
		#for line in outlet:
		#    outlet_ids.append(4,line.id)
		# 
		# self.outlet_ids = outlet_ids


		conn.close()

	def refresh_invoice(self):
		host        = self.env.user.company_id.server
		database    = self.env.user.company_id.db_name
		user        = self.env.user.company_id.db_usr
		password    = self.env.user.company_id.db_pass
		
		conn = pymssql.connect(host=host, user=user, password=password, database=database)
		if self.cardcode:
			partner = self.cardcode
		else:
			partner =""
		cursor = conn.cursor()
		cursor.execute( "exec dbo.IGU_penjualanBP '"+ partner + "','"+ self.name  +"' " )

		rowdata = cursor.fetchall() 
		self.env["sap.bp.penjualan"].load(["id",
										"name",
										"bulan",
										"basemount",
										"ppn",
										"piutang",
										"bp_id"],rowdata)

		#self.env.cr.commit()
		#print rowdata
		#outlet =self.env["sap.bp.outlet"].search([("bp_id","=",self.id)])
		#print outlet

		#outlet_ids =[]
		#for line in outlet:
		#    outlet_ids.append(4,line.id)
		# 
		# self.outlet_ids = outlet_ids


		conn.close()


	def refresh_payment(self):
		host        = self.env.user.company_id.server
		database    = self.env.user.company_id.db_name
		user        = self.env.user.company_id.db_usr
		password    = self.env.user.company_id.db_pass
		
		conn = pymssql.connect(host=host, user=user, password=password, database=database)
		if self.cardcode:
			partner = self.cardcode
		else:
			partner =""
		cursor = conn.cursor()
		cursor.execute( "select top 100  " + 
						"'IGU' + convert(varchar, A.transid )+ convert(varchar,a.line_id) id , " +
						"'IGU' + convert(varchar, A.transid )+ convert(varchar,a.line_id) name, " +
						"b.u_trans_no voucher, " + 
						"c.name + ' - ' + convert(varchar,b.number)   journal , " + 
						"convert(varchar,a.refdate,23) docdate, " + 
						"a.credit - a.debit total ," + 
						"'"+ (self.name) + "' " + 
						" from jdt1 a " + 
						"inner join ojdt b on a.transid = b.transid and a.TransType <>13 and a.TransType <>14 " + 
						"inner join oact d on a.ContraAct = d.acctcode  " + 
						"inner join [@IGU_TRANSTYPE]c on a.transtype = c.Code " + 
						" where a.account = '1130001' " + 
						"AND a.shortname = '"+ partner + "' " +
						"order by a.refdate desc,a.transid desc" )

		rowdata = cursor.fetchall() 
		self.env["sap.bp.payment"].load(["id",
										"name",
										"voucher",
										"Journal",
										"docdate",
										"total",
										"bp_id"],rowdata)

		#self.env.cr.commit()
		#print rowdata
		#outlet =self.env["sap.bp.outlet"].search([("bp_id","=",self.id)])
		#print outlet

		#outlet_ids =[]
		#for line in outlet:
		#    outlet_ids.append(4,line.id)
		# 
		# self.outlet_ids = outlet_ids


		conn.close()


	def refresh_outlet(self): 
		
		host        = self.env.user.company_id.server
		database    = self.env.user.company_id.db_name
		user        = self.env.user.company_id.db_usr
		password    = self.env.user.company_id.db_pass
		
		conn = pymssql.connect(host=host, user=user, password=password, database=database)
		if self.cardcode:
			partner = self.cardcode
		else:
			partner =""
		cursor = conn.cursor()
		cursor.execute( "select	'IGU' + a.cardcode + convert(Varchar,a.linenum) id , " + 
						"a.address name , " + 
						"a.street street ," + 
						"a.u_del_rute delivery_route  ," + 
						 "'"+ (self.name) + "' " + 
						"FROM CRD1 A where a.adresType='S' and  a.cardcode = '"+ partner + "' " )

		rowdata = cursor.fetchall() 
		self.env["sap.bp.outlet"].load(["id",
										"name",
										"street",
										"delivery_route","bp_id"],rowdata)

		#self.env.cr.commit()
		#print rowdata
		#outlet =self.env["sap.bp.outlet"].search([("bp_id","=",self.id)])
		#print outlet

		#outlet_ids =[]
		#for line in outlet:
		#    outlet_ids.append(4,line.id)
		# 
		# self.outlet_ids = outlet_ids


		conn.close()

		

class SAPBPContact(models.Model):
	_name           = "sap.bp.contact"
	_description    = "SAP BP Contact"
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
	name            = fields.Char("Contact Name")    
	bp_id           = fields.Many2one("sap.bp",string="Business Partner",ondelete='cascade')

class SAPBPSpecialPrice(models.Model):
	_name           = "sap.bp.specialprice"
	_description    = "SAP Special Price"
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
	name            = fields.Char("Special Price Key")
	itemcode        = fields.Char("Item Code")
	itemname        = fields.Char("Item Name")
	specialprice    = fields.Float("Special Price",digit=(19,6))
	usr_created      = fields.Char("User Created")
	date_created    = fields.Date("Date Created")
	usr_updated     = fields.Char("User Updated")
	date_updated    = fields.Date("User Updated")
	bp_id           = fields.Many2one("sap.bp",string="Business Partner",ondelete='cascade')

class SAPBPOutlet(models.Model):
	_name           = "sap.bp.outlet"
	_description    = "SAP BP Outlet"
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
	name            = fields.Char("Outlet")
	street          = fields.Char("Street / Address ")
	delivery_route  = fields.Char("Delivery Route")
	bp_id           = fields.Many2one("sap.bp",string="Business Partner",ondelete='cascade')
	cardcode        = fields.Char("Partner Code",related="bp_id.cardcode")
	arperson        = fields.Char("AR Person ",related="bp_id.ar_person")

class SAPBPPenjualan(models.Model):
	_name           = "sap.bp.penjualan"
	_description    = "SAP BP Penjualan"
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
	name            = fields.Char("Penjualan")
	bulan           = fields.Char("Bulan")
	basemount       = fields.Float("Base Amount",digit=(19,6))
	ppn             = fields.Float("PPn",digit=(19,6))
	piutang         = fields.Float("Piutang",digit=(19,6))
	bp_id           = fields.Many2one("sap.bp",string="Business Partner",ondelete='cascade')
class SAPBPInvoice(models.Model):
	_name           = "sap.bp.invoice"
	_description    = "SAP BP Last Invoice"
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)

	name            = fields.Char("Invoice Internal Number")
	so_number       = fields.Char("DO Number")
	kwitansi        = fields.Char("Kwitansi")
	shiptocode      = fields.Char("Outlet")
	fakturpajak     = fields.Char("Faktur Pajak")
	total           = fields.Char("Street / Address ") 
	bp_id           = fields.Many2one("sap.bp",string="Business Partner",ondelete='cascade')
class SAPBPPayment(models.Model):
	_name           = "sap.bp.payment"
	_description    = "SAP BP payment"
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
	name            = fields.Char("Payment Code")
	voucher         = fields.Char("BD Number")
	Journal         = fields.Char("Journal ID")
	docdate         = fields.Date("Doc Date")
	total           = fields.Float("Total",digit=(19,6))
	bp_id           = fields.Many2one("sap.bp",string="Business Partner",ondelete='cascade')


class SAPPartnerWizard(models.TransientModel):
	_name           = "sap.bp.wizard"
	_description    = "sap BP Wizard"
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
	partner         = fields.Char("Partner Code /Name",default="") 
	arperson        = fields.Char("AR Person")
	filexls         = fields.Binary("File Output")    
	filenamexls     = fields.Char("File Name Output")
	 
	def view_bp_xls(self): 
		
		host        = self.env.user.company_id.server
		database    = self.env.user.company_id.db_name
		user        = self.env.user.company_id.db_usr
		password    = self.env.user.company_id.db_pass
		
		conn = pymssql.connect(host=host, user=user, password=password, database=database)

		if self.partner:
			partner = self.partner
		else:
			partner =""
		arperson = self.arperson if self.arperson else ""
		
		cursor = conn.cursor() 
		msgsql = """
						declare @partner varchar(20) ,@arperson varchar(50)

						set @partner = '""" + partner + """'
						set @arperson = '""" + arperson +"""' 

						select                  'IGU_LIVE' +  convert(Varchar,a.docentry) id ,  
												'IGU_LIVE' + convert(Varchar,a.docentry) name ,  
												a.cardcode , 
												a.cardname , 
												isnull(a.cardfname,'') cardfname,  
												b.groupname ,  
												isnull(a.lictradnum,'000000000000000') lictradnum ,  
												isnull(replace(replace(a.U_Alamat_NPWP ,char(13),''),char(10),''),'') alamatnpwp ,  
												upper(isnull(a.U_AR_Person,'None')) ar_person,  
												upper('['+ c.SlpName + '] ' + isnull(c.U_SlsEmpName,'')) salesperson,  
												isnull(c.memo,'') salesgroup,  
												isnull(a.U_locktimeout ,'-1') lock_limit ,  
												isnull(a.U_IGU_LockBP,'') lock_bp ,  
												D.PymntGroup ,  
												A.CreditLine ,  
												A.Balance ,  
												A.DNotesBal ,  
												A.OrdersBal ,  
												A.Phone1 ,  
												a.phone2,  
												a.Cellular ,  
												a.Fax ,  
												a.E_Mail ,  
												a.IntrntSite ,  
												a.Notes ,  
												a.CntctPrsn ,  
												a.BillToDef ,  
												replace(a.Address ,char(13),'') Address,  
												replace(a.MailAddres ,char(13),'') MailAddres  ,b60,a60,
												A.U_IDU_NIK ,
												A.U_IGU_KK ,
												A.U_IGU_SIUP ,
												A.U_IGU_TDP ,
												A.U_IGU_SKD ,
												A.U_IGU_AKTE, 
												A.U_Parent_Group,
												A.U_IGU_virtualrek,
												A.U_print_va    ,
												a.cardcode  + isnull(a.cardname,'') bpname,
												a.free_text   itext
												from OCRD (NOLOCK) A   
												INNER JOIN OCRG (NOLOCK)  B ON A.GroupCode = B.GroupCode   
												INNER JOIN OSLP (NOLOCK)  C ON A.SLPCODE = C.SlpCode  
												INNER JOIN OCTG  (NOLOCK)  D ON A.GroupNum = D.GroupNum  
												left outer join 
															(

															select
																	c.cardcode ,
																	c.cardname ,
																	sum( CASE WHEN '""" +  self.env.user.company_id.code_base + """' = 'igu23' and  convert(varchar,a.refdate,112)='20221231'
																	
																	then case when convert(varchar,DATEADD(month, -2, getdate()),112)<=  convert(varchar,a.taxdate,112) then  (a.BalScDeb -a.balsccred ) else 0 end 
																	else case when convert(varchar,DATEADD(month, -2, getdate()),112)<=  convert(varchar,a.refdate,112) then  (a.BalScDeb -a.balsccred ) else 0 end
																	end) 'b60' ,
																	sum( CASE WHEN '""" +  self.env.user.company_id.code_base + """' = 'igu23' and  convert(varchar,a.refdate,112)='20221231'																	
																	then case when convert(varchar,DATEADD(month, -2, getdate()),112)>  convert(varchar,a.taxdate,112) then  (a.BalScDeb -a.balsccred ) else 0 end  
																	else  case when convert(varchar,DATEADD(month, -2, getdate()),112)>convert(varchar,a.refdate,112) then  (a.BalScDeb -a.balsccred ) else 0 end  
																	end ) 'a60' 

															from jdt1 (NOLOCK)  a 
																inner join ojdt (NOLOCK)  b on a.transid = b.transid 
																inner join ocrd (NOLOCK)  c on a.ShortName = c.cardcode 
																inner join ocrg  (NOLOCK) d on d.groupcode = c.groupcode
																INNER JOIN oslp  (NOLOCK) f on c.slpcode  = f.slpcode 
																inner join [@igu_transtype] e on a.transtype = e.code 

															where 
																	left(a.account ,3)='113' 
																	and ( c.cardtype='C' AND c.cardcode + UPPER(c.cardname) + UPPER(isnull(c.cardfname,''))+ UPPER(ISNULL(c.BillToDef,'')) like '%' + @partner  + '%' )
																	and a.BalScDeb -a.balsccred  <>0 
																	and convert(varchar,a.refdate,112)<=convert(varchar,getdate(),112)
																	and isnull(c.u_AR_Person,'') like '%' + @arperson + '%'
															group by c.cardcode ,
																	c.cardname 
															) as E on a.cardcode = e.cardcode ,
															OADM  (NOLOCK) G
												where a.cardtype='C' AND a.cardcode + UPPER(a.cardname) + upper(isnull(a.U_Parent_Group,'')) + UPPER(isnull(a.cardfname,''))+ UPPER(ISNULL(a.BillToDef,'')) like '%' + @partner  + '%' 
												and isnull(a.u_AR_Person,'') like '%' + @arperson + '%'
								
		"""
#        cursor.execute( """ exec  [dbo].[IGU_ACT_BUSINESSPARTNER] '""" + partner + """' """ )
#        cursor.execute( """ exec  [dbo].[IGU_ACT_BUSINESSPARTNER] '""" + partner + """' """ )
		cursor.execute( msgsql)

		rowdata = cursor.fetchall()
		print ( type(rowdata))
		self.env["sap.bp"].load(["id",
								"name",
								"cardcode",
								"cardname",
								"cardfname",
								"groupname",
								"lictradnum",
								"alamatnpwp",
								"ar_person",
								"salesperson",
								"salesgroup",
								"lock_limit",
								"lock_bp",
								"paymentgroup",
								"creditline",
								"balance",
								"delivery",
								"ordersbal",
								"phone1",   
								"phone2",
								"cellular",
								"fax",
								"e_mail",
								"intrntsite",
								"notes",
								"cntctprsn",
								"billaddress",
								"address",
								"mailaddress","b60","a60",
								"nik",
								"kartukeluarga",
								"siup",
								"tdp",
								"skd",
								"akte_pendirian",
								"parent_bp",
								"va",
								"va_status",
								"bpname",
								"freetext"
								],rowdata)

		conn.close()
		return {
			"type": "ir.actions.act_window",
			"res_model": "sap.bp",
			"views": [[False, "tree"], [False, "form"],[False,"pivot"]],
			"domain": ["&",
						("bpname", "ilike", partner), 
						("ar_person", "ilike", arperson),],}


 