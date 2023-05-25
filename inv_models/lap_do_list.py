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
import pymssql
from jinja2 import Environment, FileSystemLoader
import pdfkit




class CNWDOLIST(models.TransientModel):
	_name           = "cnw.invar.dolist"
	_description    = "INVAR DO List"
	company_id      = fields.Many2one('res.company', 'Company', required=True)

	datefrom        = fields.Date("Date From",default=lambda s:fields.Date.today())
	dateto          = fields.Date("Date To",default=lambda s:fields.Date.today())
	customer        = fields.Char("Business Partner",default="")
	filexls         = fields.Binary("File Output",default="-")    
	filenamexls     = fields.Char("File Name Output",default="test.txt")
	
	export_to       = fields.Selection([ ('xls', 'Excel'),('pdf', 'PDF'),],string='Export To', default='pdf')

	def get_solist(self):

#PATH & FILE NAME & FOLDER
		mpath       = get_module_path('cnw_invar')
		filenamexls2    = 'DOLIST_'+   self.dateto.strftime("%Y%m%d")  + '.xlsx'
		filenamepdf    = 'DOLIST_'+   self.dateto.strftime("%Y%m%d")  + '.pdf'
		filepath    = mpath + '/temp/'+ filenamexls2

#LOGO CSS AND TITLE
		logo        = mpath + '/template/logoigu.png' 
		logo        = mpath + '/template/logo'+ self.company_id.code_base + '.png'
		cssfile     = mpath + '/template/style.css'        
		options = {
					'page-size': 'A4',
					'orientation': 'portrait',
					}
		igu_title = "Sales Order List"
		igu_tanggal = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")
		igu_remarks = "Per Tanggal " + self.dateto.strftime("%Y-%m-%d")                    

#MULTI COMPANY 

		listfinal = []
		pandas.options.display.float_format = '{:,.2f}'.format
		for comp in self.company_id:

			host        = comp.server
			database    = comp.db_name
			user        = comp.db_usr
			password    = comp.db_pass 
			
			conn = pymssql.connect(host=host, user=user, password=password, database=database)
			
			bp = self.customer if self.customer else ""

			msgsql =  "exec [dbo].[IGU_ACT_SALDOPIUTANGDETAIL] '" +  self.dateto.strftime("%Y%m%d") + "','" + bp + "','"  + comp.code_base + "' " 
			msgsql = """
						select '""" + comp.name  + """' company , 
								convert(varchar,T0.docduedate,105) Dates,  
								t1.beginstr + convert(varchar,T0.DocNum) Docnum,
								T0.CardCode , 
								T0.CardName+' ['+ T0.CardCode+']' CardName ,
								t0.numatCard,
								isnull( t0.comments,'-'), 
								left(right('' + convert(varchar, T0.doctime),4),2) + ':' + right(right('00' + convert(varchar, T0.doctime),4),2) docTime 
								FROM ORDR T0  
												INNER JOIN NNM1 T1 ON T0.Series = T1.Series
						where convert(varchar,t0.docdate ,112)  between '""" + self.datefrom.strftime("%Y%m%d") + """' and '""" + self.dateto.strftime("%Y%m%d") + """'
						and T0.cardcode + T0.cardname like '%""" + bp + """%' 
						order by convert(varchar,T0.DocNum)  ,  T0.docduedate
						""" 
			data = pandas.io.sql.read_sql(msgsql,conn) 
			listfinal.append(data)
  
		


		df = pd.concat(listfinal) 

		if self.export_to =="xls":
			filename = filenamexls2 
			#report = df.groupby(["Group","AR Person"]).sum()
			df.to_excel(mpath + '/temp/'+ filenamexls2,index=False,engine='xlsxwriter') 
		else:
				   
			filename = filenamepdf
			env = Environment(loader=FileSystemLoader(mpath + '/template/'))
			dolist = df.values.tolist() 
			template = env.get_template("dolist.html")            
			template_var = {"logo":logo,
							"igu_title" :igu_title,
							"igu_tanggal" :igu_tanggal ,
							"igu_remarks" :igu_remarks ,
							"detail":dolist}
			
			html_out = template.render(template_var)
			pdfkit.from_string(html_out,mpath + '/temp/'+ filenamepdf,options=options ) 
	 
		
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
		
