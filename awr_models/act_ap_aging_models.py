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

from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class CNW_AP_AGING(models.TransientModel):
	_name           = "cnw.awr28.apaging"
	_description    = "cnw.awr28.apaging"
	company_id      = fields.Many2many('res.company', string="Company",required=True)
	 
	dateto          = fields.Date ("Date To", default=fields.Date.today()) 
	export_to       = fields.Selection([ ('xls', 'Excel'),('json','JSON Format'),('pdf', 'PDF Report')],string='Export To', default='pdf')
	filexls         = fields.Binary("File Output",default=" ")    
	filenamexls     = fields.Char("File Name Output" , default="txt.txt")
	
	@api.multi
	def view_apaging(self): 
		mpath       = get_module_path('cnw_awr28')

		filex           ='ap_aging_'+   self.env.user.company_id.db_name +   self.env.user.name +  self.dateto.strftime("%Y%m%d") 
		filenamejson    = filex + '.json'
		filenamepdf    = filex + '.json'
		filename    = 'ap_aging_'+   self.env.user.company_id.db_name +   self.env.user.name +  self.dateto.strftime("%Y%m%d")  + '.xlsx'
		filepath    = mpath + '/temp/'+ filename
		listfinal = []
		for comp in self.company_id:

			host        = comp.server
			database    = comp.db_name
			user        = comp.db_usr
			password    = comp.db_pass 
			
			#conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';UID='+user+';PWD='+ password + ';TrustServerCertificate=yes')
			conn = pymssql.connect(host=host, user=user, password=password, database=database)
			#cursor = conn.cursor()
			msgsql =  "exec [dbo].[IGU_AGING_AP] '" +  self.dateto.strftime("%Y%m%d") + "','"+ comp.code_base + "'"
			#cursor.execute( "exec [dbo].[IGU_AGING_AP] '" +  self.dateto.strftime("%Y%m%d") + "','"+ comp.code_base + "'")
			data = pandas.io.sql.read_sql(msgsql,conn)
			listfinal.append(data)
 

		df =  pd.concat(listfinal)

		if self.export_to =="xls":

			df.to_excel(mpath + '/temp/'+ filename )  
		elif self.export_to =="json":
			filename = filenamejson
			df.to_json(mpath + '/temp/'+ filenamejson,orient="records" )
		if self.export_to =="pdf":
#			df.pivot_table(index=["Company", "Partner Name","Currency"],aggfunc=np.sum,values=["06Totalfc","06Total"],fill_value="0",margins=True ).to_excel(mpath + '/temp/'+ filename )
			filename = filenamepdf
			
			proyeksi = self.env["cnw.awr28.jasper"].search([("name","=","ap_aging")])
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
			
			#jsondata = str(data)
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
			#print(payload)
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
		if self.export_to =="pdf":
			return {
				'type': 'ir.actions.do_nothing'
				}
		elif self.export_to =="pdf2":
			return {
				'type': 'ir.actions.do_nothing'
				}			 

		else :
			return {
				'name': 'Report',
				'type': 'ir.actions.act_url',
				'url': "web/content/?model=" + self._name +"&id=" + str(
					self.id) + "&filename_field=filenamexls&field=filexls&download=true&filename=" + self.filenamexls,
				'target': 'new',
				}
 
#        conn.close()    

 