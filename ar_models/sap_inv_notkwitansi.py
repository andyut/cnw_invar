# -*- coding: utf-8 -*-
import requests 
import xlsxwriter
import os
import numpy as np
import pandas as pd
import pandas.io.sql
import pytz
from odoo.exceptions import UserError
from odoo.modules import get_modules, get_module_path
from datetime import datetime
from odoo import models, fields, api
import base64
import pymssql


class SAPINVNotKwitansi(models.TransientModel):
	_name           = "sap.notkwitansi"
	_description    = "sap.notkwitansi"
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
	datefrom          = fields.Date ("Date To", default=lambda s:fields.Date.today()) 
	dateto          = fields.Date ("Date To", default=lambda s:fields.Date.today()) 
	arperson        = fields.Char("AR Person")
	customer        = fields.Char("Customer")
	jadwal        	= fields.Char("Jadwal")
	export_to       = fields.Selection([    ('xls', 'Excel'),
											('json', 'JSON Format'),
											('pdf', 'PDF Format'),
											],string='Export To', default='pdf')
	filexls         = fields.Binary("File Output",default=" ")    
	filenamexls     = fields.Char("File Name Output" , default="txt.txt")


	@api.multi
	def view_notkwitansi_xls(self): 
		#PATH FILE 
		mpath       = get_module_path('cnw_invar')
		filex = 'NotKwitansi_' + self.env.user.company_id.code_base + "_"  + self.env.user.name  +   self.dateto.strftime("%Y%m%d") 
		filenamexls2    = 'NotKwitansi_' + self.env.user.company_id.code_base + "_"  + self.env.user.name  +   self.dateto.strftime("%Y%m%d")   + '.xlsx'
		filenamejson    = 'NotKwitansi_' + self.env.user.company_id.code_base + "_"  + self.env.user.name  +   self.dateto.strftime("%Y%m%d")   + '.json'
		filenamepdf    = 'NotKwitansi_' + self.env.user.company_id.code_base + "_"  + self.env.user.name  +   self.dateto.strftime("%Y%m%d")   + '.pdf'
		filename    = 'NotKwitansi_' + self.env.user.company_id.code_base + "_"  + self.env.user.name  +   self.dateto.strftime("%Y%m%d")   + '.xlsx'
		filepath    = mpath + '/temp/'+ filename

		arperson = self.arperson if self.arperson else ""
		customer = self.customer if self.customer else ""
		jadwal = self.jadwal if self.jadwal else ""

		#SERVER CONFIGURATION
		host        = self.env.user.company_id.server
		database    = self.env.user.company_id.db_name
		user        = self.env.user.company_id.db_usr
		password    = self.env.user.company_id.db_pass
		listfinal=[]
		#EXECUTE STORE PROCEDURE 
		conn = pymssql.connect(host=host, user=user, password=password, database=database)

		cursor = conn.cursor()
		mssql=   "exec [dbo].[IGU_INVOICE_NOT_KWITANSI_DATE] '" +  self.datefrom.strftime("%Y%m%d") + "','" +  self.dateto.strftime("%Y%m%d") + "','" +  self.company_id.code_base + "'" 
		mssql = """
				DECLARE 
					@DateFrom varchar(10),
					@DateTo varchar(10),
					@COMPANY VARCHAR(50),
					@ARPERSON VARCHAR(20),
					@JADWAL VARCHAR(100),
					@CUSTOMER VARCHAR(50)

					SET @DATEFROM = '""" + self.datefrom.strftime("%Y%m%d") + """'
					SET @DATETO = '""" + self.dateto.strftime("%Y%m%d") + """'
					SET @COMPANY = '""" +  self.company_id.code_base + """'
					SET @ARPERSON = '""" + arperson + """' 
					SET @CUSTOMER = '""" + customer + """'
					SET @JADWAL = '""" + jadwal + """'

					select  @COMPANY COMPANY,
							A.DOCNUM, 
							A.NUMATCARD,
							CONVERT(VARCHAR,A.DocDate,23) DOCDATE,
							C.GROUPNAME ,
							A.CARDCODE,
							A.CARDNAME , 
							A.SHIPTOCODE,  
							A.U_IDU_FPajak ,
							A.U_Cust_PO_No ,
							A.VATSUM PPN ,
							A.DocTotal ,
							upper(b.U_AR_Person) U_AR_Person ,
							ISNULL(D.U_SlsEmpName,D.SLPNAME) SALES ,
							isnull(b.notes,'') jadwal
							
					from OINV A 
					INNER JOIN OCRD  B ON A.CARDCODE = B.CARDCODE
					inner join OCRG C ON B.GROUPCODE = C.GROUPCODE
					INNER JOIN OSLP D ON B.SlpCode = D.SlpCode
					WHERE A.CANCELED='N'
					AND CONVERT(VARCHAR,A.DOCDATE,112) BETWEEN @DateFrom aND @DateTo
					AND 
					coalesce(u_kw_no,'') =''
					AND b.cardcode + b.cardname like '%' + @CUSTOMER + '%' 
					AND b.U_AR_Person  LIKE '%' + @ARPERSON + '%' 
					AND b.Notes  LIKE '%' + @JADWAL + '%' 
					order by docdate,cardcode        
		
		"""
		data = pandas.io.sql.read_sql(mssql,conn) 
		listfinal.append(data)
		df = pd.concat(listfinal) 

		if self.export_to =="xls":
			filename = filenamexls2 
			#report = df.groupby(["Group","AR Person"]).sum()
			df.to_excel(mpath + '/temp/'+ filenamexls2,index=False,engine='xlsxwriter')          
		elif self.export_to == "json":
			filename = filenamejson
			#report = df.groupby(["Group","AR Person"]).sum()
			df.to_json(mpath + '/temp/'+ filenamejson,orient="records")         
		elif self.export_to == "pdf":
			filename = filenamepdf
			proyeksi = self.env["cnw.invar.jasper"].search([("name","=","invoicenotkwitansi")])
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
		 
		
 
