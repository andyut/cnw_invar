# -*- coding: utf-8 -*-
import requests 
import xlsxwriter
import numpy as np
import pandas as pd
import pandas.io.sql
import os
import pdfkit
import pytz
from odoo.exceptions import UserError
from odoo.modules import get_modules, get_module_path
from datetime import datetime
from odoo import models, fields, api
import base64
import pyodbc  
from jinja2 import Environment, FileSystemLoader

class CNW_MdlSlsORderList(models.Model):
	_name           = "cnw.awr28.mdlslsorderlist"
	_description    = "Model Sales Order list"
	company_id      = fields.Many2one('res.company', string="Company",required=True)
	name            = fields.Char("Name")
	canceled		= fields.Char("Canceled")
	cardcode        = fields.Char("Partner Code")
	cardname        = fields.Char("Partner Name")
	customergroup   = fields.Char("Customer Group")
	shiptocode      = fields.Char("Ship To")
	ordername       = fields.Char("PO Customer")
	so_number       = fields.Char("SO Number")
	docdate         = fields.Date("Doc Date")
	itemcode        = fields.Char("Item Code")
	ugroup 			= fields.Char("Item Group")
	usubgroup 		= fields.Char("Item Sub Group")
	uspegroup		= fields.Char("Item Commodity Group")
	ubrand			= fields.Char("Item Brand")
	itemdescription = fields.Char("Item Description")
	salesperson     = fields.Char("Sales Person")
	uom             = fields.Char("UOM")
	quantity_order  = fields.Float("Quantity Order",digit=(19,2),default=0)
	price           = fields.Float("Price",digit=(19,2))
	quantity_out    = fields.Float("Quantity Out",digit=(19,2))
	total           = fields.Float("Total",digit=(19,2))
	inuser          = fields.Integer("User")

class CNW_SLSOrderLog(models.Model):
	_name 			= "cnw.awr28.mdlslsorderlist.log"
	_description 	= "mdlslsorderlist Log"
	company_id      = fields.Many2many('res.company', string="Company",required=True)

	name 			= fields.Char("ID Number")
	datefrom        = fields.Date ("Date from", default=fields.Date.today()) 
	dateto          = fields.Date ("Date To", default=fields.Date.today()) 
	salesperson     = fields.Char("Sales Person")
	cardname        = fields.Char("Partner Name")
	item            = fields.Char("Item")
	customergroup   = fields.Char("Customer Group")
	itemgroup       = fields.Char("Item Group")	


	def create(self,vals):
		docdate = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d")
		numbering  = self.env["cnw.numbering.wizard"].getnumbering('SLSORLOG',datetime.now(pytz.timezone('Asia/Jakarta')))
		#print(numbering)
		vals["name"] = numbering 
		result = super(CNW_SLSOrderLog,self).create(vals)
		return result	



