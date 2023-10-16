# -*- coding: utf-8 -*-
import requests 
import xlsxwriter
import numpy as np
import pandas as pd
import pandas.io.sql
import os
import pdfkit
import pytz
from odoo.exceptions import UserError
from odoo.modules import get_modules, get_module_path
from datetime import datetime
from odoo import models, fields, api
import base64
import pymssql
from jinja2 import Environment, FileSystemLoader

class CNW_generalledgerREPORT(models.TransientModel):
	_name           = "cnw.awr28.generalledger"
	_description    = "cnw.awr28.generalledger"
	company_id      = fields.Many2many('res.company', string="Company",required=True)
	
	datefrom        = fields.Date ("Date From", default=fields.Date.today())
	dateto          = fields.Date ("Date To", default=fields.Date.today()) 
	account         = fields.Char ("Account No") 
	export_to       = fields.Selection([ ('xls', 'Excel'),('json','JSON Format'),('pdf', 'PDF'),],string='Export To', default='xls')
	filexls         = fields.Binary("File Output",default="-")    
	filenamexls     = fields.Char("File Name Output",default="test.txt")
	
	@api.multi
	def view_awr28_generalledger(self): 
		mpath       = get_module_path('cnw_awr28')
		filex 		=  'generalledger_'+   datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y_%m_%d_%H_%M_%S")
		filenamexls = 'generalledger_'+   datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y_%m_%d_%H_%M_%S")  + '.xlsx'
		filenamepdf = filex  + '.pdf'
		filenamejson = filex  + '.json'
		filename    =""
		filepath    = mpath + '/temp/'
		logo        = mpath + '/awr_template/logoigu.png'
		listfinal   = []
		cssfile     = mpath + '/awr_template/style.css'

		#global Var

		igu_title = "Jurnal Entry"
		igu_tanggal = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")
		igu_remarks = "Jurnal Entry "
		options = {
					'page-size': 'A4',
					'orientation': 'portrait',
					}

		for comp in self.company_id:
			host        = comp.server
			database    = comp.db_name
			user        = comp.db_usr
			password    = comp.db_pass 
			
			#conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';UID='+user+';PWD='+ password + ';TrustServerCertificate=yes')
			conn = pymssql.connect(host=host, user=user, password=password, database=database)
			account = self.account if self.account else ""
			msg_sql= "exec IGU_ACCT_GENERALLEDGER   '"+ self.datefrom.strftime("%Y%m%d")   + "','" + self.dateto.strftime("%Y%m%d")  + "','"+ account + "','" + comp.code_base + "'"
			msg_sql = """
							declare 
									@datefrom varchar(10) ,
									@dateto varchar(10) ,
									@account varchar(10) ,
									@company varchar(50)
							set @datefrom = '""" +  self.datefrom.strftime("%Y%m%d")  + """'
							set @dateto = '"""+  self.dateto.strftime("%Y%m%d")  +"""'
							SET NOCOUNT ON
							set @account = '""" + account + """'
							set @company = '""" + comp.name  + """'

							declare @table table (  idx int identity(1,1) ,
													company_id varchar(100) ,
													account varchar(100) ,
													docdate varchar(10) ,
													transno varchar(100) ,
													ref1 varchar(100) ,
													linememo varchar(200) ,
													debit numeric(19,2) ,
													credit numeric(19,2) ,
													balance numeric(19,2)
												)
							insert into @table 
							select @company company,* from 
							(
							select  
									a.account + ' - ' + c.acctname account, 
									left(@datefrom,4) +'-' + substring(@datefrom,5,2) + '-' + right(@datefrom,2)  refdate, 
									'000000' transnum ,
									'Opening' U_Trans_No ,
									' Opening' LineMemo ,
									0 DEBIT ,
									0 CREDIT  ,
									sum(a.debit - a.credit) AMOUNT
							from JDT1 A 
								INNER JOIN OJDT B ON A.transid = b.transid 
								inner join OACT C ON A.ACCOUNT = C.ACCTCODE 
								LEFT OUTER JOIN OCRD d on a.U_IGU_BPID = d.cardcode
								LEFT OUTER JOIN OPRC e on a.ProfitCode= e.PrcCode
								LEFT OUTER JOIN OPRC f on a.OcrCode2= f.PrcCode

							WHERE a.account like @account +'%'
							AND LEFT(CONVERT(VARCHAR,A.REFDATE ,112) ,8) < @datefrom  
							group by a.account + ' - ' + c.acctname

							UNION ALL
							select  
									a.account + ' - ' + c.acctname account, 
									convert(Varchar,a.refdate,23) refdate, 
									B.NUMBER transnum ,
									CASE WHEN ISNULL(b.U_Trans_No,'')='' THEN CONVERT(VARCHAR,B.REF1) ELSE  ISNULL(b.U_Trans_No,'') END   ,
									a.LineMemo ,
									isnull(a.debit,0)  DEBIT ,
									isnull(A.credit,0) CREDIT  ,
									isnull(a.debit - a.credit,0) AMOUNT
							from JDT1 A 
								INNER JOIN OJDT B ON A.transid = b.transid 
								inner join OACT C ON A.ACCOUNT = C.ACCTCODE 
								LEFT OUTER JOIN OCRD d on a.U_IGU_BPID = d.cardcode
								LEFT OUTER JOIN OPRC e on a.ProfitCode= e.PrcCode
								LEFT OUTER JOIN OPRC f on a.OcrCode2= f.PrcCode

							WHERE a.account like @account +'%'
							AND LEFT(CONVERT(VARCHAR,A.REFDATE ,112) ,8) between @datefrom and @dateto
							)as a 
							order by account ,refdate ,transnum
							

							DECLARE @ROWCOUNT INT , @ROWMAX INT ,@BALANCE NUMERIC(19,2)

							SET @ROWCOUNT = 1
							SELECT  @ROWMAX = COUNT(*) FROM @TABLE 
							SET @BALANCE =0
							WHILE @ROWCOUNT <= @ROWMAX 
							BEGIN
									SELECT @BALANCE = BALANCE FROM @TABLE WHERE IDX = @ROWCOUNT
									SET @ROWCOUNT = @ROWCOUNT + 1
									UPDATE @TABLE SET   BALANCE = @BALANCE + BALANCE FROM @TABLE WHERE IDX = @ROWCOUNT
									
							END 


							SELECT * FROM @TABLE ORDER BY IDX            
			"""

			data = pandas.io.sql.read_sql(msg_sql,conn)
			listfinal.append(data)

		df = pd.concat(listfinal)

		#doharian = df.pivot_table(index=["account"],columns=["imonth"],aggfunc=np.sum,  values=["amount"],fill_value="0",margins=True )
		



		
		if self.export_to =="xls":
			filename = filenamexls 
			#df["Balance"] = df.groupby(["account"])["AMOUNT"].cumsum()
			df.to_excel(mpath + '/temp/'+ filenamexls)  
		elif self.export_to =="json":
			filename = filenamejson 
			#df["Balance"] = df.groupby(["account"])["AMOUNT"].cumsum()
			df.to_json(mpath + '/temp/'+ filenamejson, orient="records")  
		else:
			filename = filenamepdf
			
			proyeksi = self.env["cnw.awr28.jasper"].search([("name","=","generaledger")])
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

 