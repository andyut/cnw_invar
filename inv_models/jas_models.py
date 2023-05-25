# -*- coding: utf-8 -*-

from odoo import models, fields, api
import base64
import os
import pytz
from datetime import datetime
import requests 
from odoo.exceptions import UserError
from odoo.modules import get_modules, get_module_path
import xlsxwriter
import numpy as np
import pandas as pd
import pandas.io.sql
import pyodbc  
from jinja2 import Environment, FileSystemLoader
import pdfkit

class JasLapAddresses(models.Model):
	_name 			= "jas.lap.mailaddress"
	_description 	= "JAS LAP MailAddresses"
	name 			= fields.Char("Name", required=True)
	mailaddress 	= fields.Char("Mail Address", required=True)
	remarks			= fields.Char("Remarks")

class LapKartuPiutangMdl2(models.Model):
	_name 			= "jas.lap.kartupiutangmdl2"
	_description 	= "Lap Kartu Piutang 2"
	name 			= fields.Text("Data Customer")
	cardcode 		= fields.Char("Partner Code")
	cardname 		= fields.Char("Partner Name")
	paymentterm		= fields.Char("Payment Term") 
	topdays			= fields.Integer("Payment Days")
	arperson 		= fields.Char("AR Person")
	salesperson		= fields.Char("Sales") 
	docdate 		= fields.Date("Doc Date")
	doctype 		= fields.Char("Doc Type")
	docnumber 		= fields.Char("Doc Number")
	refnumber 		= fields.Char("Ref Number")
	kwtnumber 		= fields.Char("Kwitansi")
	amount 			= fields.Float(string="Amount",digit=(19,6),default=0.0 )
	duedate 		= fields.Date("Due Date")

	diffdate 		= fields.Integer("DiffDocDate")
	diffduedate		= fields.Integer("DiffDueDate")

	paydate 		= fields.Date("Payment Date")
	paytotal 		= fields.Float(string="Payment Amount", digit=(19,6),default=0)
	#amount
	balance			= fields.Float(string="Balance",digit=(19,6),default=0.0 )



	maxdiff 		= fields.Float(string="max diff",digit=(19,6),default=0.0 )
	mindiff			= fields.Float(string="min diff",digit=(19,6),default=0.0 )
	avgdiff			= fields.Float(string="avg diff",digit=(19,6),default=0.0 )

class LapKartuPiutangMdl(models.Model):
	_name 			= "jas.lap.kartupiutangmdl"
	_description 	= "Lap Kartu Piutang "
	name 			= fields.Text("Data Customer")
	cardcode 		= fields.Char("Partner Code")
	cardname 		= fields.Char("Partner Name")
	docdate 		= fields.Date("Doc Date")
	doctype 		= fields.Char("Doc Type")
	docnumber 		= fields.Char("Doc Number")
	refnumber 		= fields.Char("Ref Number")
	kwtnumber 		= fields.Char("Kwitansi")
	
	#amount

	debit 			= fields.Float(string="Debit",digit=(19,6),default=0.0 )
	credit 			= fields.Float(string="Credit",digit=(19,6),default=0.0 )
	amount 			= fields.Float(string="Amount",digit=(19,6),default=0.0 )
	
	#extra

	trxdate 		= fields.Date("Trx Date")
	duedate 		= fields.Date("Due Date")
	diffdate 		= fields.Integer("DiffDocDate")
	diffduedate		= fields.Integer("DiffDueDate")
	paymentterm		= fields.Char("Payment Term") 
	topdays			= fields.Integer("Payment Days")
	arperson 		= fields.Char("AR Person")
	salesperson		= fields.Char("Sales")
	salesgroup		= fields.Char("Sales Group")


	maxdiff 		= fields.Float(string="max diff",digit=(19,6),default=0.0 )
	mindiff			= fields.Float(string="min diff",digit=(19,6),default=0.0 )
	avgdiff			= fields.Float(string="avg diff",digit=(19,6),default=0.0 )
	
	
