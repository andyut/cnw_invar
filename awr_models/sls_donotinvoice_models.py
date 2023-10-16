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
import pymssql
from jinja2 import Environment, FileSystemLoader

class CNW_donotinvoiceREPORT(models.TransientModel):
	_name           = "cnw.awr28.donotinvoice"
	_description    = "cnw.awr28.donotinvoice"
	company_id      = fields.Many2many('res.company', string="Company",required=True)
	 
	dateto          = fields.Date ("Date To", default=fields.Date.today()) 
	arperson          = fields.Char ("AR Person")  
	customer          = fields.Char ("Customer")  
	jadwal          = fields.Char ("Jadwal"  )  
	
	export_to       = fields.Selection([ ('xls', 'Excel'),('pdf', 'PDF'),],string='Export To', default='pdf')
	filexls         = fields.Binary("File Output")    
	filenamexls     = fields.Char("File Name Output")
	
	@api.multi
	def view_awr28_donotinvoice(self): 
		mpath       = get_module_path('cnw_awr28')

		filex  		= 'sls_donotinvoice_'+   datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y%m%d%H%M%S")
		filenamexls = 'sls_donotinvoice_'+   self.dateto.strftime("%Y%m%d")  + '.xlsx'
		filenamepdf = 'sls_donotinvoice_'+   self.dateto.strftime("%Y%m%d")  + '.pdf'
		filename    =""
		filepath    = mpath + '/temp/'
		logo        = mpath + '/awr_template/logoigu.png'
		listfinal   = []
		cssfile     = mpath + '/awr_template/style.css'

		#global Var

		igu_title = "Belum Jadi invoice"
		igu_tanggal = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")
		igu_remarks = "Belum Jadi invoice Per Tanggal "
		options = {
					'page-size': 'legal',
					'orientation': 'portrait',
					}
		pd.options.display.float_format = '{:,.2f}'.format

		for comp in self.company_id:
			host        = comp.server
			database    = comp.db_name
			user        = comp.db_usr
			password    = comp.db_pass 
			
			#conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';UID='+user+';PWD='+ password + ';TrustServerCertificate=yes')
			conn = pymssql.connect(host=host, user=user, password=password, database=database)
			msg_sql= "exec dbo.IGU_ACT_DONOTINVOICE   '"+ self.dateto.strftime("%Y%m%d")   + "','" + comp.code_base  + "'"
			customer = self.customer if self.customer else ""
			arperson = self.arperson if self.arperson else ""
			jadwal = self.jadwal if self.jadwal else  ""

			msg_sql = """
							DECLARE 
												@dateto varchar(10) , @company varchar(50),
												@partner varchar(50) , 
												@arperson varchar(50) ,
												@tfnotes varchar(50)

										set @dateto ='""" + self.dateto.strftime("%Y%m%d")  +  """'
										set @partner ='""" + customer +"""'
										set @arperson ='""" + arperson +"""'
										set @tfnotes ='""" + jadwal +"""'
										set @company = '""" + comp.name + """' 
											SELECT DISTINCT 
													@company Company,
													@dateto 'Date To',
													T0.DOCENTRY ,
													T3.DOCSTATUS, 
													CONVERT(vARCHAR,T1.docduedate,112) DOCDATE,
													CONVERT(vARCHAR,T3.DOCDATE,112) POTONGSTOCK,
													t3.docnum,
													T2.BEGINSTR+ CONVERT(VARCHAR,T1.DOCNUM) DO_NUMBER ,
													T1.CARDCODE, 
													T1.SHIPTOCODE , 
													t6.groupname memo,
													T1.CARDNAME ,
													T3.NUMATCARD,
													T4.U_SlsEmpName, 
													T3.DocTotal,
													T1.COMMENTS  ,
													isnull(t5.Notes,'') TF ,
													t5.u_ar_Person ,
													convert(varchar,t3.createdate,23)  icreatedate,
													right('0000' + convert(varchar,t3.doctime),4) idocdate  
											FROM DLN1 T0 
												INNER JOIN ORDR T1 ON T0.BASEENTRY = T1.DOCENTRY AND T0.BASETYPE=17 
												INNER JOIN OCRD T5 ON T1.cardcode = t5.cardcode 
												INNER JOIN OCRG T6 ON T5.groupcode = t6.groupcode 
												INNER JOIN OSLP  T4 ON T5.SlpCode=T4.SlpCode
												INNER JOIN NNM1 T2 ON T1.[Series] = T2.[Series] AND T0.[TargetType] not in (13,15)
												INNER JOIN ODLN T3 ON T0.DOCENTRY = T3.DOCENTRY 
											WHERE   
													T1.CARDCODE + ISNULL(T1.SHIPTOCODE ,'') + ISNULL(T1.CARDNAME,'')   LIKE '%'+ isnull(replace(@partner ,' ','%'),'')+ '%'
												AND T3.DOCSTATUS ='O'
												AND CONVERT(VARCHAR,T1.docduedate,112)>='20161231'
												and CONVERT(VARCHAR,T1.docduedate,112)<=@dateto    
												AND T5.U_AR_PERSON LIKE '%' + isnull(replace(@arperson ,' ','%'),'') + '%'         
												AND isnull(T5.notes,'') LIKE '%' + isnull(replace(@tfnotes ,' ','%'),'') + '%'         
							
			"""

			data = pandas.io.sql.read_sql(msg_sql,conn)
			listfinal.append(data)

		df = pd.concat(listfinal)
		#df.loc['Total'] = df.select_dtypes(pd.np.number).sum().reindex(df.columns, fill_value='')
		



		
		if self.export_to =="xls":
			filename = filenamexls 
			df.to_excel(mpath + '/temp/'+ filenamexls)  
		else:
			# JINJA 2 Template
			proyeksi = self.env["cnw.awr28.jasper"].search([("name","=","doblmfaktur")])
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
		return {
			'name': 'Report',
			'type': 'ir.actions.act_url',
			'url': "web/content/?model=" + self._name +"&id=" + str(
				self.id) + "&filename_field=filenamexls&field=filexls&download=true&filename=" + self.filenamexls,
			'target': 'new',
			}
 
#        conn.close()    

 