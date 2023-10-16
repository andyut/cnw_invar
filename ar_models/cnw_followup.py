from odoo import models, fields, api


class CNWCustomerFollowup(models.Model):
	_name           = "cnw.cflwup.followup"
	_description    = "Customer Follow Up history"
	_order			="id desc"
	name            = fields.Char("No Follow-up ")
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
	customer_id     = fields.Many2one("sap.bp", string="Customer")
	docdate         = fields.Date("Doc Date",required=True,default=lambda s:fields.Date.today())
	cardcode        = fields.Char("Customer Code",related="customer_id.cardcode",store=True)
	cardname        = fields.Char("Customer Name",related="customer_id.cardname",store=True)
	cardgroup       = fields.Char("Customer Group",related="customer_id.groupname",store=True )
	salesname       = fields.Char("Sales Name",related="customer_id.salesperson")
	arperson        = fields.Char("AR person",related="customer_id.ar_person")

	followup_type   = fields.Selection(selection=[("mail","E-Mail"),("phone","Phone"),("whatsapp","Whatsapp"),("others","Other")],string="Type")

	followup_by     = fields.Selection(selection=[("ar","Follow Up By AR"),("sales","Follow Up By Sales"),("debt_collector","Follow Up By Debt Collector (Iwan)")],string="Follow Up By",default="ar")
	internalnotes   = fields.Text("Internal Notes",required=True)
	notes           = fields.Html("Notes",required=True)
	balance         = fields.Float("Balance",default=0,digit=(19,2),related="customer_id.balance") 

class CNWCustomerFollowupWiz(models.TransientModel):
	_name           = "cnw.cflwup.followup.wizard"
	_description    = "Customer Follow Up history Wizard"
	name            = fields.Char("No Follow-up ")
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)

	def _getcustomerdata(self):        
		bps= self.env["sap.bp"].browse(self.env.context.get("active_ids"))
		bps.ensure_one()
		return bps.id


	customer_id     = fields.Many2one("sap.bp", string="Customer",default=_getcustomerdata)
	docdate         = fields.Date("Doc Date",required=True,default=lambda s:fields.Date.today())
	cardcode        = fields.Char("Customer Code",related="customer_id.cardcode",store=True)
	cardname        = fields.Char("Customer Name",related="customer_id.cardname" )
	cardgroup       = fields.Char("Customer Group",related="customer_id.groupname" )
	salesname       = fields.Char("Sales Name",related="customer_id.salesperson" )
	arperson        = fields.Char("AR person",related="customer_id.ar_person" )

	followup_type   = fields.Selection(selection=[("mail","E-Mail"),("phone","Phone"),("whatsapp","Whatsapp"),("others","Other")],string="Type",default="phone")

	followup_by     = fields.Selection(selection=[("ar","Follow Up By AR"),("sales","Follow Up By Sales"),("debt_collector","Follow Up By Debt Collector (Iwan)")],string="Follow Up By",default="ar")
	internalnotes   = fields.Text("Internal Notes",required=True)
	notes           = fields.Html("Notes",required=True)
	balance         = fields.Float("Balance",default=0,digit=(19,2),related="customer_id.balance") 
 
	def save_followup(self): 

		followup_number = self.env["ir.sequence"].next_by_code("cflwup.no")

		followup = []

 
		followup.append(followup_number)
		followup.append(followup_number)
		followup.append(self.company_id.name)
		followup.append(self.customer_id.name)
		followup.append(self.docdate)
		followup.append(self.cardcode)
		followup.append(self.cardname)
		followup.append(self.cardgroup)
		followup.append(self.salesname)
		followup.append(self.arperson)
		followup.append(self.followup_type)
		followup.append(self.followup_by)
		followup.append(self.internalnotes)
		followup.append(self.notes)
		followup.append(self.balance)
		
		follow=[]
		follow.append(followup)

		bp_update=[]
		bp_update.append(self.customer_id.name)
		bp_update.append(self.customer_id.name) 
		bp_update.append(self.followup_type)
		bp_update.append(self.followup_by)
		bp_update.append(self.internalnotes) 
		bp_update.append(self.docdate) 
		bpups =[]
		bpups.append(bp_update)

		data = self.env["cnw.cflwup.followup"].load(["id",
											"name",
											"company_id",
											"customer_id",
											"docdate",
											"cardcode",
											"cardname",
											"cardgroup",
											"salesname",
											"arperson",
											"followup_type",
											"followup_by",
											"internalnotes",
											"notes",
											"balance",],follow)

		print (data)
		self.env["sap.bp"].load(["id",
								"name",  
								"followup_type",
								"followup_by",
								"laststatus",
								"laststatus_date",],bpups)

		
		
 