class LapKartuPiutang(models.TransientModel):
	_name           = "jas.lap.kartupiutang"
	_description    = "Kartu Piutang"
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)

	datefrom        = fields.Date("Date From",default=lambda s:fields.Date.today())
	dateto          = fields.Date("Date To",default=lambda s:fields.Date.today())
	customer        = fields.Char("Business Partner",default="")
	arperson        = fields.Char("AR Person",default="")
	account         = fields.Selection(string="Account", selection=[
																	("1130001","1130001-PIUTANG DAGANG"),
																	("1135001","1135001-PIUTANG SEWA"),
																	("1135002","1135002-PIUTANG PENGIRIMAN BARANG"),
																	("1135003","1135003-PIUTANG PENITIPAN BARANG"),
																	("1135004","1135004-PIUTANG LAIN LAIN"),
																	("1135005","1135005-PIUTANG  HANDLING"),
																	("1137001","1137001-PIUTANG PPH23")],
																	default="1130001")

	export_to       = fields.Selection(string="Export to",selection=[("list","List View"),
																		("listsummary","List Summary View"),
																		("excelsummary","Excel Summary"),
																		("excel","Excel")],default="list")

	filexls         = fields.Binary("File Output")    
	filenamexls     = fields.Char("File Name Output")


	def get_kartupiutang(self):
#PATH & FILE NAME & FOLDER
		mpath       = get_module_path('cnw_invar')
		filenamexls2    = 'KartuPiutang_'+   self.dateto.strftime("%Y%m%d")  + '.xlsx'
		filenamepdf    = 'KartuPiutang_'+   self.dateto.strftime("%Y%m%d")  + '.pdf'
		filepath    = mpath + '/temp/'+ filenamexls2
 
#LOGO CSS AND TITLE
		logo        = mpath + '/template/logoigu.png' 
		cssfile     = mpath + '/template/style.css'        
		options = {
					'page-size': 'A4',
					'orientation': 'landscape',
					}
		igu_title = "Piutang Detail"
		igu_tanggal = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")
		igu_remarks = "Piutang Detail Per Tanggal " + self.dateto.strftime("%Y-%m-%d")                    

