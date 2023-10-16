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


class CNW_KARTUSTOCK(models.TransientModel):
	_name           = "cnw.awr28.kartustock"
	_description    = "cnw.kartustock"
	company_id      = fields.Many2many('res.company', string="Company",required=True)
	
	datefrom        = fields.Date ("Date From", default=fields.Date.today())
	dateto          = fields.Date ("Date To", default=fields.Date.today())  
	item            = fields.Char("Items / Code")
	filexls         = fields.Binary("File Output")    
	filenamexls     = fields.Char("File Name Output")
	export_to       = fields.Selection([ ('xls', 'Excel'),
				     					('json','JSON Format'),
										('pdf', 'PDF'),],string='Export To', default='xls')

	def view_kartustock(self): 
		mpath       = get_module_path('cnw_awr28')
		filex 		= 'kartustock_'+   datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y_%m_%d_%H_%M_%S") 
		filenamexls =  filex + '.xlsx'
		filenamepdf = filex + '.pdf'
		filenamejson = filex + '.json'
		filename    = 'kartustock'+   self.dateto.strftime("%Y%m%d")  + '.xlsx'
		filename    = ""
		filepath    = mpath + '/temp/'+ filename
		listfinal   = []
 
		item  = self.item  if self.item else ""
		
		for comp in self.company_id:
			host        = comp.server
			database    = comp.db_name
			user        = comp.db_usr
			password    = comp.db_pass
			#print (host,database,user,password)
			
			conn = pymssql.connect(host=host, user=user, password=password, database=database)

			#cursor = conn.cursor(as_dict=True)
			
			#cursor.execute( "exec [dbo].[IGU_LR_PERITEM] '" +  self.datefrom.strftime("%Y%m%d") + "', '" +  self.dateto.strftime("%Y%m%d") + "','"+ comp.code_base + "'")
			msg_sql = """
							declare @datefrom varchar(10), 
									@dateto varchar(10),
									@item varchar(10) ,
									@company varchar(20)

							declare @table table ( docentry int ,transtype int , doc_ref varchar(50))


							set @datefrom   = '""" +  self.datefrom.strftime("%Y%m%d") + """'
							set @dateto     = '""" +  self.dateto.strftime("%Y%m%d") + """'
							set @company    = '"""+ comp.code_base + """'
							set @item       = '"""+ item + """'
							
							insert into @table 
							SELECT a.docentry ,a.objtype, c.beginstr + convert(varchar,b.docnum) SO FROM ODLN (nolock) A 
								INNER JOIN ORDR  (nolock) B ON A.u_IGU_SODOcEntry = b.docEntry
								inner join nnm1  (nolock) c on b.series = c.series 
							WHERE convert(varchar,a.docdate,112)between @datefrom and @dateto
							union all 

							SELECT a.docentry ,a.objtype, a.numatCard SO FROM OINV  (nolock) A 
							WHERE convert(varchar,a.docdate,112)between @datefrom and @dateto

							union all
							SELECT distinct a.docentry ,a.objtype,A.BASEREF FROM PDN1  (nolock) A 
								WHERE convert(varchar,a.docdate,112)between @datefrom and @dateto AND A.BaseType=22

							select * from 
							(
							select @company company,
									a.itemcode ,
								b.itemname ,
								b.u_group ,
								b.u_subgroup ,
								isnull(convert(varchar,b.u_hs_code),'') HSCode,
								b.u_speGroup SpeGroup,
								' Opening' transtype ,
								@datefrom docdate,
								'' doc_ref, 
								' -' cardCode, 
								' -'CardName ,
								' -' ref1 ,
								' -'ref2,
								sum(a.inqty ) in_quantity ,
								sum(a.outqty) out_quantity ,
								sum(a.inqty - a.outqty) quantity ,
								0 price,
								sum(a.transvalue) amount
									from OINM  (nolock) A 
								INNER JOIN OITM  (nolock) B ON A.ITEMCODE = B.ITEMCODE  
							where convert(varchar,a.docdate,112) < @datefrom
							and b.itemcode + b.itemname like '%' + isnull(@item,'') + '%'
							group by a.itemcode ,
										b.itemname,
								b.u_group ,
								b.u_subgroup ,
								isnull(convert(varchar,b.u_hs_code),'')  ,
								b.u_speGroup  
							union all 

							select @company company,
									a.itemcode ,
								b.itemname ,
								b.u_group ,
								b.u_subgroup ,
								isnull(convert(varchar,b.u_hs_code),'') HSCode,
								b.u_speGroup SpeGroup,
								c.name transtype ,
								convert(varchar,a.docdate,112) docdate,
								isnull(e.doc_ref,'') ,
								a.cardCode, 
								a.CardName ,
								a.ref1 ,
								a.ref2,
								a.inqty  quantity ,
									a.outqty quantity ,
								isnull(a.inqty - a.outqty,0) quantity ,
								isnull(a.calcprice,0) calcprice, 
									(a.transvalue)  amount       
									from OINM  (nolock) A 
								INNER JOIN OITM  (nolock) B ON A.ITEMCODE = B.ITEMCODE 
								left outer join [@igu_transType] c on a.transtype = c.code 
								left outer join @table e on a.transtype = e.transtype and a.createdby = e.docentry 

							where convert(varchar, a.docdate,112) between @datefrom and @dateto
							and b.itemcode + b.itemname like '%' + isnull(@item,'') + '%'
							
							) as a 
							order by company ,itemcode, docdate  ,transtype
			"""
		   # msg_sql= "exec [dbo].[IGU_LR_PERITEM] '" +  self.datefrom.strftime("%Y%m%d") + "', '" +  self.dateto.strftime("%Y%m%d") + "','"+ partner + "','"+ item + "','"+ comp.code_base + "'"

			data = pandas.io.sql.read_sql(msg_sql,conn)
			listfinal.append(data)


 
		#print (listfinal)
#        df = pd.DataFrame.from_records(listfinal,columns=label,coerce_float=True)
		#df = pd.DataFrame.from_dict(listfinal)
		df = pd.concat(listfinal)
		df["Qty Balance"] = df.groupby(["company","itemcode"])["quantity"].cumsum()
		df["Amount Balance"] = df.groupby(["company","itemcode"])["amount"].cumsum()
		if self.export_to =="xls":
			filename = filenamexls
			df.to_excel(mpath + '/temp/'+ filename ) 
		elif self.export_to =="json":
			filename = filenamejson
			df.to_json(mpath + '/temp/'+ filenamejson,orient="records" )

		elif self.export_to =="pdf":
			filename = filenamepdf
			
			proyeksi = self.env["cnw.awr28.jasper"].search([("name","=","kartustock")])
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

 