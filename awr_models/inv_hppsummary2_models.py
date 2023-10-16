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


class CNW_hppsummary22(models.TransientModel):
	_name           = "cnw.awr28.hppsummary2"
	_description    = "cnw.hppsummary2"
	company_id      = fields.Many2many('res.company', string="Company",required=True) 
	items           = fields.Char("Items")
	igroup 			= fields.Char("Item Group")
	export_to       = fields.Selection([ ('xls', 'Excel'), 
											('xlswh', 'XLS Per Warehouse'),
											('hs', ' Per HS Group'),
											('json', 'JSON Format'),
											('pdf', 'PDF'),],string='Export To', default='xls')
	filexls         = fields.Binary("File Output",default=" ")    
	filenamexls     = fields.Char("File Name Output" ,default="file.txt")
	
	 
	def view_hppsummary2(self): 
		mpath       = get_module_path('cnw_awr28')

		filex  			= 'Persediaan_'+   datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y%m%d%H%M%S")
		filename    	= filex + '.xlsx'
		filenamexls    	=filex  + '.xlsx'
		filenamexls2    = filex + '.xlsx'
		filenamejson    = filex + '.json'
		filenamepdf 	= filex + '.pdf'
		filepath    	= mpath + '/temp/'+ filename
 

		logo        = mpath + '/awr_template/logoigu.png' 
		listfinal   = []
		options = {
					'orientation': 'portrait',
					}        
		igu_tanggal = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")

		items = self.items if self.items else ""
		igroup = self.igroup if self.igroup else ""

		for comp in self.company_id:

			host        = comp.server
			database    = comp.db_name
			user        = comp.db_usr
			password    = comp.db_pass 
			
			#conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';UID='+user+';PWD='+ password + ';TrustServerCertificate=yes')
			conn = pymssql.connect(host=host, user=user, password=password, database=database)
			msg_pertanian = """ declare
												@dateto varchar(10) ,
												@item varchar(50) ,
												@company varchar(10) ,
												@igroup varchar(50)
 
									set @item = '""" + items  + """'
									set @company = '""" + comp.code_base + """'
									set @igroup ='""" + igroup + """' 

								select 
											@company company,
											 B.U_PERTANIAN HS, 
											 
											sum(A.onhand) qty,
                                            avg(a.avgprice) avgprice,
											sum(A.onhand * a.avgprice) Total, 
                                            'KG' UOM
									from OITW A (nolock)
										inner join OITM b (nolock) on a.itemcode = b.itemcode 
									where   b.itemcode + b.itemname + isnull(b.u_group,'') like '%' + isnull(@item,'') + '%'  -- and a.TransValue<>0
									and b. InvntItem ='Y'
									and  isnull(b.u_group,'') like  '%' + isnull(@igroup,'') + '%' 
                                    and 	ISNULL(CONVERT(VARCHAR,B.U_PERTANIAN),'') <>''
									group by 
											B.U_PERTANIAN  
									having  sum(A.onhand * a.avgprice) <>0 
                                    ORDER BY B.U_PERTANIAN 
		
			"""			
			msg_summary = """
									declare
												@dateto varchar(10) ,
												@item varchar(50) ,
												@company varchar(10) ,
												@igroup varchar(50)
 
									set @item = '""" + items  + """'
									set @company = '""" + comp.code_base + """'
									set @igroup ='""" + igroup + """' 

									select 
											@company company,
											ISNULL(CONVERT(VARCHAR,B.U_HS_CODE),'') HSCODE,
											b.u_group ,
											b.u_subgroup,
											b.U_SPEGROUP ,
											b.U_Category ,
											b.u_country ,
											b.u_spec ,
											b.VatGroupPu PPnMasukan,
											b.VatGourpSa PPnKeluaran,
											a.itemcode ,b.itemname, 
											sum(A.onhand) qty,
											sum(A.onhand * a.avgprice) Total,
											b.invntryUom 
									from OITW A (nolock)
										inner join OITM b (nolock) on a.itemcode = b.itemcode 
									where   b.itemcode + b.itemname + isnull(b.u_group,'') like '%' + isnull(@item,'') + '%'  -- and a.TransValue<>0
									and b. InvntItem ='Y'
									and  isnull(b.u_group,'') like  '%' + isnull(@igroup,'') + '%' 
									group by 
											ISNULL(CONVERT(VARCHAR,B.U_HS_CODE),'') ,
											b.u_group ,
											b.u_subgroup,
											b.U_SPEGROUP ,
											b.U_Category ,
											b.VatGroupPu ,
											b.VatGourpSa ,
											b.u_country ,
											b.u_spec ,
											a.itemcode ,
											b.itemname,
											b.invntryUom
									having  sum(A.onhand * a.avgprice) <>0
									order by  b.u_group,b.u_subgroup, a.itemcode 

			
			"""
			msg_warehouse = """
									declare
												@dateto varchar(10) ,
												@item varchar(50) ,
												@company varchar(10),
												@igroup varchar(50)
												
 
									set @item = '""" + items  + """'
									set @company = '""" + comp.code_base + """'
									set @igroup ='""" + igroup + """' 
									

									select 
											@company company,
											ISNULL(CONVERT(VARCHAR,B.U_HS_CODE),'') HSCODE,
											b.u_group ,
											b.u_subgroup,
											b.U_SPEGROUP ,
											b.U_Category ,
											b.u_country ,
											b.u_spec ,
											a.itemcode ,b.itemname, 
											c.whsname warehouse,
											sum(A.onhand) qty,
											sum(A.onhand * a.avgprice) Total,
											b.invntryUom 
									from OITW A (nolock)
										inner join OITM b (nolock) on a.itemcode = b.itemcode 
										inner join OWHS c on a.whscode = c.whscode 
									where   b.itemcode + b.itemname + isnull(b.u_group,'') like '%' + isnull(@item,'') + '%'  -- and a.TransValue<>0
									and b. InvntItem ='Y'
									and  isnull(b.u_group,'') like  '%' + isnull(@igroup,'') + '%' 
									group by 
											c.whsname ,ISNULL(CONVERT(VARCHAR,B.U_HS_CODE),'') ,
											b.u_group ,
											b.u_subgroup,
											b.U_SPEGROUP ,
											b.U_Category ,
											b.u_country ,
											b.u_spec ,
											a.itemcode ,
											b.itemname,
											b.invntryUom
									having  sum(A.onhand * a.avgprice) <>0
									order by  
											c.whsname ,b.u_group,b.u_subgroup, a.itemcode 

			
			"""

			#cursor = conn.cursor()
			if self.export_to =="xlswh":
				msg_sql=  msg_warehouse

			if self.export_to =="xls":
				msg_sql=  msg_summary
			if self.export_to =="json":
				msg_sql=  msg_summary

			if self.export_to =="hs":
				msg_sql=  msg_pertanian

			if self.export_to =="pdf":
				msg_sql=  msg_summary
  
			data = pandas.io.sql.read_sql(msg_sql,conn)
			listfinal.append(data)

 

		df = pd.concat(listfinal)


		if self.export_to =="xls":
			filename = filenamexls2 
			#report = df.groupby(["Group","AR Person"]).sum()
			df.to_excel(mpath + '/temp/'+ filenamexls2,index=False)

		if self.export_to =="hs":
			filename = filenamexls2 
			#report = df.groupby(["Group","AR Person"]).sum()
			df.to_excel(mpath + '/temp/'+ filenamexls2,index=False)

		if self.export_to =="xlswh":
			filename = filenamexls2 
			#report = df.groupby(["Group","AR Person"]).sum()
			df.to_excel(mpath + '/temp/'+ filenamexls2,index=False)
		if self.export_to =="json":
			filename = filenamexls2 
			#report = df.groupby(["Group","AR Person"]).sum()
			df.to_json(path_or_buf=mpath + '/temp/'+ filenamexls2,orient="records")
 
		if self.export_to =="pdf":
			filename = filenamepdf
			
			proyeksi = self.env["cnw.awr28.jasper"].search([("name","=","hppsummary")])
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

 