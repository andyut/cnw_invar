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


class CNW_HPPSUMMARY2(models.TransientModel):
	_name           = "cnw.awr28.hppsummary02"
	_description    = "cnw.hppsummary02"
	company_id      = fields.Many2many('res.company', string="Company",required=True)
	dateto          = fields.Date ("Date To", default=fields.Date.today()) 
	items           = fields.Char("Items")
	igroup          = fields.Char("Item Group")
	
	export_to       = fields.Selection([ ('xls', 'Excel'),
											('hs01', 'HS  Summary'),
											('hs02', 'HS  Detail'),
											('xlswh', 'XLS Per Warehouse'),
											('pdf', 'PDF'),],string='Export To', default='xls')
	filexls         = fields.Binary("File Output")    
	filenamexls     = fields.Char("File Name Output")
	
	
	@api.multi
	def view_hppsummary(self): 
		mpath       = get_module_path('cnw_awr28')
		filename    = 'SaldoAkhirPersediaan_'+   self.dateto.strftime("%Y%m%d")  + '.xlsx'
		filenamexls    = 'SaldoAkhirPersediaan_'+   self.dateto.strftime("%Y%m%d")  + '.xlsx'
		filenamexls2    = 'SaldoAkhirPersediaan_'+   self.dateto.strftime("%Y%m%d")  + '.xlsx'
		filenamepdf = 'SaldoAkhirPersediaan_'+   self.dateto.strftime("%Y%m%d")  + '.pdf'
		filepath    = mpath + '/temp/'+ filename
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
			#cursor = conn.cursor()
			if self.export_to =="xlswh":
				msg_sql=  "exec [dbo].[IGU_HPPSUMMARY2] '" +  self.dateto.strftime("%Y%m%d") + "',' ','"+ comp.code_base + "' "

			if self.export_to =="xls":
				msg_sql=  "exec [dbo].[IGU_HPPSUMMARY] '" +  self.dateto.strftime("%Y%m%d") + "',' ','"+ comp.code_base + "' "

			if self.export_to =="pdf":
				msg_sql=  "exec [dbo].[IGU_HPPSUMMARY] '" +  self.dateto.strftime("%Y%m%d") + "',' ','"+ comp.code_base + "' "

			if self.export_to =="hs01":
				msg_sql=  """
								declare 
									@dateto varchar(10) ,
									@item varchar(50) ,
									@company varchar(10) ,
									@group varchar(50)

								set @dateto = '""" +  self.dateto.strftime("%Y%m%d") + """'
								set @item = '""" +  items + """'
								set @company = '""" +   comp.code_base  + """'
								set @group = '""" +  igroup + """'
								select 
										@company company,
										ISNULL(CONVERT(VARCHAR,b.u_hs_code),'')  , 
										b.U_SPEGROUP ,
										sum(inqty-outqty) qty,
										sum(transvalue) amount,
										upper(b.invntryUom) UOM 
								from OINM A (nolock)
									inner join OITM b (nolock) on a.itemcode = b.itemcode 
								where   
								CONVERT( VARCHAR,a.DOCDATE ,112) <= @dateto 
								and b.itemcode + b.itemname + isnull(b.u_group,'') like '%' + isnull(@item,'') + '%'  -- and a.TransValue<>0
								and b.u_group like '%' +  isnull(@group,'') + '%'
								group by 
										   ISNULL(CONVERT(VARCHAR,b.u_hs_code),'')  , 
											b.U_SPEGROUP ,
										upper(b.invntryUom)   
								having  sum(a.transvalue) <>0
								order by ISNULL(CONVERT(VARCHAR,b.u_hs_code),'') , 
										b.U_SPEGROUP 
							"""
			if self.export_to =="hs02":
				msg_sql=  	"""	declare 
									@dateto varchar(10) ,
									@item varchar(50) ,
									@company varchar(10) ,
									@group varchar(50)

								set @dateto = '""" +  self.dateto.strftime("%Y%m%d") + """'
								set @item = '""" +  items + """'
								set @company = '""" +   comp.code_base  + """'
								set @group = '""" +  igroup + """'
								select 
										@company company,
									   ISNULL(CONVERT(VARCHAR,b.u_hs_code),'') hscode , 
										b.U_SPEGROUP ,
										b.u_group ,
										b.u_subGroup ,
										b.u_Spec,
										sum(inqty-outqty) qty,
										sum(transvalue) amount,
										upper(b.invntryUom) UOM 
								from OINM A (nolock)
									inner join OITM b (nolock) on a.itemcode = b.itemcode 
								where   
								CONVERT( VARCHAR,a.DOCDATE ,112) <= @dateto 
								and b.itemcode + b.itemname + isnull(b.u_group,'') like '%' + isnull(@item,'') + '%'  -- and a.TransValue<>0
								and b.u_group like '%' + isnull(@group,'') + '%'
								group by 
										ISNULL(CONVERT(VARCHAR,b.u_hs_code),'')  , 
										b.U_SPEGROUP ,
										b.u_group ,
										b.u_subGroup ,
										b.u_Spec,
										upper(b.invntryUom)   
								having  sum(a.transvalue) <>0
								order by ISNULL(CONVERT(VARCHAR,b.u_hs_code),'') , 
										b.U_SPEGROUP ,
										b.u_group ,
										b.u_subGroup ,
										b.u_Spec 
								"""
			print(msg_sql)
			data = pandas.io.sql.read_sql(msg_sql,conn)
			listfinal.append(data)

 

		df = pd.concat(listfinal)


		if self.export_to =="xls":
			filename = filenamexls2 
			#report = df.groupby(["Group","AR Person"]).sum()
			df.to_excel(mpath + '/temp/'+ filenamexls2,index=False)

		if self.export_to =="xlswh":
			filename = filenamexls2 
			#report = df.groupby(["Group","AR Person"]).sum()
			df.to_excel(mpath + '/temp/'+ filenamexls2,index=False)

		if self.export_to =="hs01":
			filename = filenamexls2 
			#report = df.groupby(["Group","AR Person"]).sum()
			df.to_excel(mpath + '/temp/'+ filenamexls2,index=False)
		if self.export_to =="hs02":
			filename = filenamexls2 
			#report = df.groupby(["Group","AR Person"]).sum()
			df.to_excel(mpath + '/temp/'+ filenamexls2,index=False)
		if self.export_to =="pdf":
			filename = filenamepdf
			
			datalist = df.values.tolist()
			itotal = 0
			
			for dl in datalist:
				itotal += dl[7]

			env = Environment(loader=FileSystemLoader(mpath + '/template/'))
			template = env.get_template("saldo_akhir_persediaan.html")            
			template_var = {"company":self.env.user.company_id.name,
							"igu_title" :"Saldo Akhir Persediaan",
							"datetime" :igu_tanggal ,
							"dateto" :self.dateto.strftime("%Y-%m-%d") ,
							"igu_remarks" :"Saldo Akhir Persediaan" ,
							"data":datalist,
							"itotal":itotal}
			
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

 