class CNW_SlsOrderList(models.TransientModel):
	_name           = "cnw.awr28.slsorderlist"
	_description    = "cnw.awr28.slsorderlist"
	company_id      = fields.Many2many('res.company', string="Company",required=True)
	 
	datefrom          = fields.Date ("Date from", default=fields.Date.today()) 
	dateto          = fields.Date ("Date To", default=fields.Date.today()) 
	salesperson     = fields.Char("Sales Person")
	cardname        = fields.Char("Partner Name")
	item            = fields.Char("Item")
	customergroup   = fields.Char("Customer Group")
	itemgroup       = fields.Char("Item Group")
	export_to       = fields.Selection([('list','List View'), ('xls', 'Excel'),('pdf', 'PDF'),],string='Export To', default='list')
	filexls         = fields.Binary("File Output", default=" ")    
	filenamexls     = fields.Char("File Name Output",default="textemp.txt")
	
	@api.multi
	def view_SlsOrderList(self): 
		mpath       = get_module_path('cnw_awr28')
		filex 	    =   datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y%m%d%H%M%S")  
		filenamexls = 'sls_orderlist_'+   filex + '.xlsx'
		filenamepdf = 'sls_orderlist_'+   filex  + '.pdf'
		filename    =""
		filepath    = mpath + '/temp/'
		logo        = mpath + '/awr_template/logoigu.png'
		listfinal   = []
		cssfile     = mpath + '/awr_template/style.css'

		#global Var
		self.env["cnw.awr28.mdlslsorderlist.log"].create({
			"company_id" : self.company_id ,
			"datefrom" : self.datefrom ,
			"dateto" : self.dateto ,
			"salesperson" : self.salesperson ,
			"cardname" : self.cardname ,
			"item" : self.item ,
			"customergroup" : self.customergroup ,
			"itemgroup" : self.itemgroup })
		igu_title = "Sales Order List"
		igu_tanggal = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")
		igu_remarks = "Sales Order List Per Tanggal "
		options = {
					'page-size': 'A4',
					'orientation': 'landscape',
					}
		pd.options.display.float_format = '{:,.2f}'.format

		for comp in self.company_id:
			host        = comp.server
			database    = comp.db_name
			user        = comp.db_usr
			password    = comp.db_pass 
			conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';UID='+user+';PWD='+ password + ';TrustServerCertificate=yes')
			
			 
			#msg_sql= "exec dbo.IGU_ACT_DONOTINVOICE   '"+ self.dateto.strftime("%Y%m%d")   + "','" + comp.code_base  + "'"

			cardname = self.cardname if self.cardname else ""
			item = self.item if self.item else ""
			customergroup = self.customergroup if self.customergroup else ""
			itemgroup = self.itemgroup if self.itemgroup else "" 
			salesperson = self.salesperson if self.salesperson else "" 
			
			msg_sql= """ 
						declare @datefrom varchar(10), @dateto varchar(10) 
						declare @item varchar(100) 
						declare @cardname varchar(100)
						declare @customergroup varchar(100)
						declare @itemgroup varchar(100)
						declare @salesperson varchar(100)

						set @datefrom =  '""" + self.datefrom.strftime("%Y%m%d")   + """'
						set @dateto =  '""" + self.dateto.strftime("%Y%m%d")   + """'
						set @cardname =  '""" + cardname   + """'
						set @item =  '""" + item   + """'
						set @customergroup =  '""" + customergroup   + """'
						set @itemgroup =  '""" + itemgroup   + """' 
						set @salesperson =  '""" + salesperson   + """' 

						select               '""" + comp.code_base + """' + convert(varchar,t0.docentry) +'_' + convert(varchar,t5.linenum) as id,
											'""" + comp.name + """' + convert(varchar,t0.docentry) +'_' + convert(varchar,t5.linenum) as name,
												'""" + str(comp.id) + """' company_id,
												t1.cardname,
												upper(ISNULL(t0.shiptocode,' ')) shiptocode,  
												isnull(t0.numatCard,'')  as ordername ,
												t7.groupname  as customergroup ,
												isnull(t2.beginstr,'SO20') + convert( varchar,t0.docNum ) so_number,
												convert(varchar, t0.docdueDate ,23) docdate ,												
												t5.itemCode ,
												t5.Dscription  + ' ' +  isnull(t5.freetxt,'') itemdescription,
												t3.invntryuom uom,
												t5.QUANTITY quantity_order,
												t5.PriceBefDi price  ,
												isnull(t6.quantity ,0) quantity_out,
												isnull(t6.quantity ,0)*    t5.price  total ,
												t10.slpName SalesPerson ,
												t0.canceled ,
												t3.u_group  ,
												t3.u_subgroup  ,
												t3.u_speGroup ,
												t3.u_brand ,
												t0.cardcode

								from .dbo.ordr (nolock) t0 
										inner join dbo.ocrd (nolock) t1  on t0.cardCode = t1.cardCode 
										inner join  dbo.rdr1 (nolock) t5 on t0.docEntry = t5.docEntry 
										inner join  dbo.nnm1 (nolock) t2 on t0.series = t2.series 
										inner join  dbo.ocrg (nolock) t7 on t1.groupcode = t7.groupcode 
										inner join  dbo.OSLP (nolock) t10 on t0.slpcode = t10.slpcode 
										inner join  dbo.OITM (nolock) t3 on t5.itemCode = t3.itemCode
										inner join  dbo.OITB  (nolock) t4 on t3.itmsGrpCod = t4.itmsGrpCod 
										left outer join dbo.DLN1  (nolock) t6 
											ON	T5.TargetType = 15 
												and   t5.TrgetEntry = t6.docentry 
									and 
							t5.LineNum = t6.BaseLine  
						WHERE t0.canceled IN('N','Y')
						and  docdueDate between @datefrom and @dateto  
						and t0.cardcode + isnull(t1.cardname,'') + isnull(t0.shiptocode,'') like '%'+ isnull(@cardname,'')  + '%'              
						and t3.itemcode + isnull(t3.u_group,'') + isnull(t3.itemname,'') like '%'+ isnull(@item,'')  + '%'                    
						and t7.groupname like '%'+ isnull(@customergroup,'')  + '%'            
						and t3.u_group like '%'+ isnull(@itemgroup,'')  + '%'               
						and t10.slpname like '%'+ isnull(@salesperson,'')  + '%'              
			"""

			data = pandas.io.sql.read_sql(msg_sql,conn)
			listfinal.append(data)

		df = pd.concat(listfinal)
		
		
		datalist2 = df.values.tolist()



		#print(datalist2)
		if self.export_to=="list":
			#print("user :::: ")
			#print(self.env.user.id)
			#listinuser = self.env["cnw.awr28.mdlslsorderlist"].search([("write_uid","=",self.env.user.id)])
			self.env.cr.execute ("""DELETE FROM cnw_awr28_mdlslsorderlist WHERE write_uid =""" + str(self.env.user.id) + """ """ ) 
			#if listinuser :
			#	for deleteline in listinuser:
			#		deleteline.unlink()
			#		#print("Deleted Row before")
			
			#		#print(deleteline)

			for line in datalist2:

				self.env["cnw.awr28.mdlslsorderlist"].create({
											"name" 				: line[1],  
											"cardname"			: line[3],
											"company_id"		: line[2],
											"shiptocode"		: line[4],
											"ordername"			: line[5],
											"customergroup"		: line[6],
											"so_number"			: line[7],
											"docdate"			: line[8],
											"itemcode"			: line[9],
											"itemdescription"	: line[10],
											"uom"				: line[11],
											"quantity_order"	: line[12],
											"price"				: line[13],
											"quantity_out"		: line[14],
											"total"				: line[15],
											"salesperson"		: line[16],
											"canceled" 			: line[17],
											"ugroup"			: line[18],
											"usubgroup"			: line[19],
											"uspegroup"			: line[20],
											"ubrand"			: line[21],
											"cardcode"			: line[22 ]
											})
			return {
				"type": "ir.actions.act_window",
				"res_model": "cnw.awr28.mdlslsorderlist",  
				#"view_id":view_do_list_tree, 
				"view_mode":"tree,pivot",
				"act_window_id":"cnw_awr28_mdlslsorderlist_action"}
		else:
			#df.loc['Total'] = df.select_dtypes(pd.np.number).sum().reindex(df.columns, fill_value='')
			if self.export_to =="xls":
				filename = filenamexls 
				df.to_excel(mpath + '/temp/'+ filenamexls)  
			else:
				# JINJA 2 Template
				# dfpdf = df[["canceled","so_number","docdate","cardname","SalesPerson","shiptocode","ordername","itemdescription","quantity_order","quantity_out","price","total"]]
				# filename = filenamepdf
				# env = Environment(loader=FileSystemLoader(mpath + '/awr_template/'))
				# template = env.get_template("awr_template_report.html")            
				# template_var = {"logo":logo,
				# 				"igu_title" :igu_title,
				# 				"igu_tanggal" :igu_tanggal ,
				# 				"igu_remarks" :igu_remarks ,
				# 				"detail": dfpdf.to_html(index=True,float_format='{:20,.2f}'.format)}
				
				# html_out = template.render(template_var)
				# pdfkit.from_string(html_out,mpath + '/temp/'+ filenamepdf,options=options,css=cssfile) 

				proyeksi = self.env["cnw.awr28.jasper"].search([("name","=","orderlist")])
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
	## END JASPER REPORT        

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
			
			
	
#        conn.close()    

 