#MULTI COMPANY 

		listfinal = []
		pandas.options.display.float_format = '{:,.2f}'.format
		for comp in self.company_id:

			host        = comp.server
			database    = comp.db_name
			user        = comp.db_usr
			password    = comp.db_pass  
			conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';UID='+user+';PWD='+ password + ';TrustServerCertificate=yes')
			
			bp = self.customer if self.customer else ""
			arperson = self.arperson if self.arperson  else ""
			#bp = self.customer if self.customer else ""
			msgsql2 = """
						DECLARE @DateFrom 	varchar(10) ,
								@DateTo 	varchar(10),
								@cardcode 	varchar(50) ,
								@account 	varchar(10) ,
								@arperson 	varchar(50)
						SET NOCOUNT ON
						set     @DateFrom = '""" + self.datefrom.strftime("%Y-%m-%d")  + """'
						set     @DateTo   = '""" + self.dateto.strftime("%Y-%m-%d")  + """'
						set     @CardCode = '""" + bp + """'
						set     @account  = '""" + self.account + """'
						set     @arperson = '""" + arperson + """'

						declare @table table (  
												idx int identity(1,1) ,
												cardcode varchar(50), 
												cardname varchar(100),
												PymntGroup varchar(100) ,
												ExtraDays int ,
												arperson varchar(50) ,
												salesperson varchar(50),
												docdate varchar(10),
												doctype varchar(50) ,
												docnumber varchar(50) ,
												ref_number varchar(50),
												kwtno   varchar(50),
												debit numeric(19,6) ,
												credit numeric(19,6) ,
												amount numeric(19,6) ,
												trxdate varchar(10) ,
												duedate varchar(10) ,                       
												maxdiff numeric(19,2) ,
												mindiff numeric(19,2) ,
												avgdiff numeric(19,2) 
												)
						declare @table2 table ( 
												doctype varchar(10),
												docnum varchar(50),
												paytotal numeric(19,6),
												diffdate  numeric(19,2)  ,
												diffduedate  numeric(19,2)  ,
												paydate varchar(50)) 


						-- |Card Name | DocDate | Type | Doc No. | SO | Debet | Credit | Amount
						insert into @table 
						select  c.CardCode ,
								'[' + C.CardCode + '] ' + C.cardname ,
								d.PymntGroup ,
								d.ExtraDays , 
								c.U_AR_Person ,
								e.SlpName + '-' + upper(e.U_SlsEmpName),
								@datefrom , 
								'00-Opening Balance' ,
								'Opening Balance' ,
								'Opening Balance' ,
								'--',
								sum(B.Debit - B.credit) ,
								0 ,
								sum(B.Debit - B.credit) ,
								@datefrom  ,
								@datefrom ,
								0,
								0,
								0

						from OJDT A 
							INNER JOIN JDT1 B ON A.transID = b.TransID 
							INNER JOIN OCRD C ON B.ShortName = C.CARDCODE 
							INNER JOIN OCTG D ON C.GroupNum = d.GroupNum 
							INNER JOIN OSLP E ON C.SLPCODE  = E.SLPCODE 

						WHERE CONVERT(VARCHAR, A.REFDATE ,23) <=@DATEFROM 
						AND B.ACCOUNT = @account
						and (c.CardCode + c.cardname) 	  like '%' + @cardcode + '%' AND isnull(C.U_AR_Person,'') LIKE '%' + @arperson + '%')

						GROUP BY c.CardCode ,
								'[' + C.CardCode + '] ' + C.cardname ,
								d.PymntGroup ,
								d.ExtraDays , 
								c.U_AR_Person ,
								e.SlpName + '-' + upper(e.U_SlsEmpName)
						HAVING sum(B.Debit - B.credit) <>0

						UNION ALL

						SELECT  c.CardCode ,
								'[' + C.CardCode + '] ' + C.CardName ,
								d.PymntGroup ,
								d.ExtraDays , 
								c.U_AR_Person ,
								e.SlpName + '-' + upper(e.U_SlsEmpName),
								convert(varchar,a.docdate,23) docdate,
								'13-Invoice' ,
								convert(varchar,a.docnum) ,
								a.numatCard ,
								a.u_kw_no,
								a.doctotal ,
								0,
								a.doctotal,
								convert(varchar,a.docdate,23)   ,
								convert(varchar,a.docduedate,23)  ,
								0,
								0,
								0
						from oinv a 
							inner join ocrd c on a.cardcode = c.cardcode 
							INNER JOIN OCTG D ON C.GroupNum = d.GroupNum 
							INNER JOIN OSLP E ON C.SLPCODE  = E.SLPCODE 
						where convert(varchar,a.docdate,23) between @datefrom and @dateto
						and (c.CardCode + c.cardname  like '%' + @cardcode + '%' AND isnull(C.U_AR_Person,'') LIKE '%' + @arperson + '%')
						and a.canceled = 'N'
						and a.CtlAccount = @account
						UNION ALL

						SELECT  
								c.CardCode ,
								'[' + C.CardCode + '] ' + C.CardName ,
								d.PymntGroup ,
								d.ExtraDays , 
								c.U_AR_Person ,
								e.SlpName + '-' + upper(e.U_SlsEmpName),
								convert(varchar,a.docdate,23) docdate,
								'13-Invoice' ,
								convert(varchar,a.docnum) ,
								a.numatCard ,
								a.u_kw_no,
								0,
								a.doctotal ,
								-1 * a.doctotal,
								convert(varchar,a.docdate,23)   ,
								convert(varchar,a.docduedate,23)  ,
								0,
								0,
								0
						from orin a 
							inner join ocrd c on a.cardcode = c.cardcode 
							INNER JOIN OCTG D ON C.GroupNum = d.GroupNum 
							INNER JOIN OSLP E ON C.SLPCODE  = E.SLPCODE 
						where convert(varchar,a.docdate,23) between @datefrom and @dateto
						and (c.CardCode + c.cardname  like '%' + @cardcode + '%' AND isnull(C.U_AR_Person,'') LIKE '%' + @arperson + '%')
						and a.canceled = 'N'
						and a.CtlAccount = @account
						union all 

						select  c.CardCode ,
								'[' + C.CardCode + '] ' + C.CardName ,
								d.PymntGroup ,
								d.ExtraDays , 
								c.U_AR_Person ,
								e.SlpName + '-' + upper(e.U_SlsEmpName),
								convert(varchar,a.refdate,23) docdate ,
								'30-Jurnal Entry' ,
								isnull(b.U_Trans_No,convert(varchar,b.Number)) ,
								convert(varchar,b.number) ,
								'--',
								a.debit , 
								a.credit ,
								a.Debit - a.credit   ,
								convert(varchar,a.refdate,23)  ,
								convert(varchar,a.refdate,23) ,
								datediff(day,a.refdate,a.refdate),
								datediff(day,a.refdate,a.refdate),
								0
						from jdt1 a
						inner join ojdt b on a.TransId = b.TransId 
						inner join ocrd c on a.ShortName = c.CardCode     
							INNER JOIN OCTG D ON C.GroupNum = d.GroupNum 
							INNER JOIN OSLP E ON C.SLPCODE  = E.SLPCODE 
						where a.transtype =30 and a.account=@account
						and convert(varchar,a.refdate,23) between @DateFrom and @dateto
						and (c.CardCode + c.cardname  like '%' + @cardcode + '%' AND isnull(C.U_AR_Person,'') LIKE '%' + @arperson + '%')
						



						insert into @table2
						SELECT  b.invtype ,
								convert(varchar,d.docnum) , 
								sum(b.SumApplied) ,
								max(datediff(day,d.docdate,a.docdate)) ,
								max(datediff(day,d.docduedate,a.docdate)) ,
								max(CONVERT(VARCHAR, A.docdate ,23) ) 
						from orct a
						inner join rct2 b on a.DocEntry = b.DocNum
						inner join ocrd c on a.cardcode = c.cardcode 
						inner join oinv d on b.InvType=13 and d.docentry  = b.DocEntry
						where convert(varchar,d.docdate,23) between @datefrom and @dateto
						and (c.CardCode + c.cardname  like '%' + @cardcode + '%' AND isnull(C.U_AR_Person,'') LIKE '%' + @arperson + '%')
						and a.canceled = 'N'
						and a.BpAct=@account
						group by    b.invtype ,
									convert(varchar,d.docnum) 
						union all 

						SELECT  b.invtype ,
								convert(varchar,d.docnum) , 
								sum(b.SumApplied) ,
								max(datediff(day,d.docduedate,a.docdate)) ,
								max(datediff(day,d.docdate,a.docdate)) ,
								max(CONVERT(VARCHAR, A.docdate ,23) ) 
						from orct a
						inner join rct2 b on a.DocEntry = b.DocNum
						inner join ocrd c on a.cardcode = c.cardcode 
						inner join orin d on b.InvType=14 and d.docentry  = b.DocEntry
						where convert(varchar,d.docdate,23) between @datefrom and @dateto
						and (c.CardCode + c.cardname  like '%' + @cardcode + '%' AND isnull(C.U_AR_Person,'') LIKE '%' + @arperson + '%')
						and a.canceled = 'N'
						and a.BpAct=@account
						group by    b.invtype ,
									convert(varchar,d.docnum) 
						

						update @table  

						set maxdiff = b.maxdiff ,
							mindiff = b.mindiff ,
							avgdiff = b.avgdiff 
						from 
								(
								select      a.cardcode,
											maxdiff = max(b.diffduedate) ,
											mindiff = min(b.diffduedate) ,
											avgdiff = avg(b.diffduedate) 
								from @table a 
								inner join  @table2 B ON left(a.doctype ,2)= b.doctype  and a.docnumber = b.docnum 
								where isnull(b.diffduedate,0)<>0
								group by cardcode
								
								)  b where  b.cardcode = [@table].cardcode 
						select 
								a.cardname + '\n' +
								'Sales : ' + a.salesperson + '\n ' + 
								'AR : ' + a.arperson + '\n ' + 
								'Term of Payment : ' + a.salesperson + '\n ' + 
								'Max Diff : ' + ISNULL(convert(varchar,a.maxdiff),'0') + '\n ' + 
								'Min Diff : ' + ISNULL(convert(varchar,a.mindiff),'0') + '\n ' + 
								'Avg Diff : ' + ISNULL(convert(varchar,a.avgdiff),'0') + '\n ' as iname ,
								a.cardcode ,
								a.cardname ,
								a.PymntGroup ,
								a.ExtraDays ,
								a.arperson ,
								a.salesperson ,
								a.docdate ,
								a.doctype ,
								a.docnumber ,
								a.ref_number ,
								a.kwtno, 
								a.amount ,
								a.duedate ,
								isnull(b.diffdate,0) diffdate,
								isnull(b.diffduedate,0) diffduedate,
								b.paydate ,
								isnull(b.paytotal,0) ,
								a.amount - isnull(b.paytotal,0) balance,
								isnull(a.maxdiff,0) maxdiff,
								isnull(a.mindiff,0) mindiff,
								isnull(a.avgdiff,0) avgdiff


						from @table A
							left outer join  @table2 B ON left(a.doctype ,2)= b.doctype  and a.docnumber = b.docnum 



						order by    a.cardcode, 
									a.docdate ,
									a.doctype , 
									a.ref_number
			"""
			msgsql1 ="""
						DECLARE @DateFrom varchar(10) ,
								@DateTo varchar(10),
								@cardcode varchar(50) ,
								@account varchar(10) ,
								@arperson varchar(50)
						SET NOCOUNT ON
						set     @DateFrom = '""" + self.datefrom.strftime("%Y-%m-%d")  + """'
						set     @DateTo   = '""" + self.dateto.strftime("%Y-%m-%d")  + """'
						set     @CardCode = '""" + bp + """'
						set     @account  ='""" + self.account + """'
						set     @arperson = '""" + arperson + """'

						declare @table table (  
												idx int identity(1,1) ,
												cardcode varchar(50), 
												cardname varchar(100),
												docdate varchar(10),
												doctype varchar(50) ,
												docnumber varchar(50) ,
												ref_number varchar(50),
												kwtno   varchar(50),
												debit numeric(19,6) ,
												credit numeric(19,6) ,
												amount numeric(19,6) ,
												trxdate varchar(10) ,
												duedate varchar(10) ,
												diffdate int ,
												diffduedate int 
												)
						declare @table2 table ( cardcode varchar(50) ,
												maxdiff numeric(19,2) ,
												mindiff numeric(19,2) ,
												avgdiff numeric(19,2) ) 
						-- |Card Name | DocDate | Type | Doc No. | SO | Debet | Credit | Amount
						insert into @table 
						select  c.CardCode ,
								'[' + C.CardCode + '] ' + C.cardname ,
								@datefrom , 
								'00-Opening Balance' ,
								'Opening Balance' ,
								'Opening Balance' ,
								'--',
								sum(B.Debit - B.credit) ,
								0 ,
								sum(B.Debit - B.credit) ,
								@datefrom  ,
								@datefrom ,
								0,
								0
						from OJDT A 
							INNER JOIN JDT1 B ON A.transID = b.TransID 
							INNER JOIN OCRD C ON B.ShortName = C.CARDCODE 
						WHERE CONVERT(VARCHAR, A.REFDATE ,23) <=@DATEFROM 
						AND B.ACCOUNT = @account
						and (c.CardCode + c.cardname  like '%' + @cardcode + '%' AND isnull(C.U_AR_Person,'') LIKE '%' + @arperson + '%')

						GROUP BY c.CardCode , '[' + C.CardCode + '] ' + C.cardname
						HAVING sum(B.Debit - B.credit) <>0

						UNION ALL

						SELECT  c.CardCode ,
								'[' + C.CardCode + '] ' + C.CardName ,
								convert(varchar,a.docdate,23) docdate,
								'13-Invoice' ,
								convert(varchar,a.docnum) ,
								a.numatCard ,
								a.u_kw_no,
								a.doctotal ,
								0,
								a.doctotal,
								convert(varchar,a.docdate,23)   ,
								convert(varchar,a.docduedate,23)  ,
								0,
								0
						from oinv a 
						inner join ocrd c on a.cardcode = c.cardcode 
						where convert(varchar,a.docdate,23) between @datefrom and @dateto
						and (c.CardCode + c.cardname  like '%' + @cardcode + '%' AND isnull(C.U_AR_Person,'') LIKE '%' + @arperson + '%')
						and a.canceled = 'N'
						and a.CtlAccount = @account
						UNION ALL

						SELECT  
								c.CardCode ,
								'[' + C.CardCode + '] ' + C.CardName ,
								convert(varchar,a.docdate,23) docdate,
								'14-Credit Note' ,
								convert(varchar,a.docnum) ,
								a.numatCard ,
								a.u_kw_no,
								0,
								a.doctotal ,
								-1 * a.doctotal,
								convert(varchar,a.docdate,23)   ,
								convert(varchar,a.docduedate,23)  ,
								0,
								0
						from orin a 
						inner join ocrd c on a.cardcode = c.cardcode 
						where convert(varchar,a.docdate,23) between @datefrom and @dateto
						and (c.CardCode + c.cardname  like '%' + @cardcode + '%' AND isnull(C.U_AR_Person,'') LIKE '%' + @arperson + '%')
						and a.canceled = 'N'
						and a.CtlAccount = @account
						UNION ALL

						SELECT  c.CardCode , 
								'[' + C.CardCode + '] ' + C.CardName ,
								convert(varchar,a.docdate,23) docdate,
								'24-Payment Invoice' ,
								isnull(a.U_Trans_No,convert(varchar,a.docnum)) ,
								d.numatCard ,
								d.u_kw_no,
								0,
								b.SumApplied ,
								-1 *  b.SumApplied,
								convert(varchar,d.docdate,23)  ,
								convert(varchar,d.docduedate,23) ,
								datediff(day,d.docdate,a.docdate),
								datediff(day,d.docduedate,a.docdate)
						from orct a
						inner join rct2 b on a.DocEntry = b.DocNum
						inner join ocrd c on a.cardcode = c.cardcode 
						inner join oinv d on b.InvType=13 and d.docentry  = b.DocEntry
						where convert(varchar,a.docdate,23) between @datefrom and @dateto
						and (c.CardCode + c.cardname  like '%' + @cardcode + '%' AND isnull(C.U_AR_Person,'') LIKE '%' + @arperson + '%')
						and a.canceled = 'N'
						and a.BpAct=@account

						union all 
						SELECT  c.CardCode , 
								'[' + C.CardCode + '] ' + C.CardName ,
								convert(varchar,a.docdate,23) docdate,
								'24-Payment Credit' ,
								isnull(a.U_Trans_No,convert(varchar,a.docnum)) ,
								convert(varchar,d.docnum) ,
								d.u_kw_no,
								b.SumApplied,
								0 ,
								b.SumApplied,
								convert(varchar,d.docdate,23)  ,
								convert(varchar,d.docduedate,23) ,
								datediff(day,d.docdate,a.docdate),
								datediff(day,d.docduedate,a.docdate)
						from orct a
						inner join rct2 b on a.DocEntry = b.DocNum
						inner join ocrd c on a.cardcode = c.cardcode 
						inner join orin d on b.InvType=14 and d.docentry  = b.DocEntry
						where convert(varchar,a.docdate,23) between @datefrom and @dateto
						and (c.CardCode + c.cardname  like '%' + @cardcode + '%' AND isnull(C.U_AR_Person,'') LIKE '%' + @arperson + '%')
						and a.canceled = 'N'
						and a.BpAct=@account
						
						union all

						select  c.CardCode ,
								'[' + C.CardCode + '] ' + C.CardName  ,
								convert(varchar,a.refdate,23) docdate ,
								'30-Jurnal Entry' ,
								isnull(b.U_Trans_No,convert(varchar,b.Number)) ,
								convert(varchar,b.number) ,
								'--',
								a.debit , 
								a.credit ,
								a.Debit - a.credit   ,
								convert(varchar,a.refdate,23)  ,
								convert(varchar,a.refdate,23) ,
								datediff(day,a.refdate,a.refdate),
								datediff(day,a.refdate,a.refdate)
						from jdt1 a
						inner join ojdt b on a.TransId = b.TransId 
						inner join ocrd c on a.ShortName = c.CardCode 
						where a.transtype =30 and a.account=@account
						and convert(varchar,a.refdate,23) between @DateFrom and @dateto
						and (c.CardCode + c.cardname  like '%' + @cardcode + '%' AND isnull(C.U_AR_Person,'') LIKE '%' + @arperson + '%')

						insert into @table2
						select cardcode ,
							max(diffduedate) ,
							min(diffduedate) ,
							AVG(diffduedate) 
							from @table
							where left(doctype,2)='24'
						group by cardcode


						select    a.cardname  +
								'\n Sales : ' + d.SlpName + '-' + upper(d.U_SlsEmpName)   +
								'AR : '    + isnull(d.Memo,'')  + ' - ' +  upper(b.U_AR_Person) + '\n' +
								'Payment Term : ' + c.PymntGroup  + char(13) +
								'Max Diff Due vs Payment : ' + convert(varchar,e.maxdiff)  + '\n' +
								'Min Diff Due vs Payment : ' + convert(varchar,e.mindiff)  + '\n' +
								'Average Diff Due vs Payment : ' + convert(varchar,e.avgdiff)  + '\n'
								as data_customer ,
								a.*, 
								c.PymntGroup ,
								c.ExtraDays ,
								upper(b.U_AR_Person) arperson ,
								d.SlpName + '-' + upper(isnull(d.U_SlsEmpName,'')) salesperson ,
								d.Memo ,
								e.maxdiff ,
								e.mindiff ,
								e.avgdiff
						from @table a
							inner join ocrd b on a.cardcode = b.cardcode 
							inner join octg c on b.GroupNum = c.GroupNum 
							inner join oslp d on b.slpcode = d.slpcode 
							left outer join @table2 e on a.cardcode = e.cardcode

						order by    cardcode, 
									docdate ,
									doctype , 
									ref_number
			"""
			#print(msgsql)
			if self.export_to=="list":
				msgsql = msgsql1
			elif self.export_to=="listsummary" :
				msgsql = msgsql2
			elif self.export_to=="excelsummary" :
				msgsql = msgsql2
			elif self.export_to=="excel" :
				msgsql = msgsql1
 
			
			data = pandas.io.sql.read_sql(msgsql,conn) 
			listfinal.append(data)
  
		


		df = pd.concat(listfinal)  
		print(msgsql)
		if self.export_to=="list":
			self.env.cr.execute ("""DELETE FROM jas_lap_kartupiutangmdl WHERE create_uid =""" + str(self.env.user.id) + """ """ ) 
			
			datalist2 = df.values.tolist()
			#print(datalist2)
			for line in datalist2:
				self.env["jas.lap.kartupiutangmdl"].create({
											"name"				: line[0],
											"cardcode"			: line[2],
											"cardname"			: line[3],
											"docdate"			: line[4],
											"doctype"			: line[5],
											"docnumber"			: line[6],
											"refnumber"			: line[7],
											"kwtnumber"			: line[8],
											"debit"				: line[9],
											"credit"			: line[10],
											"amount"			: line[11],
											"trxdate"			: line[12],
											"duedate"			: line[13],
											"diffdate"			: line[14],
											"diffduedate"		: line[15],
											"paymentterm"		: line[16],
											"topdays"			: line[17],
											"arperson"			: line[18],
											"salesperson"		: line[19] ,
											"salesgroup"		: line[20] ,
											"maxdiff"			: line[21] ,
											"mindiff"			: line[22] ,
											"avgdiff"			: line[23] 
											
											})
			return {
				"type": "ir.actions.act_window",
				"res_model": "jas.lap.kartupiutangmdl",  
				#"view_id":view_do_list_tree, 
				"view_mode":"tree,pivot",
				"act_window_id":"jas_lap_kartupiutangmdl_action"}

		elif self.export_to=="listsummary":
			self.env.cr.execute ("""DELETE FROM jas_lap_kartupiutangmdl2 WHERE create_uid =""" + str(self.env.user.id) + """ """ ) 
			
			datalist2 = df.values.tolist()
			#print(datalist2)
			for line in datalist2:
				self.env["jas.lap.kartupiutangmdl2"].create({
											"name"				: line[0],
											"cardcode"			: line[1],
											"cardname"			: line[2],
											"paymentterm"		: line[3],
											"topdays"			: line[4],
											"arperson"			: line[5],
											"salesperson"		: line[6],
											"docdate"			: line[7],
											"doctype"			: line[8],
											"docnumber"			: line[9],
											"refnumber"			: line[10],
											"kwtnumber"			: line[11],
											"amount"			: line[12],
											"duedate"			: line[13],
											"diffdate"			: line[14],
											"diffduedate"		: line[15],
											"paydate"			: line[16],
											"paytotal"			: line[17],
											"balance"			: line[18] ,
											"maxdiff"			: line[19] ,
											"mindiff"			: line[20] ,
											"avgdiff"			: line[21]  
											
											})
			return {
				"type": "ir.actions.act_window",
				"res_model": "jas.lap.kartupiutangmdl2",  
				#"view_id":view_do_list_tree, 
				"view_mode":"tree,pivot",
				"act_window_id":"jas_lap_kartupiutangmdl2_action"}

		elif self.export_to=="excelsummary": 
			filename = filenamexls2 
			#report = df.groupby(["Group","AR Person"]).sum()
			df.to_excel(mpath + '/temp/'+ filenamexls2,index=False,engine='xlsxwriter') 
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
		elif self.export_to=="excel": 
			filename = filenamexls2 
			#report = df.groupby(["Group","AR Person"]).sum()
			df.to_excel(mpath + '/temp/'+ filenamexls2,index=False,engine='xlsxwriter')  
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
		 

 



