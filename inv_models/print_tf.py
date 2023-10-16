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
import pymssql
from jinja2 import Environment, FileSystemLoader
import pdfkit
import uuid 

 

class CNW_ARTFPrint(models.TransientModel):
	_name           = "ar.tf.print"
	_description    = "Cetakan Invoice"
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)
 
	dateto          = fields.Date("Date To",default=lambda s:fields.Date.today(), required=True)
	arperson        = fields.Char("AR Person",default="")
	collector 		= fields.Selection(string="Collector",
										selection=[("","All"),
													("YANTO","YANTO"),
													("WAWAN","WAWAN"),
													("JHON","JHON"),
													("IMAM","IMAM"),
													("SUSILO","SUSILO"),
													("IRFAN","IRFAN"),
													("JEFRI","JEFRI"),
													("BIBIT","BIBIT"),
													("FUAD","FUAD"),
													("ILYAS","ILYAS"),
													("FERRY","FERRY"),
													("AFFEN","AFFEN"),
													("BUDI","BUDI"),
													("BAYU","BAYU"),
													("TYO","TYO"),
													("YOHANES","YOHANES"),
													("RIDWAN","RIDWAN"),
													("NO COLLECTOR","NO COLLECTOR"),
													("POS","POS"),
													("AMIR","AMIR"),
													("AMIR","AMIR"), ],default="")
	collector2 		= fields.Selection(string="Collector2",
										selection=[("","All"),
													("YANTO","YANTO"),
													("WAWAN","WAWAN"),
													("JHON","JHON"),
													("IMAM","IMAM"),
													("SUSILO","SUSILO"),
													("IRFAN","IRFAN"),
													("JEFRI","JEFRI"),
													("BIBIT","BIBIT"),
													("FUAD","FUAD"),
													("ILYAS","ILYAS"),
													("FERRY","FERRY"),
													("AFFEN","AFFEN"),
													("BUDI","BUDI"),
													("BAYU","BAYU"),
													("TYO","TYO"),
													("YOHANES","YOHANES"),
													("RIDWAN","RIDWAN"),
													("NO COLLECTOR","NO COLLECTOR"),
													("POS","POS"),
													("AMIR","AMIR"),
													("AMIR","AMIR"), ],default="")
	 
	filexls         = fields.Binary("File Output",default=" ")    
	filenamexls     = fields.Char("File Name Output",default="EmptyText.txt")
	export_to       = fields.Selection([ 	('tf','Print TF'),
				     						('tfkw', 'Print TF Kwitansi'),
				     						('tt', 'Tanda Terima Faktur'),	
				     						('ttkwitansi', 'Tanda Terima Kwitansi'),	
				     						('json', 'TF JSON Format'),	 	
				     						('json2', 'TF Kwitansi JSON Format'),	 	
				     						('json3', 'TT JSON Format'),	 
											('ttdocs','Tanda Terima Faktur (MS Word)')],string='Print To', default='tf')
	
	def get_CetakanTF(self):

