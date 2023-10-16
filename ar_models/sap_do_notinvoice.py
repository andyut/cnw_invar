# -*- coding: utf-8 -*-
import requests 
import xlsxwriter
import os
import pytz
import numpy as np
import pandas as pd
import pandas.io.sql
from odoo.exceptions import UserError
from odoo.modules import get_modules, get_module_path
from datetime import datetime
from odoo import models, fields, api
import base64
import pymssql


class SAPDOBelumInvoice(models.TransientModel):
	_name           = "sap.belumfaktur"
	_description    = "sap.belumfaktur"
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
	dateto          = fields.Date ("Date To", default=lambda s:fields.Date.today())
	partner         = fields.Char("Business Partner",default=" ") 
	arperson        = fields.Char("AR Person",default="")
	tukarfaktur     = fields.Char("Jadwal Tukar Faktur",default="")
	export_to       = fields.Selection([ ('Summary', 'Summary'),
											('Items', 'Items'),
											 ('json','JSON Format (summary)'),
											 ('json2','JSON Format (detail)'),
											  ('pdf','PDF Summary Format'),
											  ('pdf2','PDF Detail Format'),
												],string='Export To', default='pdf')    
	filexls         = fields.Binary("File Output", default=" ")    
	filenamexls     = fields.Char("File Name Output",default="txt.txt")


	@api.multi
	def view_belumfaktur_xls(self): 
		#PATH FILE 
		mpath       	= get_module_path('cnw_invar')
		filex 			= 'OpenDO_' + self.env.user.company_id.code_base + "_"  + self.env.user.name  +   self.dateto.strftime("%Y%m%d") 
		filenamexls2    = filex  + '.xlsx'
		filenamejson    = filex  + '.json'
		filenamepdf    	= filex   + '.pdf'
		filename    	= filex   + '.xlsx'
		filepath    = mpath + '/temp/'+ filename

		#SERVER CONFIGURATION
		host        = self.env.user.company_id.server
		database    = self.env.user.company_id.db_name
		user        = self.env.user.company_id.db_usr
		password    = self.env.user.company_id.db_pass

		partner = self.partner if self.partner else ""
		arperson = self.arperson if self.arperson else ""
		tukarfaktur = self.tukarfaktur if self.tukarfaktur else "" 

		#EXECUTE STORE PROCEDURE 
		conn = pymssql.connect(host=host, user=user, password=password, database=database)
		
		msgsql1 =  """
					declare 
							@dateto varchar(10) ,
							@partner varchar(50) , 
							@arperson varchar(50) ,
							@tfnotes varchar(50)

					set @dateto ='"""+  self.dateto.strftime("%Y%m%d") + """'
					set @partner ='"""  + partner + """'
					set @arperson ='"""  + arperson + """'
					set @tfnotes ='"""  + tukarfaktur + """'           
						SELECT DISTINCT 
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
								isnull(t5.Notes,'') TF
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
		msgsql2 = """
					declare 
							@dateto varchar(10) ,
							@partner varchar(50) ,
							@arperson varchar(50) ,
							@tfnotes varchar(50)

					set @dateto ='"""+  self.dateto.strftime("%Y%m%d") + """'
					set @partner ='"""  + partner + """'
					set @arperson ='"""  + arperson + """'
					set @tfnotes ='"""  + tukarfaktur + """'
						SELECT DISTINCT 
								@dateto 'Date To',
								T0.DOCENTRY ,
								T3.DOCSTATUS, 
								CONVERT(vARCHAR,T1.DOCDATE,112) DOCDATE,
								t3.docnum,
								T2.BEGINSTR+ CONVERT(VARCHAR,T1.DOCNUM) DO_NUMBER ,
								T1.CARDCODE, 
								T1.SHIPTOCODE , 
								t6.groupname memo,
								T1.CARDNAME ,
								T3.NUMATCARD,
								T4.U_SlsEmpName, 
								T0.itemcode ,
								T0.dscription ,
								T0.Quantity ,
								T0.Price ,
								T0.vatgroup,
								T0.VATSUM PPn,
								T0.linetotal ,
									isnull(t5.Notes,'') tf
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
							AND CONVERT(VARCHAR,T3.docdate,112)>='20161231'
							and CONVERT(VARCHAR,T3.docdate,112)<=@dateto  
							AND T5.U_AR_PERSON LIKE '%' + isnull(replace(@arperson ,' ','%'),'') + '%'         
							AND isnull(T5.notes,'') LIKE '%' + isnull(replace(@tfnotes ,' ','%'),'') + '%'   
								
		"""
		if self.export_to=="Summary":
			mssql = msgsql1 
		elif self.export_to=="Items":
			mssql = msgsql2
		elif   self.export_to=="json":
			mssql = msgsql1
		elif   self.export_to=="json2":
			mssql = msgsql2
		elif   self.export_to=="pdf":
			mssql = msgsql1
		elif   self.export_to=="pdf2":
			mssql = msgsql2
		listfinal =[]
		data = pandas.io.sql.read_sql(mssql,conn) 
		listfinal.append(data)
		df = pd.concat(listfinal) 
		print(mssql)


		if self.export_to=="Summary":
			filename = filenamexls2 
			#report = df.groupby(["Group","AR Person"]).sum()
			df.to_excel(mpath + '/temp/'+ filenamexls2,index=False,engine='xlsxwriter')      

		elif self.export_to=="Items":
			filename = filenamexls2 
			#report = df.groupby(["Group","AR Person"]).sum()
			df.to_excel(mpath + '/temp/'+ filenamexls2,index=False,engine='xlsxwriter')      
		elif   self.export_to=="json":
			filename = filenamejson 
			#report = df.groupby(["Group","AR Person"]).sum()
			df.to_json(mpath + '/temp/'+ filenamejson,orient="records")      
		elif   self.export_to=="json2":
			filename = filenamejson 
			#report = df.groupby(["Group","AR Person"]).sum()
			df.to_json(mpath + '/temp/'+ filenamejson,orient="records")      
		elif   self.export_to=="pdf":
			filename = filenamepdf
			proyeksi = self.env["cnw.invar.jasper"].search([("name","=","notinvoice")])
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
		elif   self.export_to=="pdf2":
			filename = filenamepdf
			proyeksi = self.env["cnw.invar.jasper"].search([("name","=","notinvoicedetail")])
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
					"extension" 	: 'pdf'
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


		if self.export_to=="Summary":
			return {
				'name': 'Report',
				'type': 'ir.actions.act_url',
				'url': "web/content/?model=" + self._name +"&id=" + str(
					self.id) + "&filename_field=filenamexls&field=filexls&download=true&filename=" + self.filenamexls,
				'target': 'new',
				}
		elif self.export_to=="Items":
			return {
				'name': 'Report',
				'type': 'ir.actions.act_url',
				'url': "web/content/?model=" + self._name +"&id=" + str(
					self.id) + "&filename_field=filenamexls&field=filexls&download=true&filename=" + self.filenamexls,
				'target': 'new',
				}
		elif   self.export_to=="json":
			return {
				'name': 'Report',
				'type': 'ir.actions.act_url',
				'url': "web/content/?model=" + self._name +"&id=" + str(
					self.id) + "&filename_field=filenamexls&field=filexls&download=true&filename=" + self.filenamexls,
				'target': 'new',
				}
		elif   self.export_to=="json2":
			return {
				'name': 'Report',
				'type': 'ir.actions.act_url',
				'url': "web/content/?model=" + self._name +"&id=" + str(
					self.id) + "&filename_field=filenamexls&field=filexls&download=true&filename=" + self.filenamexls,
				'target': 'new',
				}
		elif   self.export_to=="pdf":
			return {
				'type': 'ir.actions.do_nothing'
				}
		elif   self.export_to=="pdf2":
			return {
				'type': 'ir.actions.do_nothing'
				}
		 

 
