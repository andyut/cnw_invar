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


class AWR_HPPGlobal(models.TransientModel):
	_name           = "cnw.awr28.hppglobal"
	_description    = "cnw.awr28.hppglobal"
	company_id      = fields.Many2many('res.company', string="Company",required=True)
	datefrom        = fields.Date ("Date From", default=fields.Date.today()) 
	dateto          = fields.Date ("Date To", default=fields.Date.today()) 
	export_to       = fields.Selection([ ('xls', 'Excel'),('pdf', 'PDF'),('summary', 'Summary'),('summary2', 'Summary2'),],string='Export To', default='summary2')
	filexls         = fields.Binary("File Output")    
	filenamexls     = fields.Char("File Name Output")
	
	
	
	def view_pl(self): 
		mpath       = get_module_path('cnw_awr28')
		filename    = 'HPPGLobal_'+ self.env.user.company_id.db_name +  self.dateto.strftime("%Y%m%d")  + '.xlsx'
		filenamexls    = 'HPPGLobal_'+ self.env.user.company_id.db_name +   self.dateto.strftime("%Y%m%d")  + '.xlsx'
		filenamexls2    = 'HPPGLobal_'+  self.env.user.company_id.db_name +  self.dateto.strftime("%Y%m%d")  + '.xlsx'
		filenamepdf = 'HPPGLobal_'+  self.env.user.company_id.db_name +  self.dateto.strftime("%Y%m%d")  + '.pdf'
		filepath    = mpath + '/temp/'+ filename
		logo        = mpath + '/awr_template/logoigu.png' 
		listfinal   = []
		options = {
					'orientation': 'portrait',
					}        
		igu_tanggal = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")
		
		for comp in self.company_id:

			host        = comp.server
			database    = comp.db_name
			user        = comp.db_usr
			password    = comp.db_pass 
			
			conn = pymssql.connect(host=host, user=user, password=password, database=database)
			#conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';UID='+user+';PWD='+ password + ';TrustServerCertificate=yes')
			
			cursor = conn.cursor()
		 
			msg_sql=  "exec [dbo].[IGU_ACCT_HPPGLOBAL2]  '" +  self.datefrom.strftime("%Y%m%d") + "','" +  self.dateto.strftime("%Y%m%d") + "','"+ comp.code_base + "' "

			data = pandas.io.sql.read_sql(msg_sql,conn)
			listfinal.append(data)

 

		df = pd.concat(listfinal)
		dflist = df.values.tolist() 

		if self.export_to =="xls":
			filename = filenamexls2 
			#report = df.groupby(["Group","AR Person"]).sum()
			df.to_excel(mpath + '/temp/'+ filenamexls2,index=False)


		if self.export_to =="summary":
			filename = filenamexls2 
			summary = df.pivot_table(index=["itype","Name"],columns=["Company"],aggfunc=np.sum,  values=["Amount"],fill_value="0",margins=True )
			#report = df.groupby(["Group","AR Person"]).sum()
			summary.to_excel(mpath + '/temp/'+ filenamexls2)

		if self.export_to =="summary2":
			filename = filenamexls2 
			summary = df.pivot_table(index=["itype"],columns=["Company"],aggfunc=np.sum,  values=["Amount"],fill_value="0",margins=True )
			#report = df.groupby(["Group","AR Person"]).sum()
			summary.to_excel(mpath + '/temp/'+ filenamexls2)            
		if self.export_to =="pdf":
			filename = filenamepdf
			
			env = Environment(loader=FileSystemLoader(mpath + '/template/'))
			template = env.get_template("hppglobal_template.html")            
			#print(dflist)
			template_var = {"company":self.env.user.company_id.name,
							"igu_title" :"HPP Global",
							"datetime" :igu_tanggal ,
							"dateto" :self.dateto.strftime("%Y-%m-%d") ,
							"igu_remarks" :"HPP Global" ,
							"data":dflist}
			
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
 
#        conn.close()    

 