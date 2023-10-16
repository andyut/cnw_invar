# -*- coding: utf-8 -*-
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
#import pyodbc
import pymssql
from jinja2 import Environment, FileSystemLoader
import pdfkit


class AWR_BL(models.TransientModel):
	_name           = "cnw.awr28.bl"
	_description    = "cnw.awr28.bl"
	company_id      = fields.Many2many('res.company', string="Company",required=True)
	dateto          = fields.Date ("Date To", default=fields.Date.today()) 
	export_to       = fields.Selection([ ('xls', 'Excel'),
											('pdf', 'PDF'),
											('xlsmonthly', 'BL XLS Monthly'),
											('xlsmonthly4', 'BL XLS Monthly Lvl 4'),
											('xls2', 'Summary Level 4 '),
											('xls3', 'Summary (Level 7) '),
											],string='Export To', default='pdf')
	filexls         = fields.Binary("File Output")    
	filenamexls     = fields.Char("File Name Output")
	
	
	
	def view_pl(self): 
		mpath       = get_module_path('cnw_awr28')
		filename    = 'BL_'+ self.env.user.company_id.db_name +  self.dateto.strftime("%Y%m%d")  + '.xlsx'
		filenamexls    = 'BL_'+ self.env.user.company_id.db_name +   self.dateto.strftime("%Y%m%d")  + '.xlsx'
		filenamexls2    = 'BL_'+  self.env.user.company_id.db_name +  self.dateto.strftime("%Y%m%d")  + '.xlsx'
		filenamepdf = 'BL_'+  self.env.user.company_id.db_name +  self.dateto.strftime("%Y%m%d")  + '.pdf'
		filepath    = mpath + '/temp/'+ filename
		logo        = mpath + '/awr_template/logoigu.png' 
		listfinal   = []
		options = {
					'orientation': 'portrait',
					}        
		igu_tanggal = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")
		
		listcom = []
		for comp in self.company_id:

			host        = comp.server
			database    = comp.db_name
			user        = comp.db_usr
			password    = comp.db_pass 
			
			conn = pymssql.connect(host=host, user=user, password=password, database=database)
			#conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';UID='+user+';PWD='+ password + ';TrustServerCertificate=yes')

			listcom.append(comp.code_base)
			cursor = conn.cursor()
			if self.export_to == "xlsmonthly":
				msg_sql=  "exec [dbo].[IGU_ACT_BL2] '" +  self.dateto.strftime("%Y%m%d") + "','"+ comp.code_base + "' "
			elif self.export_to == "xlsmonthly4":

				msg_sql=  "exec [dbo].[IGU_ACT_BL3] '" +  self.dateto.strftime("%Y%m%d") + "','"+ comp.code_base + "' "
			else :
				msg_sql=  "exec [dbo].[IGU_ACT_BL] '" +  self.dateto.strftime("%Y%m%d") + "','"+ comp.code_base + "' "

			data = pandas.io.sql.read_sql(msg_sql,conn)
			listfinal.append(data)

 

		df = pd.concat(listfinal)
		dflist = df.values.tolist() 

		if self.export_to =="xls":
			filename = filenamexls2 
			#report = df.groupby(["Group","AR Person"]).sum()
			df.to_excel(mpath + '/temp/'+ filenamexls2,index=False)

		if self.export_to =="xlsmonthly":
			filename = filenamexls2 
			#report = df.groupby(["Group","AR Person"]).sum()
			
			#writer = pd.ExcelWriter(mpath + '/temp/'+ filenamexls2,engine="xlsxwriter")
			workbook = xlsxwriter.Workbook(mpath + '/temp/'+ filenamexls2)

			money_format = workbook.add_format({'num_format': '#,##0.00',
													'font_size':8,
													'font_name':'Arial'}) 

			moneyb_format = workbook.add_format({   'bold': True, 
													'num_format': '#,##0.00',
													'font_size':10, 
													'font_name':'Arial'}) 
			moneyc_format = workbook.add_format({   'bold': True, 
													'num_format': '#,##0.00',
													'font_size':10, 
													'border':True,
													'font_name':'Arial'}) 
			header_format = workbook.add_format({'bold': True, 
												'valign': 'top',
												'align': 'right',
												'font_size':16, 
												'font_name':'Arial',})        
			header_format2 = workbook.add_format({'bold': True, 
												'valign': 'top',
												'align': 'center',
												'font_size':12, 
												'border':True,
												'font_name':'Arial',})                   
			
			for line in listcom:
				worksheet = workbook.add_worksheet(line)

				comdata = df[df.company==line]
				line=0 

				worksheet.set_column(1,2,10) 
				worksheet.set_column(3,3,40)
				worksheet.set_column(4,4,10)
				worksheet.set_column(5,5,40)
				worksheet.set_column(6,17,20)

				worksheet.write (2,1 ,"Company",header_format2)
				worksheet.write (2,2 ,"Header",header_format2)
				worksheet.write (2,3 ,"Title",header_format2)
				worksheet.write (2,4 ,"Account",header_format2)
				worksheet.write (2,5 ,"Subtitle",header_format2)
				worksheet.write (2,6 ,"Jan",header_format2)
				worksheet.write (2,7 ,"Feb",header_format2)
				worksheet.write (2,8 ,"Mar",header_format2)
				worksheet.write (2,9 ,"Apr",header_format2)
				worksheet.write (2,10 ,"Mei",header_format2)
				worksheet.write (2,11,"Jun",header_format2)
				worksheet.write (2,12,"Jul",header_format2)
				worksheet.write (2,13,"Ags",header_format2)
				worksheet.write (2,14,"Sep",header_format2)
				worksheet.write (2,15 ,"Okt",header_format2)
				worksheet.write (2,16,"Nov",header_format2)
				worksheet.write (2,17,"Des",header_format2)                 

				for ln in comdata.values.tolist(): 
					if ln[4]=='9999001':

						worksheet.write(3+line,1, ln[0],moneyb_format)
						worksheet.write(3+line,2, ln[2],moneyb_format)
						worksheet.write(3+line,3, ln[3],moneyb_format)
						worksheet.write(3+line,4, ln[4],moneyb_format)
						worksheet.write(3+line,5, ln[5],moneyb_format)
						worksheet.write(3+line,6, ln[6],moneyb_format)
						worksheet.write(3+line,7, ln[7],moneyb_format)
						worksheet.write(3+line,8 ,ln[8],moneyb_format)
						worksheet.write(3+line,9, ln[9],moneyb_format)
						worksheet.write(3+line,10, ln[10],moneyb_format)
						worksheet.write(3+line,11, ln[11],moneyb_format)
						worksheet.write(3+line,12, ln[12],moneyb_format)
						worksheet.write(3+line,13, ln[13],moneyb_format)
						worksheet.write(3+line,14, ln[14],moneyb_format)
						worksheet.write(3+line,15, ln[15],moneyb_format)
						worksheet.write(3+line,16, ln[16],moneyb_format)
						worksheet.write(3+line,17, ln[17],moneyb_format)  
					elif  ln[4]=='9999002':
						worksheet.write(3+line,1, ln[0],moneyc_format)
						worksheet.write(3+line,2, ln[2],moneyc_format)
						worksheet.write(3+line,3, ln[3],moneyc_format)
						worksheet.write(3+line,4, ln[4],moneyc_format)
						worksheet.write(3+line,5, ln[5],moneyc_format)
						worksheet.write(3+line,6, ln[6],moneyc_format)
						worksheet.write(3+line,7, ln[7],moneyc_format)
						worksheet.write(3+line,8 ,ln[8],moneyc_format)
						worksheet.write(3+line,9, ln[9],moneyc_format)
						worksheet.write(3+line,10, ln[10],moneyc_format)
						worksheet.write(3+line,11, ln[11],moneyc_format)
						worksheet.write(3+line,12, ln[12],moneyc_format)
						worksheet.write(3+line,13, ln[13],moneyc_format)
						worksheet.write(3+line,14, ln[14],moneyc_format)
						worksheet.write(3+line,15, ln[15],moneyc_format)
						worksheet.write(3+line,16, ln[16],moneyc_format)
						worksheet.write(3+line,17, ln[17],moneyc_format)              
					else:
						worksheet.write(3+line,1, ln[0])
						worksheet.write(3+line,2, ln[2])
						worksheet.write(3+line,3, ln[3])
						worksheet.write(3+line,4, ln[4])
						worksheet.write(3+line,5, ln[5])
						worksheet.write(3+line,6, ln[6])
						worksheet.write(3+line,7, ln[7])
						worksheet.write(3+line,8 ,ln[8])
						worksheet.write(3+line,9, ln[9])
						worksheet.write(3+line,10, ln[10])
						worksheet.write(3+line,11, ln[11])
						worksheet.write(3+line,12, ln[12])
						worksheet.write(3+line,13, ln[13])
						worksheet.write(3+line,14, ln[14])
						worksheet.write(3+line,15, ln[15])
						worksheet.write(3+line,16, ln[16])
						worksheet.write(3+line,17, ln[17])            
					line+=1

			workbook.close()
			
		if self.export_to =="xlsmonthly4":
			filename = filenamexls2 
			#report = df.groupby(["Group","AR Person"]).sum()
			df.to_excel(mpath + '/temp/'+ filenamexls2,index=False)

		if self.export_to =="xls2":
			filename = filenamexls2 
			#report = df.groupby(["Group","AR Person"]).sum()
			pvt = df[df.account =="9999001"].pivot_table(index=["subtitle"],columns=["company"],aggfunc=np.sum,  values=["amount"],fill_value="0",margins=True )
			pvt.to_excel(mpath + '/temp/'+ filenamexls2)


		if self.export_to =="xls3":
			filename = filenamexls2 
			#report = df.groupby(["Group","AR Person"]).sum()
			pvt = df[(df.amount  != 0) & (df.account  != "9999001") & (df.account  != "9999002" ) ].pivot_table(index=["subtitle"],columns=["company"],aggfunc=np.sum,  values=["amount"],fill_value="0",margins=True )
			pvt.to_excel(mpath + '/temp/'+ filenamexls2)

		if self.export_to =="pdf":
			filename = filenamepdf
			
			env = Environment(loader=FileSystemLoader(mpath + '/template/'))
			template = env.get_template("bl_template.html")            
			template_var = {"company":self.env.user.company_id.name,
							"igu_title" :"Balance Sheet",
							"datetime" :igu_tanggal ,
							"dateto" :self.dateto.strftime("%Y-%m-%d") ,
							"igu_remarks" :"Balance Sheet" ,
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

 