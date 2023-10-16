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


class AWR_PurchasingReportList(models.Model):
	_name           = "cnw.awr28.purchasingreportmodel"
	_description    = "cnw.awr28.purchasingreportmodel"
	name            = fields.Char("Name")
	company_id      = fields.Many2many('res.company', string="Company",required=True)


class AWR_PurchasingReport(models.TransientModel):
	_name           = "cnw.awr28.purchasingreport"
	_description    = "cnw.awr28.purchasingreport"
	company_id      = fields.Many2many('res.company', string="Company",required=True)
	datefrom        = fields.Date ("Date From", default=fields.Date.today()) 
	dateto          = fields.Date ("Date To", default=fields.Date.today()) 
	partner         = fields.Char("Partner")
	item            = fields.Char("Item(s)")
	itemgroup       = fields.Char("Item Group (s)")
	igroup         = fields.Selection([ ('','All'),('Lokal', 'Lokal'), ('Import', 'Import'), ('Cabang', 'Cabang'), ('Group', 'Group'),],string='Vendor Group', default='')
	export_to       = fields.Selection([    ('summarypartner', 'Total Per Partner'), 
											('topgroupitem', 'Top Group Item'), 
											('toppartneritem', 'Top Partner Item'), 
											('apservices', 'AP services'), 
											('summaryaptype', 'Summary AP Type'), 
											('summary', 'AP invoice Summary'),
											('json', 'JSON Summary Format'),
											('json2', 'JSON Detail Format'),
											('pdf', 'PDF Summary Format'),
											('pdf2', 'PDF Detail Format'),
											('detail', 'Detail Per Item'),],
											string='Export To', default='pdf')
	filexls         = fields.Binary("File Output", default=" ")    
	filenamexls     = fields.Char("File Name Output" ,default="txt.txt")
	
	
	
	def view_pl(self): 
		mpath           = get_module_path('cnw_awr28')
		filex           = 'purchasingreport_'+ self.env.user.company_id.db_name +  self.dateto.strftime("%Y%m%d") 
		filenamejson    = filex + '.json'
		filename        = 'purchasingreport_'+ self.env.user.company_id.db_name +  self.dateto.strftime("%Y%m%d")  + '.xlsx'
		filenamexls     = 'purchasingreport_'+ self.env.user.company_id.db_name +   self.dateto.strftime("%Y%m%d")  + '.xlsx'
		filenamexls2    = 'purchasingreport_'+  self.env.user.company_id.db_name +  self.dateto.strftime("%Y%m%d")  + '.xlsx'
		filenamepdf     = 'purchasingreport_'+  self.env.user.company_id.db_name +  self.dateto.strftime("%Y%m%d")  + '.pdf'
		filepath        = mpath + '/temp/'+ filename
		logo            = mpath + '/awr_template/logoigu.png' 
		listfinal       = []
		options         = {
							'orientation': 'portrait',
							}        
		igu_tanggal     = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")

		pd.options.display.float_format = '{:,.2f}'.format        

		item = self.item if self.item else ""
		partner = self.partner if self.partner else ""
		igroup = self.igroup if self.igroup else ""
		itemgroup = self.itemgroup if self.itemgroup else ""

		for comp in self.company_id:

			host        = comp.server
			database    = comp.db_name
			user        = comp.db_usr
			password    = comp.db_pass 
			msgreportsummary = """
									declare 
											@datefrom varchar(20),
											@dateto varchar(20),
											@company varchar(50) ,
											@item varchar(50) ,
											@supplier  varchar(50) ,
											@igroup varchar(50) 


									set @datefrom = '"""+   self.datefrom.strftime("%Y%m%d") + """' 
									set @dateto = '"""+   self.dateto.strftime("%Y%m%d") + """' 
									set @company = '"""+   comp.name + """' 
									set @item = '""" + item + """'
									set @supplier ='""" + partner + """'
									set @igroup = '""" + igroup + """'

										declare @table table (  idx int identity(1,1)  , 
												docentry int,
												docnum varchar(50) ,  
												grpo int ,
												numatcard varchar(50))

										declare @table2 table (  idx int identity(1,1)  , 
												oipf  int,
												opdn int )

										declare @table3 table (  idx int identity(1,1)  , 
												opdn  int,
												bea_masuk numeric(19,2),
												shipment numeric(19,2),
												receiving numeric(19,2),
												pib_pnbp numeric(19,2),
												surveyor numeric(19,2),
												h_biaya numeric(19,2),
												lainlain numeric(19,2),
												total numeric(19,2) ) 


										INSERT INTO @TABLE
										select DISTINCT A.DOCENTRY, D.DOCNUM ,c.docentry , D.NUMATCARD 
										from OPCH (nolock) A 
										INNER JOIN PCH1 (nolock)  B ON A.DOCENTRY  = B.DOCENTRY
										INNER JOIN PDN1 (nolock)  C ON B.BASEENTRY = C.DOCENTRY AND B.BASETYPE = 20 
										INNER JOIN OPOR (nolock)  D ON C.BASEENTRY = D.DOCENTRY AND C.BASETYPE=22 

										where convert(varchar,a.docdate,112)between @datefrom and @dateto



										insert into  @table2 
										select distinct a.docentry ,b.oribaBsEnt  from OIPF (nolock)  a 
										inner join ipf1 (nolock)  b on a.DocEntry = b.docentry 
										where  convert(varchar,a.docdate,112)between @datefrom and @dateto
										order by b.oribaBsEnt

										insert into @table3
										select c.opdn, 
										-1 *    sum(bea_masuk) ,
										-1 *    sum(shipment) ,
										-1 *    sum(receiving) ,
										-1 *    sum(pib_pnbp) ,
										-1 *    sum(surveyor) ,                                    
										-1 *    sum(h_biaya) ,
										-1 *    sum(lainlain) , 
										-1 *    sum(amount) 

										from oipf (nolock) a 
										inner join 
										(
										select  a.transid,
										SUM(case when a.account = '2140001' then a.debit - a.credit else 0 end )  bea_masuk,
										SUM(case when a.account = '2140002' then a.debit - a.credit else 0 end ) shipment,
										SUM(case when a.account = '2140003' then a.debit - a.credit else 0 end ) receiving,
										SUM(case when a.account = '2140004' then a.debit - a.credit else 0 end ) pib_pnbp,
										SUM(case when a.account = '2140005' then a.debit - a.credit else 0 end ) surveyor,
										SUM(case when a.account = '2140006' then a.debit - a.credit else 0 end ) h_biaya,
										SUM(case when a.account = '2140007' then a.debit - a.credit else 0 end ) lainlain,        
										sum(a.debit - a.credit) amount
										from jdt1 (nolock) a 
										inner join ojdt (nolock) b on a.transid = b.transid 
										where  convert(varchar,b.refdate,112)between @datefrom and @dateto
										and left(a.account,4)='2140' and a.TransType =69
										group by a.transid 
										)B ON a.JdtNum = b.transid 
										inner join @table2 c on a.docentry = c.oipf 
										where  convert(varchar,a.docdate,112)between @datefrom and @dateto
										group by c.opdn 

										select distinct
										@company company,
										'AP Invoice' docs,
										a.doctype,
										a.docentry ,
										a.docnum ,
										a.numatcard , 
										a.U_PI_No PI_Number,
										a.u_Vessel ,
										replace(replace(a.u_Container,char(10),'') ,char(13),'')u_Container , 
										a.u_Pesawat ,
										a.u_AwBillNo ,
										a.u_VendDO_No ,
										a.u_IGU_PIBNo, 
										a.u_IGU_PIB_Nop Nopen ,
										convert(varchar,a.u_IGU_PIBRemarks) KodeBilling ,
										isnull(a.U_Int_BarCode,'') NTPN ,
										a.u_IGU_Invoice_Vendor ,
										a.u_IGU_PPh_21 PPh22,
										a.u_IGU_Payment PPnPIB, 
										isnull(a.u_IGU_TotalCif2,0) NilaiPabean_IDR ,
										a.u_IGU_NDPBM ,
										convert(varchar,a.docDate,23) docDate ,
										a.cardcode ,
										a.cardname ,
										a.shiptocode,
										C.GROUPNAME ,
										(a.DocTotalSy) Doctotal,
										(a.DpmAmntSC) DownPayment ,
										(a.VatSum) PPn,
										(a.Max1099)  - (a.VatSum)  Amount,
										isnull(i.bea_masuk,0) bea_masuk ,
										isnull(i.shipment,0) shipment ,
										isnull(i.receiving,0) receiving ,
										isnull(i.pib_pnbp,0) pib_pnbp ,
										isnull(i.surveyor,0) surveyor ,
										isnull(i.h_biaya,0) h_biaya ,
										isnull(i.lainlain,0) lainlain , 
										isnull(i.total,0) TotalLandedCost ,
										isnull(a.TotalExpSC,0) Freight,
										(isnull(a.Max1099,0) )  - (isnull(a.VatSum,0)) + isnull(a.TotalExpSC,0) + isnull(i.total,0)  total
										from OPCH A 
										INNER JOIN OCRD B ON A.CARDCODE = B.CARDCODE 
										INNER JOIN OCRG C ON B.GROUPCODE = C.GROUPCODE
										inner join @table f on a.docentry = f.docentry
										left outer join @table3 i on f.grpo = i.opdn
										WHERE  convert(varchar,a.docdate,112)between @datefrom and @dateto
										and a.canceled ='N' 
										and a.CtlAccount = '2110001'
										and b.cardcode + b.cardname like '%' + @supplier + '%'   
										and c.groupname like '%' + @igroup + '%'

										UNION ALL

										select distinct
										@company company,
										'AP Credit',
										a.doctype,
										a.docentry ,
										a.docnum ,
										a.numatcard , 
										a.U_PI_No PI_Number,
										a.u_Vessel ,
										replace(replace(a.u_Container,char(10),'') ,char(13),'') u_Container, 
										a.u_Pesawat ,
										a.u_AwBillNo ,
										a.u_VendDO_No ,
										a.u_IGU_PIBNo, 
										a.u_IGU_PIB_Nop Nopen ,
										convert(varchar,a.u_IGU_PIBRemarks) KodeBilling ,
									'' NTPN ,
										a.u_IGU_Invoice_Vendor ,
										a.u_IGU_PPh_21 PPh22,
										a.u_IGU_Payment PPnPIB, 
										a.u_IGU_TotalCif2 NilaiPabean_IDR ,
										a.u_IGU_NDPBM ,
										convert(varchar,a.docDate,23) docDate ,
										a.cardcode ,
										a.cardname ,
										a.shiptocode,
										c.groupname ,
										-1* (a.DocTotalSy) Doctotal,
										-1* (a.DpmAmntSC) DownPayment ,
										-1* (a.VatSum) VatSum,
										-1* (a.Max1099  - (a.VatSum))  Amount,
										0 LANDED ,
										0 LANDED ,
										0 LANDED ,
										0 LANDED ,
										0 LANDED ,
										0 LANDED ,
										0 LANDED ,
										0 LANDED ,
										-1* a.TotalExpSC Freight,
										-1* (a.Max1099  - (a.VatSum) + isnull(a.TotalExpSC,0))  total
										from orpc A 
										INNER JOIN OCRD B ON A.CARDCODE = B.CARDCODE 
										INNER JOIN OCRG C ON B.GROUPCODE = C.GROUPCODE
										inner join 
										(select distinct a.docentry from rpc1 a
										inner join orpc b on a.docentry = b.docentry where  convert(varchar,b.docdate,112)between @datefrom and @dateto and a.basetype<>204) d on a.docentry = d.docentry  
										WHERE  convert(varchar,a.docdate,112)between @datefrom and @dateto
										and a.canceled ='N'  
										and a.CtlAccount = '2110001'
										and b.cardcode + b.cardname like '%' + @supplier + '%'   
										and c.groupname like '%' + @igroup + '%'

"""
			msgreportsummaryservices = """
								declare 
										@datefrom varchar(20),
										@dateto varchar(20),
										@company varchar(50) ,
										@item varchar(50) ,
										@supplier  varchar(50) ,
										@igroup varchar(50) 


								set @datefrom = '"""+   self.datefrom.strftime("%Y%m%d") + """' 
								set @dateto = '"""+   self.dateto.strftime("%Y%m%d") + """' 
								set @company = '"""+   comp.name + """' 
								set @item = '""" + item + """'
								set @supplier ='""" + partner + """'
								set @igroup = '""" + igroup + """'

									declare @table table (  idx int identity(1,1)  , 
											docentry int,
											docnum varchar(50) ,  
											grpo int ,
											numatcard varchar(50))

									declare @table2 table (  idx int identity(1,1)  , 
											oipf  int,
											opdn int )

									declare @table3 table (  idx int identity(1,1)  , 
											opdn  int,
											bea_masuk numeric(19,2),
											shipment numeric(19,2),
											receiving numeric(19,2),
											pib_pnbp numeric(19,2),
											surveyor numeric(19,2),
											h_biaya numeric(19,2),
											lainlain numeric(19,2),
											total numeric(19,2) ) 


									INSERT INTO @TABLE
									select DISTINCT A.DOCENTRY, D.DOCNUM ,c.docentry , D.NUMATCARD 
									from OPCH (nolock) A 
									INNER JOIN PCH1 (nolock)  B ON A.DOCENTRY  = B.DOCENTRY
									INNER JOIN PDN1 (nolock)  C ON B.BASEENTRY = C.DOCENTRY AND B.BASETYPE = 20 
									INNER JOIN OPOR (nolock)  D ON C.BASEENTRY = D.DOCENTRY AND C.BASETYPE=22 

									where convert(varchar,a.docdate,112)between @datefrom and @dateto



									insert into  @table2 
									select distinct a.docentry ,b.oribaBsEnt  from OIPF (nolock)  a 
									inner join ipf1 (nolock)  b on a.DocEntry = b.docentry 
									where  convert(varchar,a.docdate,112)between @datefrom and @dateto
									order by b.oribaBsEnt

									insert into @table3
									select c.opdn, 
									-1 * sum(bea_masuk) ,
									-1 * sum(shipment) ,
									-1 * sum(receiving) ,
									-1 * sum(pib_pnbp) ,
									-1 * sum(surveyor) ,
									-1 * sum(h_biaya) ,
									-1 * sum(lainlain) , 
									-1 *  sum(amount) 

									from oipf (nolock) a 
									inner join 
									(
									select  a.transid,
									SUM(case when a.account = '2140001' then a.debit - a.credit else 0 end )  bea_masuk,
									SUM(case when a.account = '2140002' then a.debit - a.credit else 0 end ) shipment,
									SUM(case when a.account = '2140003' then a.debit - a.credit else 0 end ) receiving,
									SUM(case when a.account = '2140004' then a.debit - a.credit else 0 end ) pib_pnbp,
									SUM(case when a.account = '2140005' then a.debit - a.credit else 0 end ) surveyor,
									SUM(case when a.account = '2140006' then a.debit - a.credit else 0 end ) h_biaya,
									SUM(case when a.account = '2140007' then a.debit - a.credit else 0 end ) lainlain,        
									sum(a.debit - a.credit) amount
									from jdt1 (nolock) a 
									inner join ojdt (nolock) b on a.transid = b.transid 
									where  convert(varchar,b.refdate,112)between @datefrom and @dateto
									and left(a.account,4)='2140' and a.TransType =69
									group by a.transid 
									)B ON a.JdtNum = b.transid 
									inner join @table2 c on a.docentry = c.oipf 
									where  convert(varchar,a.docdate,112)between @datefrom and @dateto
									group by c.opdn 

									select distinct
									@company company,
									'AP Invoice' docs,
									a.doctype,
									a.docentry ,
									a.docnum ,
									a.numatcard ,a.u_IGU_PIBRemarks 
									a.u_Vessel ,
									replace(replace(a.u_Container,char(10),'') ,char(13),'')u_Container , 
									a.u_Pesawat ,
									a.u_AwBillNo ,
									a.u_VendDO_No ,
									a.u_IGU_PIBNo, 
									a.u_IGU_PIB_Nop Nopen ,
									a.u_IGU_Invoice_Vendor ,
									a.u_IGU_PPh_21 ,
										a.u_IGU_Payment PPnPIB, 
									a.u_IGU_Tgl_SSPCP ,
									a.u_IGU_NDPBM ,
									a.docDate ,
									a.cardcode ,
									a.cardname ,
									a.shiptocode,
									C.GROUPNAME ,
									(a.DocTotalSy) Doctotal,
									(a.DpmAmntSC) DownPayment ,
									(a.VatSum) PPn,
									(a.Max1099)  - (a.VatSum)  Amount,
									isnull(i.bea_masuk,0) bea_masuk ,
									isnull(i.shipment,0) shipment ,
									isnull(i.receiving,0) receiving ,
									isnull(i.pib_pnbp,0) pib_pnbp ,
									isnull(i.surveyor,0) surveyor ,
									isnull(i.h_biaya,0) h_biaya ,
									isnull(i.lainlain,0) lainlain , 
									isnull(i.total,0) TotalLandedCost ,
									isnull(a.TotalExpSC,0) Freight,
									(isnull(a.Max1099,0) )  - (isnull(a.VatSum,0)) + isnull(a.TotalExpSC,0) + isnull(i.total,0)  total
									from OPCH A 
									INNER JOIN OCRD B ON A.CARDCODE = B.CARDCODE 
									INNER JOIN OCRG C ON B.GROUPCODE = C.GROUPCODE
									inner join @table f on a.docentry = f.docentry
									left outer join @table3 i on f.grpo = i.opdn
									WHERE  convert(varchar,a.docdate,112)between @datefrom and @dateto
									and a.canceled ='N'    and a.doctype='S'
									and b.cardcode + b.cardname like '%' + @supplier + '%'   
									and c.groupname like '%' + @igroup + '%'
									union all
									select distinct
									@company company,
									'AP Credit',
									a.doctype,
									a.docentry ,
									a.docnum ,
									a.numatcard ,
									a.shiptocode, 
									a.U_PI_No PI_Number,
									a.u_Vessel ,
									replace(replace(a.u_Container,char(10),'') ,char(13),'') u_Container, 
									a.u_Pesawat ,
									a.u_AwBillNo ,
									a.u_VendDO_No ,
									a.u_IGU_PIBNo, 
									a.u_IGU_PIB_Nop Nopen ,
									a.u_IGU_Invoice_Vendor ,
									a.u_IGU_PPh_21 ,
										a.u_IGU_Payment PPnPIB, 
									a.u_IGU_Tgl_SSPCP ,
									a.u_IGU_NDPBM ,
									a.docDate ,
									a.cardcode ,
									a.cardname ,
									a.shiptocode,
									c.groupname ,
									-1* (a.DocTotalSy) Doctotal,
									-1* (a.DpmAmntSC) DownPayment ,
									-1* (a.VatSum) VatSum,
									-1* (a.Max1099  - (a.VatSum))  Amount,
									0 LANDED ,
									0 LANDED ,
									0 LANDED ,
									0 LANDED ,
									0 LANDED ,
									0 LANDED ,
									0 LANDED ,
									a.u_IGU_PIBNo, 
									a.u_IGU_PIB_Nop Nopen ,
									a.u_IGU_PIBRemarks KodeBilling ,
									-1* a.TotalExpSC Freight,
									-1* (a.Max1099  - (a.VatSum) + isnull(a.TotalExpSC,0))  total
									from orpc A 
									INNER JOIN OCRD B ON A.CARDCODE = B.CARDCODE 
									INNER JOIN OCRG C ON B.GROUPCODE = C.GROUPCODE
									inner join 
									(select distinct a.docentry from rpc1 a
									inner join orpc b on a.docentry = b.docentry where  convert(varchar,b.docdate,112)between @datefrom and @dateto and a.basetype<>204) d on a.docentry = d.docentry  
									WHERE  convert(varchar,a.docdate,112)between @datefrom and @dateto
									and a.canceled ='N'   and a.doctype='S'
									and b.cardcode + b.cardname like '%' + @supplier + '%'   
									and c.groupname like '%' + @igroup + '%'

"""

			msgreportdetail = """   
				   
								declare 
											@datefrom varchar(20),
											@dateto varchar(20) ,
											@company varchar(50) ,
											@item varchar(50) ,
											@supplier  varchar(50) ,
											@igroup varchar(50) ,@itemgroup varchar(50)
 
											set @datefrom = '"""+   self.datefrom.strftime("%Y%m%d") + """' 
											set @dateto = '"""+   self.dateto.strftime("%Y%m%d") + """' 
											set @company = '"""+   comp.name + """' 
											set @item = '""" + item + """'
											set @supplier ='""" + partner + """'
											set @igroup = '""" + igroup + """'
											set @itemgroup = '""" + itemgroup + """"' 

								declare @table table (  idx int identity(1,1)  , 
														docentry int,
														docnum varchar(100) ,  
														grpo int ,
														numatcard varchar(100))

								declare @table2 table (  idx int identity(1,1)  , 
														oipf  int,
														opdn int )

								declare @table3 table (  idx int identity(1,1)  , 
														opdn  int,
														bea_masuk numeric(19,2),
														shipment numeric(19,2),
														receiving numeric(19,2),
														pib_pnbp numeric(19,2),
														surveyor numeric(19,2),
														h_biaya numeric(19,2),
														lainlain numeric(19,2),
														total numeric(19,2) ) 

								INSERT INTO @TABLE
								select DISTINCT A.DOCENTRY, D.DOCNUM ,c.docentry , D.NUMATCARD 
								from OPCH (nolock)  A 
									INNER JOIN PCH1 (nolock)  B ON A.DOCENTRY  = B.DOCENTRY
									INNER JOIN PDN1 (nolock) C ON B.BASEENTRY = C.DOCENTRY AND B.BASETYPE = 20 
									INNER JOIN OPOR (nolock) D ON C.BASEENTRY = D.DOCENTRY AND C.BASETYPE=22 
								
								where  convert(varchar,a.docdate,112)between @datefrom and @dateto


								
								insert into  @table2 
								select distinct a.docentry ,b.oribaBsEnt  from OIPF (nolock) a 
								inner join ipf1 (nolock) b on a.DocEntry = b.docentry 
								where  convert(varchar,a.docdate,112)between @datefrom and @dateto
								order by b.oribaBsEnt

								insert into @table3
								select c.opdn,-1 * sum(bea_masuk) ,
										-1 * sum(shipment) ,
										-1 * sum(receiving) ,
										-1 * sum(pib_pnbp) ,
										-1 * sum(surveyor) ,
										-1 * sum(h_biaya) ,
										-1 * sum(lainlain) , 
										-1 *  sum(amount) from oipf (nolock) a 
								inner join 
								(
										select  a.transid, 
												SUM(case when a.account = '2140001' then a.debit - a.credit else 0 end )  bea_masuk,
												SUM(case when a.account = '2140002' then a.debit - a.credit else 0 end ) shipment,
												SUM(case when a.account = '2140003' then a.debit - a.credit else 0 end ) receiving,
												SUM(case when a.account = '2140004' then a.debit - a.credit else 0 end ) pib_pnbp,
												SUM(case when a.account = '2140005' then a.debit - a.credit else 0 end ) surveyor,
												SUM(case when a.account = '2140006' then a.debit - a.credit else 0 end ) h_biaya,
												SUM(case when a.account = '2140007' then a.debit - a.credit else 0 end ) lainlain,      
												sum(a.debit - a.credit) amount
										from jdt1 (nolock) a 
											inner join ojdt (nolock) b on a.transid = b.transid 
										where  convert(varchar,b.refdate,112)between @datefrom and @dateto
										and left(a.account,4)='2140' and a.TransType =69
										group by a.transid 
								)B ON a.JdtNum = b.transid 
								inner join @table2 c on a.docentry = c.oipf 
								where  convert(varchar,a.docdate,112)between @datefrom and @dateto
								group by c.opdn 

								select 
										@company company,
									'AP Invoice' itype,
									a.docentry ,
									a.docnum ,
									f.docnum PO, 
									f.numatcard Vendor_invoice, 
									a.numatcard,
									isnull(b.U_PI_Number,isnull(a.u_PI_NO,'')) PI_Number ,
									isnull(b.U_slaughterhouse,'') 'Rumah Potong/EST',
									a.U_Vessel ,
									a.U_Container ,
									a.U_Pesawat ,
									a.U_AwBillNo ,
									a.U_VendDO_No ,
									a.U_Cust_PO_No ,
									a.U_PL_No ,
									a.U_Do_No ,

									a.u_IGU_PIBNo, 
									a.u_IGU_PIB_Nop Nopen ,
									convert(varchar,a.u_IGU_PIBRemarks) KodeBilling ,
									'' NTPN ,
									a.u_IGU_Invoice_Vendor ,
									a.u_IGU_PPh_21 PPh22,
										a.u_IGU_Payment PPnPIB, 
									a.u_IGU_TotalCif2 NilaiPabean_IDR ,
									a.u_IGU_NDPBM ,

									a.docDate ,
									a.cardcode ,
									a.cardname ,
									a.shiptocode,
									h.groupname group_Vendor,
									k.whsname ,
									b.itemcode ,
									e.itemname ,
									e.U_group ,
									e.u_Subgroup ,
									e.u_country ,
									b.vatgroup PPn_inTrx,
									e.vatgourpSa PPn_inMaster,
									isnull(convert(varchar,e.u_hs_code),'') HSCode,
									isnull(convert(varchar,e.u_spegroup),'') spegroup,
									isnull(e.U_spec,'') U_spec, 
									b.Quantity ,
									
									b.Currency ,
									b.Rate ,
									b.Price ,
									b.TotalFrgn, 
									b.TotalSumSy,
									b.LineTotal - (isnull(a.DiscPrcnt,0)/ 100 * b.LineTotal ) LineTotal , 
									(isnull(i.bea_masuk,0)/(a.max1099 - a.vatsum)) * (b.LineTotal - (isnull(a.DiscPrcnt,0)/ 100 * b.LineTotal )) bea_masuk , 
									(isnull(i.shipment,0)/(a.max1099 - a.vatsum)) * (b.LineTotal - (isnull(a.DiscPrcnt,0)/ 100 * b.LineTotal )) shipment , 
									(isnull(i.receiving,0)/(a.max1099 - a.vatsum)) * (b.LineTotal - (isnull(a.DiscPrcnt,0)/ 100 * b.LineTotal )) receiving , 
									(isnull(i.pib_pnbp,0)/(a.max1099 - a.vatsum)) * (b.LineTotal - (isnull(a.DiscPrcnt,0)/ 100 * b.LineTotal )) pib_pnbp , 
									(isnull(i.surveyor,0)/(a.max1099 - a.vatsum)) * (b.LineTotal - (isnull(a.DiscPrcnt,0)/ 100 * b.LineTotal )) surveyor , 
									(isnull(i.h_biaya,0)/(a.max1099 - a.vatsum)) * (b.LineTotal - (isnull(a.DiscPrcnt,0)/ 100 * b.LineTotal )) h_biaya , 
									(isnull(i.lainlain,0)/(a.max1099 - a.vatsum)) * (b.LineTotal - (isnull(a.DiscPrcnt,0)/ 100 * b.LineTotal )) lainlain ,  
									(isnull(i.total,0)/(a.max1099 - a.vatsum)) * (b.LineTotal - (isnull(a.DiscPrcnt,0)/ 100 * b.LineTotal )) landed , 
									b.dstrbsumSc freight  ,
									(b.LineTotal - (isnull(a.DiscPrcnt,0)/ 100 * b.LineTotal ))+ b.dstrbsumSc + (isnull(i.total,0)/(a.max1099 - a.vatsum))* (b.LineTotal - (isnull(a.DiscPrcnt,0)/ 100 * b.LineTotal ))  Total
									
								from OPCH (nolock) A 
								inner join pch1 (nolock) b on a.docentry = b.docentry 
								inner join oitm (nolock) e on b.itemcode = e.itemcode and e.InvntItem='Y'  
								inner join ocrd (nolock) g on a.cardcode = g.cardcode 
								inner join ocrg (nolock) h on g.groupcode = h.groupcode 
								inner join owhs (nolock) k on b.whscode = k.whscode
								inner join @table f on a.docentry = f.docentry
								left outer join @table3 i on f.grpo = i.opdn

								WHERE  convert(varchar,a.docdate,112)between @datefrom and @dateto
									and g.cardcode + g.cardname like '%' + @supplier + '%'
									and h.groupname like '%' + @igroup + '%' 
									and e.itemcode + e.itemname like '%' + @item + '%'                                 
									and a.canceled ='N'   
									and (a.max1099 - a.vatsum) <>0
									and a.CtlAccount = '2110001'

								union all
								select @company company,
									'AP Credit',
									a.docentry ,
									a.docnum ,
									'-' PO,
									'' Vendor_invoice, 
									a.numatcard,
									isnull(b.U_PI_Number,isnull(a.u_PI_NO,'')) U_PI_No ,
									isnull(b.U_slaughterhouse,'') 'Rumah Potong/EST',
									a.U_Vessel ,
									a.U_Container ,
									a.U_Pesawat ,
									a.U_AwBillNo ,
									a.U_VendDO_No ,
									a.U_Cust_PO_No ,
									a.U_PL_No ,
									a.U_Do_No ,

									a.u_IGU_PIBNo, 
									a.u_IGU_PIB_Nop Nopen ,
									convert(varchar,a.u_IGU_PIBRemarks) KodeBilling ,
									''NTPN ,
									a.u_IGU_Invoice_Vendor ,
									a.u_IGU_PPh_21 PPh22,
										a.u_IGU_Payment PPnPIB, 
									a.u_IGU_TotalCif2 NilaiPabean_IDR ,
									a.u_IGU_NDPBM ,

									a.docDate ,
									a.cardcode ,
									a.cardname ,
									a.shiptocode,
									h.groupname group_Vendor,
									k.whsname ,
									b.itemcode ,
									e.itemname ,
									e.U_group ,
									e.u_Subgroup ,
									e.u_country ,
									b.vatgroup PPn_inTrx,
									e.vatgourpSa PPn_inMaster,
									isnull(convert(varchar,e.u_hs_code),'') HSCode,
									isnull(convert(varchar,e.u_spegroup),'') spegroup,
									isnull(e.U_spec,'') ,
									-1 * b.Quantity ,
									b.Currency ,
									b.Rate ,
									-1 * b.Price ,
									-1 * b.TotalFrgn, 
									-1 * b.TotalSumSy, 
									-1 * (b.LineTotal - (a.DiscPrcnt/ 100 * b.LineTotal )),
										0 landed         ,
										0 landed         ,
										0 landed         ,
										0 landed         ,
										0 landed         ,
										0 landed         ,
										0 landed         ,
										0 landed         ,
										isnull(b.dstrbsumSc,0)  Freight ,
										-1 * ((b.LineTotal - (isnull(a.DiscPrcnt,0)/ 100 * b.LineTotal )) + isnull(b.dstrbsumSc,0) )
								from orpc (nolock) A 
								inner join pch1 (nolock) b on a.docentry = b.docentry 
								inner join oitm (nolock) e on b.itemcode = e.itemcode and e.InvntItem='Y'  
								inner join ocrd (nolock) g on a.cardcode = g.cardcode 
								inner join ocrg (nolock) h on g.groupcode = h.groupcode 
								inner join owhs (nolock) k on b.whscode = k.whscode       
								inner join 
									(select distinct a.docentry from rpc1 a (nolock) 
										inner join orpc b on a.docentry = b.docentry 
										where  convert(varchar,b.docdate,112)between @datefrom and @dateto and a.basetype<>204
									) c on a.docentry = c.docentry  
								WHERE  convert(varchar,a.docdate,112) between @datefrom and @dateto
								and a.canceled ='N'   
								and a.CtlAccount = '2110001' 
								and g.cardcode + g.cardname like '%' + @supplier + '%'
								and h.groupname like '%' + @igroup + '%' 
								and e.u_Group like '%' + isnull(@itemgroup,'') + '%' 
								and e.itemcode + e.itemname like '%' + @item + '%'             
			"""
			
			#conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';UID='+user+';PWD='+ password + ';TrustServerCertificate=yes')
			conn = pymssql.connect(host=host, user=user, password=password, database=database)
			cursor = conn.cursor()
			
			if self.export_to =="summary":
				msg_sql=  "exec [dbo].[IGU_ACCT_PURCHASINGREPORT] '" +  self.datefrom.strftime("%Y%m%d") + "','" +  self.dateto.strftime("%Y%m%d") + "','"+ comp.code_base + "' "
				msg_sql = msgreportsummary
			
			if self.export_to =="summarypartner":
				msg_sql=  "exec [dbo].[IGU_ACCT_PURCHASINGREPORT] '" +  self.datefrom.strftime("%Y%m%d") + "','" +  self.dateto.strftime("%Y%m%d") + "','"+ comp.code_base + "' "
				msg_sql = msgreportdetail

			if self.export_to =="apservices":
				msg_sql=  "exec [dbo].[IGU_ACCT_PURCHASINGREPORT2] '" +  self.datefrom.strftime("%Y%m%d") + "','" +  self.dateto.strftime("%Y%m%d") + "','"+ comp.code_base + "' "
				msg_sql = msgreportsummaryservices

			if self.export_to =="summaryaptype":
				msg_sql=  "exec [dbo].[IGU_ACCT_PURCHASINGREPORT] '" +  self.datefrom.strftime("%Y%m%d") + "','" +  self.dateto.strftime("%Y%m%d") + "','"+ comp.code_base + "' "
				msg_sql = msgreportsummary

			if self.export_to =="detail":
				msg_sql=  "exec [dbo].[IGU_ACCT_PURCHASINGREPORT_DETAIL] '" +  self.datefrom.strftime("%Y%m%d") + "','" +  self.dateto.strftime("%Y%m%d") + "','"+ comp.code_base + "' "
				msg_sql = msgreportdetail
			if self.export_to =="topgroupitem":
				msg_sql=  "exec [dbo].[IGU_ACCT_PURCHASINGREPORT_DETAIL] '" +  self.datefrom.strftime("%Y%m%d") + "','" +  self.dateto.strftime("%Y%m%d") + "','"+ comp.code_base + "' "
				msg_sql = msgreportdetail
			if self.export_to =="toppartneritem":
				msg_sql=  "exec [dbo].[IGU_ACCT_PURCHASINGREPORT_DETAIL] '" +  self.datefrom.strftime("%Y%m%d") + "','" +  self.dateto.strftime("%Y%m%d") + "','"+ comp.code_base + "' "
				msg_sql = msgreportdetail
			if self.export_to =="json":
				msg_sql = msgreportsummary
			if self.export_to =="json2":
				msg_sql = msgreportdetail
			if self.export_to =="pdf":
				msg_sql = msgreportsummary
			if self.export_to =="pdf2":
				msg_sql = msgreportdetail
			

			data = pandas.io.sql.read_sql(msg_sql,conn)
			listfinal.append(data)

 

		df = pd.concat(listfinal)
		dflist = df.values.tolist() 

		filename = filenamexls2 
		if self.export_to == "topgroupitem":
			hasil = df.groupby(["company","U_group"])["Total"].sum().reset_index() 
			hasil.sort_values(by=["company","Total"],ascending=False).to_excel(mpath + '/temp/'+ filenamexls2)

		if self.export_to == "toppartneritem":
			hasil = df.groupby(["company","U_group","cardname"])["Total"].sum().reset_index()
			hasil.sort_values(by=["Total","U_group","cardname","company"],ascending=False).to_excel(mpath + '/temp/'+ filenamexls2)

		if self.export_to =="summarypartner":
			summary = df.pivot_table(index=["company","cardname","Currency"],aggfunc=np.sum,  values=["TotalFrgn","Total"],fill_value="0",margins=True )
			summary.to_excel(mpath + '/temp/'+ filenamexls2)

		if self.export_to =="apservices":
			 
			df.to_excel(mpath + '/temp/'+ filenamexls2)

		if self.export_to =="summaryaptype":
			summary = df.pivot_table(index=["company","doctype","docs"],aggfunc=np.sum,  values=["Amount","bea_masuk","shipment","receiving","pib_pnbp","surveyor","h_biaya", "TotalLandedCost","Freight","total"],fill_value="0",margins=True )
			summary.to_excel(mpath + '/temp/'+ filenamexls2)

		if self.export_to =="summary" :
			df.to_excel(mpath + '/temp/'+ filenamexls2,index=False)

		if self.export_to =="detail" :
			df.to_excel(mpath + '/temp/'+ filenamexls2,index=False)
 
		if self.export_to =="json" :
			filename = filenamejson
			df.to_json(mpath + '/temp/'+ filenamejson,orient="records")
		if self.export_to =="json2" :
			filename = filenamejson
			df.to_json(mpath + '/temp/'+ filenamejson,orient="records")
		if self.export_to == "pdf":
			filename = filenamepdf
			
			proyeksi = self.env["cnw.awr28.jasper"].search([("name","=","purchasingreport")])
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

		if self.export_to == "pdf2":
			filename = filenamepdf
			
			proyeksi = self.env["cnw.awr28.jasper"].search([("name","=","purchasingreportdetail")])
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

 