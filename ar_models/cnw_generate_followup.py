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
import pyodbc
import psycopg2 as pg
from jinja2 import Environment, FileSystemLoader
import pdfkit

class CNWCustomerFollowupWizard(models.TransientModel):
	_name           = "cnw.cflwup.followup.report"
	_description    = "cnw.cflwup.followup.report"
	company_id      = fields.Many2many('res.company', string="Company",required=True) 
	filexls         = fields.Binary("File Output")    
	filenamexls     = fields.Char("File Name Output")
	
	export_to       = fields.Selection([ ('xls', 'Excel'),('pdf', 'PDF'),],string='Export To', default='pdf')
 
	def generate_report(self): 
#PATH & FILE NAME & FOLDER
		mpath       = get_module_path('cnw_invar')
		filenamexls2    = 'followup_' + '.xlsx'
		filenamepdf    = 'followup_'+   '.pdf'
		filepath    = mpath + '/temp/'+ filenamexls2

#LOGO CSS AND TITLE
		logo        = mpath + '/template/logoigu.png'  
		cssfile     = mpath + '/template/style.css'        
		options = {
					'page-size': 'legal',
					'orientation': 'landscape',
					}
		igu_title = "Follow Up Customer"
		igu_tanggal = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")
		igu_remarks = "Follow Up Customer"                    