class LapInvoiceC2Long(models.TransientModel):
	_name           = "jas.lap.invoicec2long"
	_description    = "Cetakan Invoice C2 Long "
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)

	datefrom        = fields.Date("Date From",default=lambda s:fields.Date.today())
	dateto          = fields.Date("Date To",default=lambda s:fields.Date.today())
	inv_from        = fields.Char("Invoice No from",default="")
	inv_to          = fields.Char("Invoice No To",default="")

	def get_invoicec2long(self):
		url = "http://192.168.1.171:8080/jasperserver/flow.html?_flowId=viewReportFlow&standAlone=true&_flowId=viewReportFlow&ParentFolderUri=%2Freports%2FIGU%2FAR&reportUnit=%2Freports%2FIGU%2FAR%2Finvoice_long_c2_odoo&j_username=jasperadmin&j_password=jasperadmin&decorate=no&prm_datefrom="+ self.datefrom.strftime("%Y-%m-%d")  +"&prm_dateto="+ self.dateto.strftime("%Y-%m-%d")  + "&prm_inv_from=" + self.inv_from  + "&prm_inv_to=" + self.inv_to  + "&prm_ppn=&output=pdf"
		return {
					"type": "ir.actions.act_url",
					"url": url,
					"target": "new",
				}                



class LapInvoiceC4Short(models.TransientModel):
	_name           = "jas.lap.invoicec4short"
	_description    = "Cetakan Invoice C4 Short "
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)

	datefrom        = fields.Date("Date From",default=lambda s:fields.Date.today())
	dateto          = fields.Date("Date To",default=lambda s:fields.Date.today())
	inv_from        = fields.Char("Invoice No from",default="")
	inv_to          = fields.Char("Invoice No To",default="")

	def get_invoicec4short(self):
		url = "http://192.168.1.171:8080/jasperserver/flow.html?_flowId=viewReportFlow&standAlone=true&_flowId=viewReportFlow&ParentFolderUri=%2Freports%2FIGU%2FAR&reportUnit=%2Freports%2FIGU%2FAR%2Finvoice_print_c4_odoo&j_username=jasperadmin&j_password=jasperadmin&decorate=no&prm_datefrom="+ self.datefrom.strftime("%Y-%m-%d")  +"&prm_dateto="+ self.dateto.strftime("%Y-%m-%d")  + "&prm_inv_from=" + self.inv_from  + "&prm_inv_to=" + self.inv_to  + "&prm_ppn=&output=pdf"
		return {
					"type": "ir.actions.act_url",
					"url": url,
					"target": "new",
				}                


