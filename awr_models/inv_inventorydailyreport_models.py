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


class CNW_inventorydailyreport(models.TransientModel):
	_name           = "cnw.awr28.inventorydailyreport"
	_description    = "cnw.inventorydailyreport"
	company_id      = fields.Many2many('res.company', string="Company",required=True)
	datefrom        = fields.Date ("Date From", default=fields.Date.today()) 
	dateto          = fields.Date ("Date To", default=fields.Date.today()) 
	item            = fields.Char("Item",default="")
	warehouse       = fields.Char("Warehouse",default="")
	export_to       = fields.Selection([ 	('xls', 'Excel'),
				     						('xlswh', 'XLS Per Warehouse'),
				     						('json', 'jsonFormat'),
				     						('json2', 'Json format Per Warehouse'),
				     						('pdf', 'PDF'),
				     						('pdf2', 'PDF format Per Warehouse'),
				     						('hs', 'Per HS Group'),
				     						('hsdetail', 'Per HS Group Detail'),
				     					],string='Export To', default='xls')
	filexls         = fields.Binary("File Output")    
	filenamexls     = fields.Char("File Name Output")
	
	
	@api.multi
	def view_inventorydailyreport(self): 
		mpath       = get_module_path('cnw_awr28')
		filex 		= 'DailyReport_'+ datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y%m%d%H%M%S")
		filenamejson= filex + '.json'
		filename    = 'DailyReport_'+   self.dateto.strftime("%Y%m%d")  + '.xlsx'
		filenamexls    = 'DailyReport_'+   self.dateto.strftime("%Y%m%d")  + '.xlsx'
		filenamexls2   = filex + '.xlsx'
		filenamepdf =filex + '.pdf'
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
			
			cursor = conn.cursor()
			item = self.item if self.item else ""
			warehouse  = self.warehouse if self.warehouse   else ""
			msg_pertanian= """
							declare 
							
									@datefrom varchar(10) , 
									@dateto varchar(10) , 
									@item varchar(50) ,
									@group varchar(50),
									@company varchar(50)



							set @datefrom = '"""+  self.datefrom.strftime("%Y%m%d")  +"""'
							set @dateto = '""" +  self.dateto.strftime("%Y%m%d")  +"""'
							set @item = '""" + item + """'
							set @group = ''

							set @company = '""" + comp.code_base  + """'            
								select 
									@company Company,
									@datefrom DateFrom,
									@dateto Dateto,
									B.U_PERTANIAN ,
									
									SUM ( CASE when convert(varchar,a.docdate,112)< @datefrom then  (A.INQTY - a.OUTQTY) else 0 end ) OpeningBalanceQty,

                                    SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
                                                    and a.transtype in ( 20,19,21,18,69 ) and left(a.cardcode,2)='VI'
                                                then  (A.INQTY - a.OUTQTY) else 0 end ) PembelianImportQty,

                                    SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
                                                    and a.transtype in ( 20,19,21,18,69 ) and left(a.cardcode,2)<>'VI'
                                                then  (A.INQTY - a.OUTQTY) else 0 end ) PembelianLokalQty,


									SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
													and a.transtype in (14,16,13,15 ) 
												then  (A.INQTY - a.OUTQTY) else 0 end ) PenjualanQty,

									SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
													and a.transtype in (67) 
												then  (A.INQTY - a.OUTQTY) else 0 end ) InventoryTransferQty, 

									SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
													and a.transtype in (-2,58,60,162,59 ) 
												then  (A.INQTY - a.OUTQTY) else 0 end ) AdjustmentQty, 

									SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
													and a.transtype in (10000071) 
												then  (A.INQTY - a.OUTQTY) else 0 end ) SAPOpnameQty, 

									SUM ( CASE when convert(varchar,a.docdate,112)<= @dateto then  (A.INQTY - a.OUTQTY) else 0 end ) EndingBalanceQty
							from OINM (NOLOCK)A
								INNER JOIN OITM (NOLOCK) B ON A.ITEMCODE = B.ITEMCODE  
							where 
								convert(varchar,a.docdate,112) <=@dateto
								and a.itemcode + b.itemname like '%' + isnull(@item,'') +'%' 
							 AND ISNULL(B.U_PERTANIAN,'')<>''
							group by 
							B.U_PERTANIAN
							order by 
							B.U_PERTANIAN            
			""" 
			msg_sql=  "exec [dbo].[IGU_ACCT_DAILYINVENTORY] '" +  self.datefrom.strftime("%Y%m%d") + "', '" +  self.dateto.strftime("%Y%m%d") + "', '" +  warehouse + "', '" +  item + "','"+ comp.code_base + "' "
			msg_wh="""
						declare 
						
								@datefrom varchar(10) , 
								@dateto varchar(10) , 
								@item varchar(50) ,
								@group varchar(50),
								@company varchar(50)



						set @datefrom = '"""+  self.datefrom.strftime("%Y%m%d")  +"""'
						set @dateto = '""" +  self.dateto.strftime("%Y%m%d")  +"""'
						set @item = '""" + item + """'
						set @group = ''

						set @company = '""" + comp.code_base  + """'

						select 
								@company Company,
								@datefrom DateFrom,
								@dateto Dateto,
								B.u_GROUP ,
								B.U_SUBGROUP ,                                      
								A.ITEMCODE ,
								B.ITEMNAME ,

								SUM ( CASE when convert(varchar,a.docdate,112)< @datefrom then  (A.INQTY - a.OUTQTY) else 0 end ) OpeningBalanceQty,
								SUM ( CASE when convert(varchar,a.docdate,112)< @datefrom then  (A.transvalue) else 0 end ) OpeningBalanceAmt,

								SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
												and a.transtype in ( 20,19,21,18,69 ) 
											then  (A.INQTY - a.OUTQTY) else 0 end ) PembelianQty,
								SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
												and a.transtype in ( 20,19,21,18,69 ) 
											then  (A.transvalue) else 0 end ) PembelianAmt,


								SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
												and a.transtype in (14,16,13,15 ) 
											then  (A.INQTY - a.OUTQTY) else 0 end ) PenjualanQty,
								SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
												and a.transtype in (14,16,13,15 ) 
											then  (A.transvalue) else 0 end ) PenjualanAmt,

								SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
												and a.transtype in (67) 
											then  (A.INQTY - a.OUTQTY) else 0 end ) InventoryTransferQty, 
								SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
												and a.transtype in (67) 
											then  (A.transvalue) else 0 end ) InventoryTransferAmt, 

								SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
												and a.transtype in (-2,58,60,162,59 ) 
											then  (A.INQTY - a.OUTQTY) else 0 end ) AdjustmentQty, 
								SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
												and a.transtype in (-2,58,60,162,59 ) 
											then  (A.transvalue) else 0 end ) AdjustmentAmt, 

								SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
												and a.transtype in (10000071) 
											then  (A.INQTY - a.OUTQTY) else 0 end ) SAPOpnameQty, 
								SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
												and a.transtype in (10000071) 
											then  (A.transvalue) else 0 end ) SAPOpnameAmt, 

								SUM ( CASE when convert(varchar,a.docdate,112)<= @dateto then  (A.INQTY - a.OUTQTY) else 0 end ) EndingBalanceQty,
								SUM ( CASE when convert(varchar,a.docdate,112)<= @dateto then  (A.transvalue) else 0 end ) EndingBalanceAmt
						from OINM (NOLOCK)A
							INNER JOIN OITM (NOLOCK) B ON A.ITEMCODE = B.ITEMCODE  
						where 
							convert(varchar,a.docdate,112) <=@dateto
							and a.itemcode + b.itemname like '%' + isnull(@item,'') +'%' 

						group by 
						A.ITEMCODE ,
								B.ITEMNAME ,
								B.u_GROUP ,
								B.U_SUBGROUP   
						
						order by 
								B.u_GROUP ,
								B.U_SUBGROUP   ,
						A.ITEMCODE ,
								B.ITEMNAME 

			"""
			 
			msg_sql=  "exec [dbo].[IGU_ACCT_DAILYINVENTORY_TOTAL] '" +  self.datefrom.strftime("%Y%m%d") + "', '" +  self.dateto.strftime("%Y%m%d") + "', '" +  warehouse + "', '" +  item + "','"+ comp.code_base + "' "
			msg_hsdetail ="""
						declare 
						
								@datefrom varchar(10) , 
								@dateto varchar(10) , 
								@item varchar(50) ,
								@group varchar(50),
								@company varchar(50)



						set @datefrom = '"""+  self.datefrom.strftime("%Y%m%d")  +"""'
						set @dateto = '""" +  self.dateto.strftime("%Y%m%d")  +"""'
						set @item = '""" + item + """'
						set @group = ''

						set @company = '""" + comp.code_base  + """'

								select 
										@company Company,
										@datefrom DateFrom,
										@dateto Dateto,
										b.U_Pertanian,
										B.u_GROUP ,
										B.U_SUBGROUP ,  
										isnull(replace(replace(b.u_spec,char(10),''),char(13),''),'') spec,
										A.ITEMCODE ,
										B.ITEMNAME ,
										SUM ( CASE when convert(varchar,a.docdate,112)< @datefrom then  (A.INQTY - a.OUTQTY) else 0 end ) OpeningBalanceQty,

										SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
														and a.transtype in ( 20,19,21,18,69 ) and left(a.cardcode,2)='VI'
													then  (A.INQTY - a.OUTQTY) else 0 end ) PembelianImportQty,
										SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
														and a.transtype in ( 20,19,21,18,69 ) and left(a.cardcode,2)<>'VI' 
													then  (A.INQTY - a.OUTQTY) else 0 end ) PembelianLokalQty,
										SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
														and a.transtype in (14,16,13,15 ) 
													then  (A.INQTY - a.OUTQTY) else 0 end ) PenjualanQty,


										SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
														and a.transtype in (67) 
													then  (A.INQTY - a.OUTQTY) else 0 end ) InventoryTransferQty, 


										SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
														and a.transtype in (-2,58,60,162,59 ) 
													then  (A.INQTY - a.OUTQTY) else 0 end ) AdjustmentQty, 


										SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
														and a.transtype in (10000071) 
													then  (A.INQTY - a.OUTQTY) else 0 end ) SAPOpnameQty, 


										SUM ( CASE when convert(varchar,a.docdate,112)<= @dateto then  (A.INQTY - a.OUTQTY) else 0 end ) EndingBalanceQty
								from OINM (NOLOCK)A
									INNER JOIN OITM (NOLOCK) B ON A.ITEMCODE = B.ITEMCODE  
								where 
									convert(varchar,a.docdate,112) <=@dateto
									and a.itemcode + b.itemname like '%' + isnull(@item,'') +'%' 
								and isnull(b.u_pertanian,'')<>''
								group by 
								A.ITEMCODE ,
										B.ITEMNAME ,
										B.u_GROUP ,b.U_Pertanian,isnull(replace(replace(b.u_spec,char(10),''),char(13),''),''),
										B.U_SUBGROUP   
								
								order by b.U_Pertanian,
										B.u_GROUP ,
										B.U_SUBGROUP   ,
								A.ITEMCODE ,
										B.ITEMNAME 			
			"""
			msg_daily= """
						declare 
						
								@datefrom varchar(10) , 
								@dateto varchar(10) , 
								@item varchar(50) ,
								@group varchar(50),
								@company varchar(50)




						set @datefrom = '"""+  self.datefrom.strftime("%Y%m%d")  +"""'
						set @dateto = '""" +  self.dateto.strftime("%Y%m%d")  +"""'
						set @item = '""" + item + """'
						set @group = ''

						set @company = '""" + comp.code_base  + """'

						select 
								@company Company,
								@datefrom DateFrom,
								@dateto Dateto,
								B.u_GROUP ,
								B.U_SUBGROUP ,  
								A.ITEMCODE ,
								B.ITEMNAME ,
								SUM ( CASE when convert(varchar,a.docdate,112)< @datefrom then  (A.INQTY - a.OUTQTY) else 0 end ) OpeningBalanceQty,
								SUM ( CASE when convert(varchar,a.docdate,112)< @datefrom then  (A.transvalue) else 0 end ) OpeningBalanceAmt,

								SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
												and a.transtype in ( 20,19,21,18,69 ) 
											then  (A.INQTY - a.OUTQTY) else 0 end ) PembelianQty,
								SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
												and a.transtype in ( 20,19,21,18,69 ) 
											then  (A.transvalue) else 0 end ) PembelianAmt,


								SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
												and a.transtype in (14,16,13,15 ) 
											then  (A.INQTY - a.OUTQTY) else 0 end ) PenjualanQty,
								SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
												and a.transtype in (14,16,13,15 ) 
											then  (A.transvalue) else 0 end ) PenjualanAmt,

								SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
												and a.transtype in (67) 
											then  (A.INQTY - a.OUTQTY) else 0 end ) InventoryTransferQty, 
								SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
												and a.transtype in (67) 
											then  (A.transvalue) else 0 end ) InventoryTransferAmt, 

								SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
												and a.transtype in (-2,58,60,162,59) 
											then  (A.INQTY - a.OUTQTY) else 0 end ) AdjustmentQty, 
								SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
												and a.transtype in (-2,58,60,162,59 ) 
											then  (A.transvalue) else 0 end ) AdjustmentAmt, 

								SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
												and a.transtype in (10000071) 
											then  (A.INQTY - a.OUTQTY) else 0 end ) SAPOpnameQty, 
								SUM ( CASE when convert(varchar,a.docdate,112)between  @datefrom  and @dateto
												and a.transtype in (10000071) 
											then  (A.transvalue) else 0 end ) SAPOpnameAmt, 

								SUM ( CASE when convert(varchar,a.docdate,112)<= @dateto then  (A.INQTY - a.OUTQTY) else 0 end ) EndingBalanceQty,
								SUM ( CASE when convert(varchar,a.docdate,112)<= @dateto then  (A.transvalue) else 0 end ) EndingBalanceAmt
						from OINM (NOLOCK)A
							INNER JOIN OITM (NOLOCK) B ON A.ITEMCODE = B.ITEMCODE  
						where 
							convert(varchar,a.docdate,112) <=@dateto
							and a.itemcode + b.itemname like '%' + isnull(@item,'') +'%' 

						group by 
						A.ITEMCODE ,
								B.ITEMNAME ,
								B.u_GROUP ,
								B.U_SUBGROUP   
						
						order by 
								B.u_GROUP ,
								B.U_SUBGROUP   ,
						A.ITEMCODE ,
								B.ITEMNAME 
												
			"""
			if self.export_to =="xlswh":
				msg_sql=  msg_wh

			if self.export_to =="xls":
				msg_sql=  msg_daily

			if self.export_to =="json":
				msg_sql=  msg_daily

			if self.export_to =="json2":
				msg_sql=  msg_wh
			if self.export_to =="pdf":
				msg_sql=  msg_daily

			if self.export_to =="pdf2":
				msg_sql=  msg_wh

			if self.export_to =="hs":
				msg_sql=  msg_pertanian

			if self.export_to =="hsdetail":
				msg_sql = msg_hsdetail
              
			data = pandas.io.sql.read_sql(msg_sql,conn)
			listfinal.append(data)

 

		df = pd.concat(listfinal)
		if self.export_to =="xlswh":
			filename = filenamexls2 
			#report = df.groupby(["Group","AR Person"]).sum()
			df.to_excel(mpath + '/temp/'+ filenamexls2,index=False)

		if self.export_to =="xls":
			filename = filenamexls2 
			#report = df.groupby(["Group","AR Person"]).sum()
			df.to_excel(mpath + '/temp/'+ filenamexls2,index=False)

		if self.export_to =="json":
			filename = filenamejson 
			#report = df.groupby(["Group","AR Person"]).sum()
			df.to_json(mpath + '/temp/'+ filenamejson,orient="records")
		
		if self.export_to =="json2":
			filename = filenamejson 
			#report = df.groupby(["Group","AR Person"]).sum()
			df.to_json(mpath + '/temp/'+ filenamejson,orient="records")
		if self.export_to =="pdf":
			filename = filenamepdf
			
			proyeksi = self.env["cnw.awr28.jasper"].search([("name","=","dailyreport1")])
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
			print(payload)
			response = appSession.post(url, json=payload,verify=False)
			print(response.text)

			os.remove(input_file )
			os.remove(data_file )

		if self.export_to =="pdf2":
			filename = filenamepdf
			
			proyeksi = self.env["cnw.awr28.jasper"].search([("name","=","dailyreport2")])
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
			print(payload)
			response = appSession.post(url, json=payload,verify=False)
			print(response.text)

			os.remove(input_file )
			os.remove(data_file )


		if self.export_to =="hs":
			msg_sql=  msg_pertanian

		if self.export_to =="hsdetail":
			msg_sql = msg_hsdetail


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

 