#MULTI COMPANY 
		  
		#companyDB 	= self.env.user.company_id.db_name
		#UserName 	=  self.env.user.company_id.sapuser
		#Password 	=  self.env.user.company_id.sappassword

		host        = self.env.user.company_id.server
		database    = self.env.user.company_id.db_name
		user        = self.env.user.company_id.db_usr
		password    = self.env.user.company_id.db_pass


		host2        = "192.168.250.14"
		database2    = "igportal"
		user2        = "invoice"
		password2    = "invoice" 

		conn2 = pg.connect("host="+ host2 + " dbname="+  database2 + " user="+ user2 + " password="+ password2 + "")
			
		#conn = pymssql.connect(host=host, user=user, password=password, database=database)
		conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';UID='+user+';PWD='+ password + ';TrustServerCertificate=yes')
		if self.env.user.company_id.code_base =="igu23":
			msg_sql= """                
						select    
									c.cardcode  ,
									c.cardname 'Partner Name',
									d.groupname 'Group',
									c.U_AR_Person , 
									c.shiptodef outlet ,
									sum(case 
										when datediff(day,a.taxdate,getdate())<=30 and a.transtype in (13,14) then (a.BalScDeb -a.balsccred ) 
										else 0
									end) '0-30',  
									sum(case 
										when datediff(day,a.taxdate,getdate()) between 31 and 60  and a.transtype in (13,14)  then (a.BalScDeb -a.balsccred ) 
										else 0
									end) '31-60',  
									sum(case 
										when datediff(day,a.taxdate,getdate())  between 61 and 90  and a.transtype in (13,14)  then (a.BalScDeb -a.balsccred ) 
										else 0
									end) '61-90',  
									sum(case 
										when datediff(day,a.taxdate,getdate())  between 91 and 120    and a.transtype in (13,14)  then (a.BalScDeb -a.balsccred ) 
										else 0
									end) '91-120',  
									sum(case 
										when datediff(day,a.taxdate,getdate()) >=121 and year (a.taxdate) = 2023 and a.transtype in (13,14)  then (a.BalScDeb -a.balsccred ) 
										else 0
									end) '121+ 2023',  

									sum(case 
										when year (a.taxdate) = 2023 and a.transtype in (13,14)  then (a.BalScDeb -a.balsccred ) 
										else 0
									end) as 'total 2023',      
									sum(case 
										when year (a.taxdate) = 2022 and a.transtype in (13,14)  then (a.BalScDeb -a.balsccred ) 
										else 0
									end) as '2022',
									sum(case 
										when year (a.taxdate) = 2021 and a.transtype in (13,14)  then (a.BalScDeb -a.balsccred ) 
										else 0
									end) as '2021',                                
									sum(case 
										when year (a.taxdate) = 2020 and a.transtype in (13,14)  then (a.BalScDeb -a.balsccred ) 
										else 0
									end) as '2020',
									sum(case 
										when datediff(day,a.taxdate,getdate()) >=121 and year (a.taxdate) = 2019  and a.transtype in (13,14)  then (a.BalScDeb -a.balsccred ) 
										else 0
									end) '2019',
									sum(case 
										when datediff(day,a.taxdate,getdate()) >=121 and year (a.taxdate) = 2018  and a.transtype in (13,14)  then (a.BalScDeb -a.balsccred ) 
										else 0
									end) '2018',
									sum(case 
										when datediff(day,a.taxdate,getdate()) >=121 and year (a.taxdate) = 2017  and a.transtype in (13,14)  then (a.BalScDeb -a.balsccred ) 
										else 0
									end) '2017',
									sum(case 
										when datediff(day,a.taxdate,getdate()) >=121 and year (a.taxdate) = 2016  and a.transtype in (13,14)  then (a.BalScDeb -a.balsccred ) 
										else 0
									end) '2016',
									sum( case when a.transtype in (24,30,231) then (a.BalScDeb -a.balsccred ) else 0 end )'UnRec',
									sum(a.BalScDeb -a.balsccred ) 'Total'
									from jdt1 a 
									inner join ojdt b on a.transid = b.transid 
									inner join ocrd c on a.ShortName = c.cardcode 
									inner join ocrg d on d.groupcode = c.groupcode 
									where 
									a.account ='1130001' 
									and a.BalScDeb -a.balsccred  <>0 
									and convert(varchar,a.refdate,112)<= convert(varchar,getdate(),112)
									group by  
									c.cardcode ,
									d.groupname ,
									c.cardname , c.shiptodef ,
									c.U_AR_Person
						"""
		
		else :
			msg_sql= """                
						select    
								c.cardcode  ,
								c.cardname 'Partner Name',
								d.groupname 'Group',
								c.U_AR_Person , 
								c.shiptodef outlet ,
								sum(case 
									when datediff(day,a.refdate,getdate())<=30 and a.transtype in (13,14) then (a.BalScDeb -a.balsccred ) 
									else 0
								end) '0-30',  
								sum(case 
									when datediff(day,a.refdate,getdate()) between 31 and 60  and a.transtype in (13,14)  then (a.BalScDeb -a.balsccred ) 
									else 0
								end) '31-60',  
								sum(case 
									when datediff(day,a.refdate,getdate())  between 61 and 90  and a.transtype in (13,14)  then (a.BalScDeb -a.balsccred ) 
									else 0
								end) '61-90',  
								sum(case 
									when datediff(day,a.refdate,getdate())  between 91 and 120    and a.transtype in (13,14)  then (a.BalScDeb -a.balsccred ) 
									else 0
								end) '91-120',  
								sum(case 
									when datediff(day,a.refdate,getdate()) >=121 and year (a.refdate) = 2023 and a.transtype in (13,14)  then (a.BalScDeb -a.balsccred ) 
									else 0
								end) as '121+ 2023',  

								sum(case 
									when year (a.refdate) = 2022 and a.transtype in (13,14)  then (a.BalScDeb -a.balsccred ) 
									else 0
								end) as 'total 2022',
								sum(case 
									when year (a.refdate) = 2021 and a.transtype in (13,14)  then (a.BalScDeb -a.balsccred ) 
									else 0
								end) as '2021',                                
								sum(case 
									when year (a.refdate) = 2020 and a.transtype in (13,14)  then (a.BalScDeb -a.balsccred ) 
									else 0
								end) as '2020',
								sum(case 
									when datediff(day,a.refdate,getdate()) >=121 and year (a.refdate) = 2019  and a.transtype in (13,14)  then (a.BalScDeb -a.balsccred ) 
									else 0
								end) '2019',
								sum(case 
									when datediff(day,a.refdate,getdate()) >=121 and year (a.refdate) = 2018  and a.transtype in (13,14)  then (a.BalScDeb -a.balsccred ) 
									else 0
								end) '2018',
								sum(case 
									when datediff(day,a.refdate,getdate()) >=121 and year (a.refdate) = 2017  and a.transtype in (13,14)  then (a.BalScDeb -a.balsccred ) 
									else 0
								end) '2017',
								sum(case 
									when datediff(day,a.refdate,getdate()) >=121 and year (a.refdate) = 2016  and a.transtype in (13,14)  then (a.BalScDeb -a.balsccred ) 
									else 0
								end) '2016',
								sum( case when a.transtype in (24,30,231) then (a.BalScDeb -a.balsccred ) else 0 end )'UnRec',
								sum(a.BalScDeb -a.balsccred ) 'Total'
								from jdt1 a 
								inner join ojdt b on a.transid = b.transid 
								inner join ocrd c on a.ShortName = c.cardcode 
								inner join ocrg d on d.groupcode = c.groupcode 
								where 
								a.account ='1130001' 
								and a.BalScDeb -a.balsccred  <>0 
								and convert(varchar,a.refdate,112)<= convert(varchar,getdate(),112)
								group by  
								c.cardcode ,
								d.groupname ,
								c.cardname , c.shiptodef ,
								c.U_AR_Person
						"""

		pandas.options.display.float_format = '{:,.2f}'.format

		#msg_sql = """ exec [dbo].[IGU_AGING_AR] '20200531','IGU' """
		data = pandas.io.sql.read_sql(msg_sql,conn)
 

		msg_sql2= """
				select  
				    a.salesgroup as "Sales Group" ,  
				    a.salesperson as "Sales Person",
				    a.groupname as "Customer Group",
				    a.ar_person as "AR Person",
				    A.cardcode cardcode,
				    a.cardname   Customer, 
				    a.lock_limit , 
				    a.paymentGroup as "Term of Payment",
				    a.creditline as "Credit limit",
				    a.b60 as "Before 60days" ,
				    a.a60 as "After 60days",
				    a.balance "Balance",
				    (a.creditline - a.balance) as "Remain Credit" ,
				    a.followup_by ,
				    a.laststatus_date,
				    '[' || coalesce(a.followup_type,'') || '] ' || coalesce(a.laststatus ,'') status
				from sap_bp  A
				where a.company_id=""" + str(self.env.user.company_id.id) + """
				order by 
				    a.salesgroup ,  a.salesperson,
				    a.groupname ,  A.cardcode
					"""


		data2 = pandas.io.sql.read_sql(msg_sql2,conn2)
 
		pandas.options.display.float_format = '{:,.2f}'.format
  
  
		igu_tanggal = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")
  
		new_df = pandas.merge(data, data2, how = 'left', on=["cardcode"])
		#df = new_df[["cardcode","customer","outlet","Customer Group","Sales Group","Sales Person","AR Person","Term of Payment","Credit limit","0-30","31-60","61-90","91-120","121+ 2022","total 2022","2021" ,"2020","2019", "2018", "2017", "2016","UnRec", "Total","Remain Credit","followup_by","laststatus_date","status"]]