class LapInvoiceB1(models.TransientModel):
	_name           = "jas.lap.invoiceb1logo"
	_description    = "Cetakan Invoice B1 "
	company_id      = fields.Many2one('res.company', 'Company', required=True, index=True,  default=lambda self: self.env.user.company_id.id)

	datefrom        = fields.Date("Date From",default=lambda s:fields.Date.today())
	dateto          = fields.Date("Date To",default=lambda s:fields.Date.today())
	inv_from        = fields.Char("Invoice No from",default="")
	inv_to          = fields.Char("Invoice No To",default="")


	def get_invoiceb1logo(self):
		url = "http://192.168.1.171:8080/jasperserver/flow.html?_flowId=viewReportFlow&standAlone=true&_flowId=viewReportFlow&ParentFolderUri=%2Freports%2FIGU%2FAR&reportUnit=%2Freports%2FIGU%2FAR%2Finvoice_print_b1_odoo&j_username=jasperadmin&j_password=jasperadmin&decorate=no&prm_datefrom="+ self.datefrom.strftime("%Y-%m-%d")  +"&prm_dateto="+ self.dateto.strftime("%Y-%m-%d")  + "&prm_inv_from=" + self.inv_from  + "&prm_inv_to=" + self.inv_to  + "&output=pdf"
		return {
					"type": "ir.actions.act_url",
					"url": url,
					"target": "new",
				}                                