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
import pymssql
from jinja2 import Environment, FileSystemLoader
import pdfkit


class AWR_InterCompAP(models.TransientModel):
	_name           = "cnw.intercomp.ap"
	_description    = "cnw.intercomp.ap"
	company_id      = fields.Many2many('res.company', string="Company",required=True)
	dateto          = fields.Date ("Date To", default=fields.Date.today()) 
	export_to       = fields.Selection([ ('xls', 'Excel Per Sheet (Monthly)') ,
											('xls2','Excel Summary'), 
											],string='Export To', default='xls')
	filexls         = fields.Binary("File Output")    
	filenamexls     = fields.Char("File Name Output")
	
	
	
	def view_intercomp(self): 
		mpath       = get_module_path('cnw_awr28')
		filename    = 'INTERCOMP_AP'+ self.env.user.company_id.db_name +  self.dateto.strftime("%Y%m%d")  + '.xlsx'
		filenamexls    = 'INTERCOMP_AP'+ self.env.user.company_id.db_name +   self.dateto.strftime("%Y%m%d")  + '.xlsx'
		filenamexls2    = 'INTERCOMP_AP'+  self.env.user.company_id.db_name +  self.dateto.strftime("%Y%m%d")  + '.xlsx'
		filenamepdf = 'INTERCOMP_AP'+  self.env.user.company_id.db_name +  self.dateto.strftime("%Y%m%d")  + '.pdf'
		filepath    = mpath + '/temp/'+ filename
		logo        = mpath + '/awr_template/logoigu.png' 
		listfinal   = []
		options = {
					'orientation': 'portrait',
					}        
		igu_tanggal = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")
		
		listcom = []
		listintercomp = ""
		sqlinject = ""
		intercomp1 = self.env["cnw.intercomp.setting"].search([])
		i=0
		for ln in intercomp1:
			 
			if i==0 :
				listintercomp = listintercomp + "'" + ln["npwp"]+ "'"  
			else :
				listintercomp = listintercomp +  ",'" + ln["npwp"] + "'"
			
			sqlinject += "\n insert into @table values('" + ln["npwp"] + "','" + ln["codename"] + "','" + ln["company"] + "') \n"
			i+=1


		imax = 0 

		for comp in self.company_id:
			imax +=1
			host        = comp.server
			database    = comp.db_name
			user        = comp.db_usr
			password    = comp.db_pass 
			
			conn = pymssql.connect(host=host, user=user, password=password, database=database)
			#conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';UID='+user+';PWD='+ password + ';TrustServerCertificate=yes')

			listcom.append(comp.code_base)
			
			msg_sql=  """
							declare @dateto varchar(10)

							declare @table table ( npwp varchar(50) , codename varchar(50), company varchar(100))

							""" + sqlinject + """

							set @dateto = '""" +  self.dateto.strftime("%Y%m%d") + """'
							select   '""" + comp.code_base + """' company,
							c.company cardname, 
											sum(case when left(convert(varchar,a.refdate,112),6) <= left(@dateto ,4) + '01' and left(@dateto ,4)+'01' <= left(@dateto ,6) then (a.debit - a.credit ) else 0 end )jan,
											sum(case when left(convert(varchar,a.refdate,112),6) <= left(@dateto ,4) + '02' and left(@dateto ,4)+'02' <= left(@dateto ,6)  then (a.debit - a.credit ) else 0 end )feb,
											sum(case when left(convert(varchar,a.refdate,112),6) <= left(@dateto ,4) + '03' and left(@dateto ,4)+'03' <= left(@dateto ,6)  then (a.debit - a.credit ) else 0 end )mar,
											sum(case when left(convert(varchar,a.refdate,112),6) <= left(@dateto ,4) + '04' and left(@dateto ,4)+'04' <= left(@dateto ,6)  then (a.debit - a.credit ) else 0 end )apr,
											sum(case when left(convert(varchar,a.refdate,112),6) <= left(@dateto ,4) + '05' and left(@dateto ,4)+'05' <= left(@dateto ,6)  then (a.debit - a.credit ) else 0 end )may,
											sum(case when left(convert(varchar,a.refdate,112),6) <= left(@dateto ,4) + '06' and left(@dateto ,4)+'06' <= left(@dateto ,6)  then (a.debit - a.credit ) else 0 end )jun,
											sum(case when left(convert(varchar,a.refdate,112),6) <= left(@dateto ,4) + '07' and left(@dateto ,4)+'07' <= left(@dateto ,6)  then (a.debit - a.credit )else 0 end )jul,
											sum(case when left(convert(varchar,a.refdate,112),6) <= left(@dateto ,4) + '08' and left(@dateto ,4)+'08' <= left(@dateto ,6)  then (a.debit - a.credit ) else 0 end )ags,
											sum(case when left(convert(varchar,a.refdate,112),6) <= left(@dateto ,4) + '09' and left(@dateto ,4)+'09' <= left(@dateto ,6)  then (a.debit - a.credit ) else 0 end )sep,
											sum(case when left(convert(varchar,a.refdate,112),6) <= left(@dateto ,4) + '10' and left(@dateto ,4)+'10' <= left(@dateto ,6)  then (a.debit - a.credit ) else 0 end )okt,
											sum(case when left(convert(varchar,a.refdate,112),6) <= left(@dateto ,4) + '11' and left(@dateto ,4)+'11' <= left(@dateto ,6)  then (a.debit - a.credit ) else 0 end )nov,
											sum(case when left(convert(varchar,a.refdate,112),6) <= left(@dateto ,4) + '12' and left(@dateto ,4)+'12' <= left(@dateto ,6)  then (a.debit - a.credit ) else 0 end )des,
							sum(a.debit - a.credit )total from JDT1 A 
								inner join OCRD B ON A.shortname = b.cardcode
								inner join @table C ON b.lictradnum = c.npwp
								WHERE CONVERT(VARCHAR,A.REFDATE,112)<=  @dateto
								AND A.Account ='2110001'
								and b.lictradnum in (""" + listintercomp + """ )
							group by c.company               
			"""
			#print(msg_sql)
			data = pandas.io.sql.read_sql(msg_sql,conn)
			listfinal.append(data)

 

		df = pd.concat(listfinal)
		#dflist = df.values.tolist() 

		workbook = xlsxwriter.Workbook(mpath + '/temp/'+ filenamexls2)

		money_format = workbook.add_format({'num_format': '#,##0.00',
												'font_size':10,
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
											'font_size':10, 
											'border':True,
											'font_name':'Arial',})           
		header_format3 = workbook.add_format({'bold': True, 
											'valign': 'top',
											'align': 'right',
											'font_size':14, 
											'border':False,
											'font_name':'Arial',})          

		if self.export_to =="xls":
			filename = filenamexls2 
			#report = df.groupby(["Group","AR Person"]).sum()
			
			#writer = pd.ExcelWriter(mpath + '/temp/'+ filenamexls2,engine="xlsxwriter")
													  
			
			for line in listcom:
				worksheet = workbook.add_worksheet(line)

				comdata = df[df.company==line]
				line=0 

				worksheet.set_column(0,0,30)
				worksheet.set_column(1,13,15)

				worksheet.write (1,13 ,"Hutang Dagang",header_format3)

				worksheet.write (2,0 ,"Partner",header_format2)
				worksheet.write (2,1 ,"Jan",header_format2)
				worksheet.write (2,2 ,"Feb",header_format2)
				worksheet.write (2,3 ,"Mar",header_format2)
				worksheet.write (2,4 ,"Apr",header_format2)
				worksheet.write (2,5 ,"Mei",header_format2)
				worksheet.write (2,6,"Jun",header_format2)
				worksheet.write (2,7,"Jul",header_format2)
				worksheet.write (2,8,"Ags",header_format2)
				worksheet.write (2,9,"Sep",header_format2)
				worksheet.write (2,10 ,"Okt",header_format2)
				worksheet.write (2,11,"Nov",header_format2)
				worksheet.write (2,12,"Des",header_format2)    
				worksheet.write (2,13,"Total",header_format2)                 

				for ln in comdata.values.tolist(): 

					worksheet.write(3+line,0, ln[1],money_format)
					worksheet.write(3+line,1, ln[2],money_format)
					worksheet.write(3+line,2, ln[3],money_format)
					worksheet.write(3+line,3, ln[4],money_format)
					worksheet.write(3+line,4, ln[5],money_format)
					worksheet.write(3+line,5, ln[6],money_format)
					worksheet.write(3+line,6, ln[7],money_format)
					worksheet.write(3+line,7 ,ln[8],money_format)
					worksheet.write(3+line,8, ln[9],money_format)
					worksheet.write(3+line,9, ln[10],money_format)
					worksheet.write(3+line,10, ln[11],money_format)
					worksheet.write(3+line,11, ln[12],money_format)
					worksheet.write(3+line,12, ln[13],money_format)
					worksheet.write(3+line,13, ln[14],money_format)            
					line+=1
		workbook.close()
		if self.export_to =="xls2":
			filename = filenamexls2 
			#report = df.groupby(["Group","AR Person"]).sum()
			
			#writer = pd.ExcelWriter(mpath + '/temp/'+ filenamexls2,engine="xlsxwriter")
			 
			df.pivot_table(index=("cardname"),columns=("company"),aggfunc=np.sum,  values=["total"],fill_value="0",margins=True).to_csv(mpath + '/temp/'+ filenamexls2 ,float_format='%.2f', decimal=".",sep="\t")



		
		
		##workbook.close()
			 
			 
			   
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

 