#PATH & FILE NAME & FOLDER
		mpath       	= get_module_path('cnw_invar')
		filex  			= 'TF_'+   datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y%m%d%H%M%S")
		filenamexls2    = filex + '.xlsx'
		filenamedocx    =   filex + '.docx'
		filenamertf    	=    filex + '.rtf'
		filenamepdf    	=   filex + '.pdf'
		filenamejson 	= filex + '.json'
		filepath    	= mpath + '/temp/'+ filenamexls2

		host        = self.company_id.server
		database    = self.company_id.db_name
		user        = self.company_id.db_usr
		password    = self.company_id.db_pass 
		companyname	= self.company_id.name
		companycode= self.company_id.code_base

		conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';UID='+user+';PWD='+ password + ';TrustServerCertificate=yes')


		collector = self.collector if self.collector else ""
		arperson = self.arperson if self.arperson else ""
		#collector = self.collector if self.collector else ""
		msgsql1 = """
						select  '""" + companyname + """'  Company,
								upper(case when isnull(a.u_coll_name,'')  ='' then b.u_Coll_Name else a.U_Coll_Name end)  U_Coll_Name , 
								upper(b.U_AR_Person) U_AR_Person,
								b.CardCode + ' - ' +   b.cardname customer , 
								a.U_Kw_No ,
								convert(varchar,a.U_kw_PrintDate,23) docdate,
								convert(varchar,a.TAXDATE,23) TFDate,
								sum(a.DocTotal - a.PaidSys) amount ,
								isnull(a.U_RemDelay,'') notes1

						from oinv a 
						inner join ocrd b on a.cardcode = b.cardcode 
						where convert(varchar,a.taxdate,112) = '""" +  self.dateto.strftime("%Y%m%d")    + """'  
						AND (isnull(b.U_AR_Person,'') like '%' + isnull( '""" + arperson + """' ,'')  + '%' )
						AND (upper(case when isnull(a.u_coll_name,'')  =''  then b.u_Coll_Name else a.U_Coll_Name end)  like '%' +   isnull( '""" + collector + """' ,'')  + '%' )
						and isnull(a.U_Kw_No,'')<>''
						and isnull(a.U_LT_No,'')<>''
						group by 
							upper(case when isnull(a.u_coll_name,'')  ='' then b.u_Coll_Name else a.U_Coll_Name end)   , 
							upper(b.U_AR_Person),
								b.CardCode + ' - ' +   b.cardname  , 
								a.U_Kw_No , 
								convert(varchar,a.U_kw_PrintDate,23),
								convert(varchar,a.TAXDATE,23) , 
								isnull(a.U_RemDelay,'') 
						order by  upper(case when isnull(a.u_coll_name,'')  ='' then b.u_Coll_Name else a.U_Coll_Name end)   , 
								upper(b.U_AR_Person)
					"""
		msgsql2 = """
						select  '""" + companyname + """'  Company,
								upper(case when isnull(a.u_coll_name,'')='' then b.u_Coll_Name else a.U_Coll_Name end)  U_Coll_Name , 
								upper(b.U_AR_Person)U_AR_Person,
								b.CardCode + ' - ' +   b.cardname  customer ,
								a.ShipToCode  ,
								a.NumAtCard ,
								isnull(a.U_Kw_No,'')  U_Kw_No,
								convert(varchar,a.DocDate,23) docdate,
								convert(varchar,a.TAXDATE,23) TFDate,
								a.DocTotal - a.PaidSys amount ,
								isnull(a.U_RemDelay,'') notes1

						from oinv a 
						inner join ocrd b on a.cardcode = b.cardcode 
						where convert(varchar,a.taxdate,112) =  '""" +  self.dateto.strftime("%Y%m%d")    + """'  
						and (isnull(b.U_AR_Person,'') like '%' + isnull(  '""" + arperson + """' ,'') + '%' )
						and (isnull(case when isnull(a.u_coll_name,'')='' then b.u_Coll_Name else a.U_Coll_Name end,'')  like '%' + isnull( '""" + collector + """'  ,'') + '%' )
						and 
							isnull(a.U_LT_no,'')  <>''
						order by  convert(varchar,a.TAXDATE,23)  ,upper(a.U_Coll_Name ), 
							upper( b.U_AR_Person)
					"""
		msgsql3 = """
					declare @dateto varchar(20),
							@arperson varchar(50),
							@collector varchar(50)
					set nocount on
					set @dateto = '""" +  self.dateto.strftime("%Y%m%d")    + """'  
					set @arperson = '""" + arperson + """'  
					set @collector = '""" + collector + """'  
					select  
							'""" + companyname + """'  Company,
							upper(case when isnull(a.u_coll_name,'')='' then b.u_Coll_Name else a.U_Coll_Name end)  U_Coll_Name , 
							upper(b.U_AR_Person)U_AR_Person,
							b.CardCode ,
							b.cardname  customer ,
							a.ShipToCode  ,
							a.NumAtCard ,
							isnull(a.U_Kw_No,'')  U_Kw_No,
							convert(varchar,a.DocDate,23) docdate,
							convert(varchar,a.TAXDATE,23) TFDate,
							a.DocTotal - a.PaidSys amount ,
							isnull(a.U_RemDelay,'') notes1,
							       a.U_Cust_PO_No


					from oinv a 
					inner join ocrd b on a.cardcode = b.cardcode 
					where convert(varchar,a.taxdate,112) = @dateto 
					and (isnull(b.U_AR_Person,'') like '%' + isnull(  @arperson,'') + '%' )
					and (isnull(case when isnull(a.u_coll_name,'')='' then b.u_Coll_Name else a.U_Coll_Name end,'')  like '%' + isnull(  @collector,'') + '%' )
					and 
						isnull(a.U_LT_no,'')  <>''
					order by  convert(varchar,a.TAXDATE,23)  ,upper(a.U_Coll_Name ), 
						upper( b.U_AR_Person)
		"""
		
		if self.export_to =="json":
			msgsql = msgsql2
		elif self.export_to =="json2":
			msgsql = msgsql1
		elif self.export_to =="json3":
			msgsql = msgsql3
		elif self.export_to =="tf":
			msgsql = msgsql2
		elif self.export_to =="tfkw":
			msgsql = msgsql1
		elif self.export_to =="tt":
			msgsql = msgsql3
		elif self.export_to =="ttkwitansi":
			msgsql = msgsql1
		elif self.export_to =="ttdocs":
			msgsql = msgsql3
		
		listfinal = []
		pandas.options.display.float_format = '{:,.2f}'.format
		company = ""
		data = pandas.io.sql.read_sql(msgsql,conn) 
		listfinal.append(data)

		df = pd.concat(listfinal)  
		
		#url = "http://192.168.250.19:8080/jasperserver/flow.html?_flowId=viewReportFlow&standAlone=true&_flowId=viewReportFlow&ParentFolderUri=%2Freports%2FIGU%2FAR&reportUnit=%2Freports%2FIGU%2FAR%2Finvoice_print_c4_odoo&j_username=jasperadmin&j_password=jasperadmin&decorate=no&prm_datefrom="+ self.datefrom.strftime("%Y-%m-%d")  +"&prm_dateto="+ self.dateto.strftime("%Y-%m-%d")  + "&prm_inv_from=" + self.inv_from  + "&prm_inv_to=" + self.inv_to  + "&prm_ppn=&output=pdf"
		if self.export_to =="tf" :
			if companycode =="igu23":

				url = "http://192.168.250.19:8080/jasperserver/flow.html?_flowId=viewReportFlow&standAlone=true&_flowId=viewReportFlow&ParentFolderUri=%2Freports%2FIGU%2FAR&reportUnit=%2Freports%2FIGU%2FAR%2FTF2&j_username=jasperadmin&j_password=jasperadmin&decorate=no&dateto="+ self.dateto.strftime("%Y%m%d") + "&arperson="+ self.arperson + "&collector=" + collector + "&output=pdf"
				return {
							"type": "ir.actions.act_url",
							"url": url,
							"target": "new",
						}    
			else:
				proyeksi = self.env["cnw.invar.jasper"].search([("name","=","tf")])
				input_file 		= mpath + '/temp/' +  filex + ".jrxml" 
				data_file 		= mpath + '/temp/' +  filex + ".json" 
				output_file 	= mpath + '/temp/' +  filex
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

		elif self.export_to =="tfkw" :
			if companycode=="igu23":

				url = "http://192.168.250.19:8080/jasperserver/flow.html?_flowId=viewReportFlow&standAlone=true&_flowId=viewReportFlow&ParentFolderUri=%2Freports%2FIGU%2FAR&reportUnit=%2Freports%2FIGU%2FAR%2F05_tfkw&j_username=jasperadmin&j_password=jasperadmin&decorate=no&dateto="+ self.dateto.strftime("%Y%m%d") + "&arperson="+ self.arperson + "&collector=" + collector + "&output=pdf"
			
				return {
							"type": "ir.actions.act_url",
							"url": url,
							"target": "new",
						}     	
			else :

				proyeksi = self.env["cnw.invar.jasper"].search([("name","=","tfkw")])
				input_file 		= mpath + '/temp/' +  filex + ".jrxml" 
				data_file 		= mpath + '/temp/' +  filex + ".json" 
				output_file 	= mpath + '/temp/' +  filex
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


		elif self.export_to=="json":
			filename = filenamejson
			df.to_json(mpath + "/temp/" + filenamejson, orient="records")

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
		elif self.export_to=="json2":
			filename = filenamejson
			df.to_json(mpath + "/temp/" + filenamejson, orient="records")

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
		elif self.export_to=="json3":
			filename = filenamejson
			df.to_json(mpath + "/temp/" + filenamejson, orient="records")

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
		
		elif self.export_to =="tt" :
			proyeksi = self.env["cnw.invar.jasper"].search([("name","=","tandaterima")])
			input_file 		= mpath + '/temp/' +  filex + ".jrxml" 
			data_file 		= mpath + '/temp/' +  filex + ".json" 
			output_file 	= mpath + '/temp/' +  filex
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
		elif self.export_to =="ttkwitansi" :
			proyeksi = self.env["cnw.invar.jasper"].search([("name","=","tandaterimakwitansi")])
			input_file 		= mpath + '/temp/' +  filex + ".jrxml" 
			data_file 		= mpath + '/temp/' +  filex + ".json" 
			output_file 	= mpath + '/temp/' +  filex
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

		else :
			proyeksi = self.env["cnw.invar.jasper"].search([("name","=","tandaterima")])
			input_file 		= mpath + '/temp/' +  filex + ".jrxml" 
			data_file 		= mpath + '/temp/' +  filex + ".json" 
			output_file 	= mpath + '/temp/' +  filex
			filename 		= filenamedocx 


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
						"extension" : 'docx'
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
