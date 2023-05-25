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

class CNWKwitansiList(models.TransientModel):
	_name           = "cnw.invar.kwitansilist"
	_description    = "Kwitansi List"
	company_id      = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id.id )

	datetfrom		= fields.Date("Date From",default=lambda s:fields.Date.today(),required=True)
	dateto          = fields.Date("Date To",default=lambda s:fields.Date.today(),required=True)
	customer        = fields.Char("Business Partner",default="")
	kwitansi		= fields.Char("Kwitansi")
	filexls         = fields.Binary("File Output",default=" ")    
	filenamexls     = fields.Char("File Name Output",default="EmptyText.txt")
	 
	 
	export_to       = fields.Selection([ ('pdf','pdf')],string='Print To', default='pdf')

	def getCNWKwitansiList(self):


#PATH & FILE NAME & FOLDER
		mpath       = get_module_path('cnw_invar')
		filenamexls2    = 'KwitansiList'+   datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d%H%M%S") + '.xlsx'
		filenamepdf    = 'KwitansiList'+   datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d%H%M%S")  + '.pdf'
		filepath    = mpath + '/temp/'+ filenamexls2

		 
#LOGO CSS AND TITLE
		logo        = mpath + '/template/logoigu.png' 
		logo        = mpath + '/template/logo'+ self.company_id.code_base + '.png'
		cssfile     = mpath + '/template/style.css'        
		options = {
					'page-size': 'A4',
					'orientation': 'landscape',
					}
		igu_title = "Kwitansi Detail"
		igu_tanggal = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")
		igu_remarks = " Per Tanggal " + self.dateto.strftime("%Y-%m-%d")                    

#MULTI COMPANY 

		listfinal = []
		#pandas.options.display.float_format = '{:,.2f}'.format
		company = ""
		for comp in self.company_id:

			host        = comp.server
			database    = comp.db_name
			user        = comp.db_usr
			password    = comp.db_pass 
			company = comp.name
			 
			#conn = pymssql.connect(host=host, user=user, password=password, database=database)
			conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';UID='+user+';PWD='+ password + ';TrustServerCertificate=yes')
			
			bp = self.customer if self.customer else ""
			kwitansi = self.kwitansi if self.kwitansi else ""

			msgsql ="""
						declare @datefrom varchar(20), @dateto varchar(20) 
						declare @cardname varchar(50) , @kwitansi varchar(50)
						
						set nocount ON

						set @datefrom = '""" + self.datefrom.strftime("%Y%m%d")  + """'
						set @dateto = '""" + self.dateto.strftime("%Y%m%d")  + """'
						set @cardname = '""" + bp + """'
						set @kwitansi = '""" + kwitansi + """'
						select 
								a.kwt_no ,
								a.kwt_date, 
								a.kwt_indate,
								a.kwt_inuser,
								a.kwt_customer  + ' - ' + a.kwt_customername customer ,
								b.kwt_invNo,
								b.kwt_invdt ,
								b.kwt_customeroutlet,
								b.kwt_amt 
						from trade.t_t_skwitansi_Master a
						inner join trade.t_t_sKwitansi_detail b on a.kwt_no = b.kwt_no
						where a.kwt_date between @datefrom and @dateto
						and a.kwt_customer  + ' - ' + a.kwt_customername  like '%' + @cardname + '%'
						and a.kwt_no     like '%' + @kwitansi + '%'
						order by 	a.kwt_no ,
									a.kwt_date , 
									b.kwt_invNo
			"""
			#print(msgsql)
			data = pandas.io.sql.read_sql(msgsql,conn) 
			listfinal.append(data)
  
		


		df = pd.concat(listfinal)  
 

		if self.export_to =="pdf":
				   
			filename = filenamepdf
			env = Environment(loader=FileSystemLoader(mpath + '/kwt_models/'))

			rpt = df.values.tolist() 
			total = 0.0
			for iline in rpt :

				total	  += iline[8]

			
			template = env.get_template("kwitansilist.html")            
			template_var = {"logo":logo,
							"igu_title" :igu_title,
							"igu_tanggal" :igu_tanggal ,
							"igu_remarks" :igu_remarks , 
							"total" : total,
							"detail": rpt}
			
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
		

 