#		df = new_df[["Sales Group","Sales Person","AR Person","cardcode","customer","outlet","Customer Group","Term of Payment","Credit limit","0-30","31-60","61-90","91-120","121+ 2021","total 2021","2020" ,"2019", "2018", "2017", "2016","UnRec", "Total","Remain Credit","followup_by","laststatus_date","status"]]
		#df = new_df[["cardcode","customer","outlet","Customer Group","Sales Group","Sales Person","AR Person","Term of Payment","Credit limit","0-30","31-60","61-90","91-120","121+ 2022","total 2022","2021" ,"2020","2019", "2018", "2017", "2016","UnRec", "Total","Remain Credit","followup_by","laststatus_date","status"]]
		
		# df = new_df[["cardcode","customer","outlet","Customer Group","Sales Group","Sales Person","AR Person","Term of Payment","Credit limit","0-30","31-60","61-90","91-120","121+ 2023","total 2023","2022","2021" ,"2020","2019", "2018", "2017", "2016","UnRec", "Total","Remain Credit","followup_by","laststatus_date","status"]]
		#Menghilangkan 2016 dari view
		df = new_df[["cardcode","customer","outlet","Customer Group","Sales Group","Sales Person","AR Person","Term of Payment","Credit limit","0-30","31-60","61-90","91-120","121+ 2023","total 2023","2022","2021" ,"2020","2019", "2018", "2017","UnRec", "Total","Remain Credit","followup_by","laststatus_date","status"]]
		df.rename(columns={"121+ 2023": "121+"},inplace=True)

		if self.export_to =="xls":
			filename = filenamexls2 
			#report = df.groupby(["Group","AR Person"]).sum()
			#newdf2 = new_df[["salesgroup","salesperson","salesemail","AR Person","cardcode","Partner Name","Customer Group","Payment","Credit Limit","0-30","31-60","61-90","91-120","121+","Total","Remain Credit","followup_by","laststatus_date","status"]].sort_values(["salesgroup","salesperson"])
			df.to_excel(mpath + '/temp/'+ filename ,engine="xlsxwriter",index=False)
		else:
				   
			filename = filenamepdf
			env = Environment(loader=FileSystemLoader(mpath + '/template/'))
			template = env.get_template("cnw_followup_report.html")            
			data3 = new_df[["Sales Group","Sales Person","AR Person","cardcode","customer","Customer Group","Term of Payment","Credit limit","0-30","31-60","61-90","91-120","121+ 2022","total 2022","Remain Credit","followup_by","laststatus_date","status"]]
			template_var = {"logo":logo, 
							"igu_title" :igu_title,
							"igu_header1" : "Laporan Follow Up Customer",
							"igu_header2" : "Laporan Follow Up Customer",
							"igu_tanggal" :igu_tanggal ,  
							"detail": data3.to_html(float_format='{:20,.2f}'.format),}
			
			html_out = template.render(template_var)
			pdfkit.from_string(html_out,mpath + '/temp/'+ filenamepdf,options=options,css=cssfile) 
	 
		
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

 