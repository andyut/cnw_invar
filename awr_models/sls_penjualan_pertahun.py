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
import pyodbc  
from jinja2 import Environment, FileSystemLoader

class CNW_PENJUALANPERTAHUN(models.Model):
	_name           = "cnw.awr28.penjualanpertahun"
	_description    = "Model penjualanpertahun"
	company_id      = fields.Many2many('res.company', string="Company",required=True)
	name            = fields.Char("Name")
	customergroup	= fields.Char("Customer Group")
	cardcode        = fields.Char("Partner Code")
	cardname        = fields.Char("Partner Name")
	 
	salesperson     = fields.Char("Sales Person") 

	jan  			= fields.Float("Jan",digit=(19,2),default=0)
	feb  			= fields.Float("Feb",digit=(19,2),default=0)
	mar  			= fields.Float("Mar",digit=(19,2),default=0)
	apr  			= fields.Float("Apr",digit=(19,2),default=0)
	mei  			= fields.Float("Mei",digit=(19,2),default=0)
	jun  			= fields.Float("Jun",digit=(19,2),default=0)
	jul  			= fields.Float("Jul",digit=(19,2),default=0)
	ags  			= fields.Float("Ags",digit=(19,2),default=0)
	sep  			= fields.Float("Sep",digit=(19,2),default=0)
	okt  			= fields.Float("Okt",digit=(19,2),default=0)
	nov  			= fields.Float("Nov",digit=(19,2),default=0)
	des  			= fields.Float("Des",digit=(19,2),default=0) 
	total  			= fields.Float("Total",digit=(19,2),default=0) 
 


class CNW_PenjualanPertahunWizard(models.TransientModel):
	_name           = "cnw.awr28.penjualanpertahun.wizard"
	_description    = "cnw.awr28.penjualanpertahun"
	company_id      = fields.Many2many('res.company', string="Company",required=True)
	  
	dateto          = fields.Date ("Date Year", default=fields.Date.today()) 
	salesperson     = fields.Char("Sales Person")
	cardname        = fields.Char("Partner Name") 
	customergroup   = fields.Char("Customer Group") 
	item 			= fields.Char("Items")
	igroup			= fields.Char("Group Barang")
	subgroup 		= fields.Char("Sub Group barang")
	ibrand 			= fields.Char("Brand")
	export_to       = fields.Selection([('list','List View Nilai Penjualan per Customer'), ('xls', 'Excel- Nilai Penjualan per Customer   '),
											('xls2', 'Excel- Qty Penjualan per Barang '),
											('xls3','Excel- Nilai Penjualan per Sales   '),
											('xls4','Excel- Nilai Penjualan per Sales per group barang   '),
											('xls5', 'Excel- Nilai Penjualan per barang'),
											('xls6', 'Excel- Nilai Penjualan per Group barang'),
											('xls7', 'Excel- Nilai Penjualan per Group Customer'),
											('xls8', 'Excel- Nilai Penjualan per Sub Group barang'),
											('pdf', 'PDF'),
											],string='Export To', default='xls')
	filexls         = fields.Binary("File Output")    
	filenamexls     = fields.Char("File Name Output")
	
	@api.multi
	def view_penjualanpertahun(self): 
		mpath       = get_module_path('cnw_awr28')
		filenamexls = 'PENJUALANPERTAHUN_'+   self.dateto.strftime("%Y%m%d")  + '.xlsx'
		filenamepdf = 'PENJUALANPERTAHUN_'+   self.dateto.strftime("%Y%m%d")  + '.pdf'
		filename    =""
		filepath    = mpath + '/temp/'
		logo        = mpath + '/awr_template/logoigu.png'
		listfinal   = []
		cssfile     = mpath + '/awr_template/style.css'




		#global Var
		 
		igu_title = "Penjualan pertahun"
		igu_tanggal = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")
		igu_remarks = "Penjualan pertahun"
		options = {
					'page-size': 'A4',
					'orientation': 'landscape',
					}
		pd.options.display.float_format = '{:,.2f}'.format

		for comp in self.company_id:
			host        = comp.server
			database    = comp.db_name
			user        = comp.db_usr
			password    = comp.db_pass 
			conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';UID='+user+';PWD='+ password + ';TrustServerCertificate=yes')
			
			 
			#msg_sql= "exec dbo.IGU_ACT_DONOTINVOICE   '"+ self.dateto.strftime("%Y%m%d")   + "','" + comp.code_base  + "'"

			cardname = self.cardname if self.cardname else ""			 
			salesperson = self.salesperson if self.salesperson else "" 
			item = self.item if self.item else "" 
			igroup = self.igroup if self.igroup else "" 
			subgroup = self.subgroup if self.subgroup else "" 
			ibrand = self.ibrand if self.ibrand else "" 
			
			msg_sql = """
							declare @dateto varchar(20) ,
									@customer varchar(50) ,
									@salesperson varchar(50)

							set @dateto =  '""" + self.dateto.strftime("%Y")   + """'
							set @customer ='""" + cardname   + """'
							set @salesperson =  '""" + salesperson   + """' 


							select 
								'""" + str(comp.name) + """' company_id,
								a.groupname ,
								a.salesperson  ,
								a.customer ,
								sum(ijan) jan ,
								sum(ifeb) feb ,
								sum(imar) mar ,
								sum(iapr) apr ,
								sum(imay) may ,
								sum(ijun) jun ,
								sum(ijul) jul ,
								sum(iags) ags ,
								sum(isep) sep ,
								sum(iokt) okt ,
								sum(inov) nov ,
								sum(ides) des ,
								sum(Total)Total 
							from 
							(
							select d.groupname ,
								c.slpname + '-' + isnull(c.U_SlsEmpName,'-') salesperson,
								'[' + b.cardcode + '] ' + b.cardname customer ,
								sum(case month(a.docdate) when 1 then a.doctotal - a.vatsum  else 0 end) ijan ,
								sum(case month(a.docdate) when 2 then a.doctotal - a.vatsum  else 0 end) ifeb ,
								sum(case month(a.docdate) when 3 then a.doctotal - a.vatsum  else 0 end) imar ,
								sum(case month(a.docdate) when 4 then a.doctotal - a.vatsum  else 0 end) iapr ,
								sum(case month(a.docdate) when 5 then a.doctotal - a.vatsum  else 0 end) imay ,
								sum(case month(a.docdate) when 6 then a.doctotal - a.vatsum  else 0 end) ijun ,
								sum(case month(a.docdate) when 7 then a.doctotal - a.vatsum  else 0 end) ijul ,
								sum(case month(a.docdate) when 8 then a.doctotal - a.vatsum  else 0 end) iags ,
								sum(case month(a.docdate) when 9 then a.doctotal - a.vatsum  else 0 end) isep ,
								sum(case month(a.docdate) when 10 then a.doctotal - a.vatsum  else 0 end) iokt ,
								sum(case month(a.docdate) when 11 then a.doctotal - a.vatsum  else 0 end) inov ,
								sum(case month(a.docdate) when 12 then a.doctotal - a.vatsum  else 0 end) ides ,
								sum(a.doctotal - a.vatsum)    Total 

							from oinv a 
								inner join ocrd b on a.cardcode = b.cardcode 
								inner join oslp c on b.slpcode = c.slpcode 
								inner join ocrg d on b.groupcode = d.groupcode
							where 
							a.canceled = 'N'
							and year(a.docdate) = @dateto 
							and  b.cardcode + b.cardname like '%' + isnull( @customer,'') + '%'
							and  c.slpname like '%' + @salesperson + '%'

							group by d.groupname ,
									c.slpname + '-' +  isnull(c.U_SlsEmpName,'-') ,
								'[' + b.cardcode + '] ' + b.cardname
							union all 
							select d.groupname ,
								c.slpname + '-' + isnull(c.U_SlsEmpName,'-') salesperson,
								'[' + b.cardcode + '] ' + b.cardname customer ,
								-1* sum(case month(a.docdate) when 1 then a.doctotal - a.vatsum  else 0 end) ijan ,
								-1* sum(case month(a.docdate) when 2 then a.doctotal - a.vatsum  else 0 end) ifeb ,
								-1* sum(case month(a.docdate) when 3 then a.doctotal - a.vatsum  else 0 end) imar ,
								-1* sum(case month(a.docdate) when 4 then a.doctotal - a.vatsum  else 0 end) iapr ,
								-1* sum(case month(a.docdate) when 5 then a.doctotal - a.vatsum  else 0 end) imay ,
								-1* sum(case month(a.docdate) when 6 then a.doctotal - a.vatsum  else 0 end) ijun ,
								-1* sum(case month(a.docdate) when 7 then a.doctotal - a.vatsum  else 0 end) ijul ,
								-1* sum(case month(a.docdate) when 8 then a.doctotal - a.vatsum  else 0 end) iags ,
								-1* sum(case month(a.docdate) when 9 then a.doctotal - a.vatsum  else 0 end) isep ,
								-1* sum(case month(a.docdate) when 10 then a.doctotal - a.vatsum  else 0 end) iokt ,
								-1* sum(case month(a.docdate) when 11 then a.doctotal - a.vatsum  else 0 end) inov ,
								-1* sum(case month(a.docdate) when 12 then a.doctotal - a.vatsum  else 0 end) ides ,
								-1* sum(a.doctotal - a.vatsum)    Total 

							from orin a 
								inner join ocrd b on a.cardcode = b.cardcode 
								inner join oslp c on b.slpcode = c.slpcode 
								inner join ocrg d on b.groupcode = d.groupcode
							where 
							a.canceled = 'N'
							and year(a.docdate) = @dateto 
							and  b.cardcode + b.cardname like '%' + isnull( @customer,'') + '%'
							and  c.slpname like '%' + @salesperson + '%'

							group by d.groupname ,
									c.slpname + '-' +  isnull(c.U_SlsEmpName,'-') ,
								'[' + b.cardcode + '] ' + b.cardname       
							) as a 
							group by a.groupname ,
								a.salesperson ,
								a.customer			
			"""
			msg_sql2 = """
							declare @dateto varchar(20) ,
									@customer varchar(50) ,
									@salesperson varchar(50) ,
									@item varchar(100) ,
									@igroup varchar(100) ,
									@subgroup varchar(50) ,
									@brand varchar(50)

							set @dateto =  '""" + self.dateto.strftime("%Y")   + """'
							set @customer ='""" + cardname   + """'
							set @salesperson =  '""" + salesperson   + """' 
							set @item 	=  '""" + item    + """' 
							set @igroup  =  '""" + igroup    + """' 
							set @subgroup =  '""" + subgroup    + """' 
							set @brand 		= '""" + ibrand    + """' 

							select 
								'""" + str(comp.name) + """' company_id,
								u_group ,
								u_subgroup ,
								itemcode ,
								itemname ,
								uom,
								SUM(ijan) jan ,
								SUM(ifeb) feb ,
								SUM(imar) mar ,
								SUM(iapr) apr ,
								SUM(imay) may ,
								SUM(ijun) jun ,
								SUM(ijul) jul ,
								SUM(iags) ags ,
								SUM(isep) sep ,
								SUM(iokt) okt ,
								SUM(inov) nov ,
								SUM(ides) des ,
								SUM(Total)Total 
							from 
							(
							select 
									f.u_group ,
									f.u_subgroup,
									f.itemcode ,
									f.ItemName,
									f.InvntryUom uom,
								SUM(case month(a.docdate) when 1 then e.quantity   else 0 end) ijan ,
								SUM(case month(a.docdate) when 2 then e.quantity else 0 end) ifeb ,
								SUM(case month(a.docdate) when 3 then e.quantity else 0 end) imar ,
								SUM(case month(a.docdate) when 4 then e.quantity else 0 end) iapr ,
								SUM(case month(a.docdate) when 5 then e.quantity else 0 end) imay ,
								SUM(case month(a.docdate) when 6 then e.quantity else 0 end) ijun ,
								SUM(case month(a.docdate) when 7 then e.quantity else 0 end) ijul ,
								SUM(case month(a.docdate) when 8 then e.quantity else 0 end) iags ,
								SUM(case month(a.docdate) when 9 then  e.quantity else 0 end) isep ,
								SUM(case month(a.docdate) when 10 then e.quantity else 0 end) iokt ,
								SUM(case month(a.docdate) when 11 then e.quantity else 0 end) inov ,
								SUM(case month(a.docdate) when 12 then e.quantity else 0 end) ides ,
								SUM(e.quantity)    Total 

							from oinv a 
								inner join ocrd b on a.cardcode = b.cardcode 
								inner join oslp c on b.slpcode = c.slpcode 
								inner join ocrg d on b.groupcode = d.groupcode
								inner join inv1 e on a.docentry = e.docentry 
								inner join oitm f on e.itemcode = f.itemcode 
							where 
							a.canceled = 'N'
							and year(a.docdate) = @dateto 
							and  b.cardcode + b.cardname like '%' + isnull( @customer,'') + '%'
							and  c.slpname like '%' + @salesperson + '%'
							and  f.itemcode + f.itemname like  '%' + @salesperson + '%'

							group by    f.u_group ,
										f.u_subgroup,
										f.itemcode ,
										f.ItemName,
										f.InvntryUom
							union all 
							select      f.u_group ,
										f.u_subgroup,
										f.itemcode ,
										f.ItemName,
										f.InvntryUom ,
								-1* SUM(case month(a.docdate) when 1 then e.quantity else 0 end) ijan ,
								-1* SUM(case month(a.docdate) when 2 then e.quantity else 0 end) ifeb ,
								-1* SUM(case month(a.docdate) when 3 then e.quantity else 0 end) imar ,
								-1* SUM(case month(a.docdate) when 4 then e.quantity else 0 end) iapr ,
								-1* SUM(case month(a.docdate) when 5 then e.quantity else 0 end) imay ,
								-1* SUM(case month(a.docdate) when 6 then e.quantity else 0 end) ijun ,
								-1* SUM(case month(a.docdate) when 7 then e.quantity else 0 end) ijul ,
								-1* SUM(case month(a.docdate) when 8 then e.quantity else 0 end) iags ,
								-1* SUM(case month(a.docdate) when 9 then e.quantity else 0 end) isep ,
								-1* SUM(case month(a.docdate) when 10 then e.quantity else 0 end) iokt ,
								-1* SUM(case month(a.docdate) when 11 then e.quantity else 0 end) inov ,
								-1* SUM(case month(a.docdate) when 12 then e.quantity else 0 end) ides ,
								-1* SUM(e.quantity)    Total 

							from orin a 
								inner join ocrd b on a.cardcode = b.cardcode 
								inner join oslp c on b.slpcode = c.slpcode 
								inner join ocrg d on b.groupcode = d.groupcode
								inner join rin1 e on a.docentry = e.docentry 
								inner join oitm f on e.itemcode = f.itemcode 
							where 
							a.canceled = 'N'
							and year(a.docdate) = @dateto 
							and  b.cardcode + b.cardname like '%' + isnull( @customer,'') + '%'
							and  c.slpname like '%' + @salesperson + '%'

							group by    f.u_group ,
										f.u_subgroup,
										f.itemcode ,
										f.ItemName,
										f.InvntryUom
							) as a 
							group by    u_group ,
										u_subgroup ,
										itemcode ,
										itemname ,
										uom	
			"""
			msg_sql3 = """
							declare @dateto varchar(20) ,
									@customer varchar(50) ,
									@salesperson varchar(50),
									@item varchar(100) ,
									@igroup varchar(100) ,
									@subgroup varchar(50) ,
									@brand varchar(50)

							set @dateto =  '""" + self.dateto.strftime("%Y")   + """'
							set @customer ='""" + cardname   + """'
							set @salesperson =  '""" + salesperson   + """' 

							set @item 	=  '""" + item    + """' 
							set @igroup  =  '""" + igroup    + """' 
							set @subgroup =  '""" + subgroup    + """' 
							set @brand 		= '""" + ibrand    + """' 							

							select 
								'""" + str(comp.name) + """' company_id,
								SalesGroup,
								SalesPerson,
								SUM(ijan) jan ,
								SUM(ifeb) feb ,
								SUM(imar) mar ,
								SUM(iapr) apr ,
								SUM(imay) may ,
								SUM(ijun) jun ,
								SUM(ijul) jul ,
								SUM(iags) ags ,
								SUM(isep) sep ,
								SUM(iokt) okt ,
								SUM(inov) nov ,
								SUM(ides) des ,
								SUM(Total)Total 
							from 
							(
							select  isnull(c.memo,'NoGroup') SalesGroup,
									c.slpName + ' ' + isnull(c.u_slsEmpName,'') SalesPerson,
								SUM(case month(a.docdate) when 1 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )   else 0 end) ijan ,
								SUM(case month(a.docdate) when 2 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ifeb ,
								SUM(case month(a.docdate) when 3 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) imar ,
								SUM(case month(a.docdate) when 4 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iapr ,
								SUM(case month(a.docdate) when 5 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) imay ,
								SUM(case month(a.docdate) when 6 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ijun ,
								SUM(case month(a.docdate) when 7 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ijul ,
								SUM(case month(a.docdate) when 8 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iags ,
								SUM(case month(a.docdate) when 9 then  e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) isep ,
								SUM(case month(a.docdate) when 10 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iokt ,
								SUM(case month(a.docdate) when 11 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) inov ,
								SUM(case month(a.docdate) when 12 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ides ,
								SUM(e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ))    Total 

							from oinv a 
								inner join ocrd b on a.cardcode = b.cardcode 
								inner join oslp c on b.slpcode = c.slpcode 
								inner join ocrg d on b.groupcode = d.groupcode
								inner join inv1 e on a.docentry = e.docentry 
								inner join oitm f on e.itemcode = f.itemcode 
							where 
							a.canceled = 'N'
							and year(a.docdate) = @dateto 
							and  b.cardcode + b.cardname like '%' + isnull( @customer,'') + '%'
							and  c.slpname like '%' + @salesperson + '%'

							group by    isnull(c.memo,'NoGroup') ,
										c.slpName + ' ' + isnull(c.u_slsEmpName,'') 
							union all 
							select      isnull(c.memo,'NoGroup') ,
										c.slpName + ' ' + isnull(c.u_slsEmpName,'')  ,
								-1* SUM(case month(a.docdate) when 1 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ijan ,
								-1* SUM(case month(a.docdate) when 2 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ifeb ,
								-1* SUM(case month(a.docdate) when 3 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) imar ,
								-1* SUM(case month(a.docdate) when 4 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iapr ,
								-1* SUM(case month(a.docdate) when 5 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) imay ,
								-1* SUM(case month(a.docdate) when 6 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ijun ,
								-1* SUM(case month(a.docdate) when 7 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ijul ,
								-1* SUM(case month(a.docdate) when 8 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iags ,
								-1* SUM(case month(a.docdate) when 9 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) isep ,
								-1* SUM(case month(a.docdate) when 10 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iokt ,
								-1* SUM(case month(a.docdate) when 11 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) inov ,
								-1* SUM(case month(a.docdate) when 12 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ides ,
								-1* SUM(e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ))    Total 

							from orin a 
								inner join ocrd b on a.cardcode = b.cardcode 
								inner join oslp c on b.slpcode = c.slpcode 
								inner join ocrg d on b.groupcode = d.groupcode
								inner join rin1 e on a.docentry = e.docentry 
								inner join oitm f on e.itemcode = f.itemcode 
							where 
							a.canceled = 'N'
							and year(a.docdate) = @dateto 
							and  b.cardcode + b.cardname like '%' + isnull( @customer,'') + '%'
							and  c.slpname like '%' + @salesperson + '%'

							group by    isnull(c.memo,'NoGroup') ,
										c.slpName + ' ' + isnull(c.u_slsEmpName,'') 
							) as a 
							group by    SalesGroup,
								SalesPerson
							order by    SalesGroup,
								SalesPerson
			"""			
			msg_sql4 = """
							declare @dateto varchar(20) ,
									@customer varchar(50) ,
									@salesperson varchar(50),
									@item varchar(100) ,
									@igroup varchar(100) ,
									@subgroup varchar(50) ,
									@brand varchar(50)

							set @dateto =  '""" + self.dateto.strftime("%Y")   + """'
							set @customer ='""" + cardname   + """'
							set @salesperson =  '""" + salesperson   + """' 
							
							set @item 	=  '""" + item    + """' 
							set @igroup  =  '""" + igroup    + """' 
							set @subgroup =  '""" + subgroup    + """' 
							set @brand 		= '""" + ibrand    + """' 

							select 
								'""" + str(comp.name) + """' company_id,
								SalesGroup,
								SalesPerson,
								u_group,
								SUM(ijan) jan ,
								SUM(ifeb) feb ,
								SUM(imar) mar ,
								SUM(iapr) apr ,
								SUM(imay) may ,
								SUM(ijun) jun ,
								SUM(ijul) jul ,
								SUM(iags) ags ,
								SUM(isep) sep ,
								SUM(iokt) okt ,
								SUM(inov) nov ,
								SUM(ides) des ,
								SUM(Total)Total 
							from 
							(
							select  isnull(c.memo,'NoGroup') SalesGroup,
									c.slpName + ' ' + isnull(c.u_slsEmpName,'') SalesPerson,
									f.u_group u_group,
								SUM(case month(a.docdate) when 1 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )  else 0 end) ijan ,
								SUM(case month(a.docdate) when 2 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ifeb ,
								SUM(case month(a.docdate) when 3 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) imar ,
								SUM(case month(a.docdate) when 4 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iapr ,
								SUM(case month(a.docdate) when 5 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) imay ,
								SUM(case month(a.docdate) when 6 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ijun ,
								SUM(case month(a.docdate) when 7 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ijul ,
								SUM(case month(a.docdate) when 8 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iags ,
								SUM(case month(a.docdate) when 9 then  e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) isep ,
								SUM(case month(a.docdate) when 10 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iokt ,
								SUM(case month(a.docdate) when 11 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) inov ,
								SUM(case month(a.docdate) when 12 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ides ,
								SUM( e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ))    Total 

							from oinv a 
								inner join ocrd b on a.cardcode = b.cardcode 
								inner join oslp c on b.slpcode = c.slpcode 
								inner join ocrg d on b.groupcode = d.groupcode
								inner join inv1 e on a.docentry = e.docentry 
								inner join oitm f on e.itemcode = f.itemcode 
							where 
							a.canceled = 'N'
							and year(a.docdate) = @dateto 
							and  b.cardcode + b.cardname like '%' + isnull( @customer,'') + '%'
							and  c.slpname like '%' + @salesperson + '%'

							group by    isnull(c.memo,'NoGroup') ,
										c.slpName + ' ' + isnull(c.u_slsEmpName,'') ,
										f.u_group 
							union all 
							select      isnull(c.memo,'NoGroup') ,
										c.slpName + ' ' + isnull(c.u_slsEmpName,'')  ,
										f.u_group ,
								-1* SUM(case month(a.docdate) when 1 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ijan ,
								-1* SUM(case month(a.docdate) when 2 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ifeb ,
								-1* SUM(case month(a.docdate) when 3 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) imar ,
								-1* SUM(case month(a.docdate) when 4 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iapr ,
								-1* SUM(case month(a.docdate) when 5 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) imay ,
								-1* SUM(case month(a.docdate) when 6 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ijun ,
								-1* SUM(case month(a.docdate) when 7 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ijul ,
								-1* SUM(case month(a.docdate) when 8 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iags ,
								-1* SUM(case month(a.docdate) when 9 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) isep ,
								-1* SUM(case month(a.docdate) when 10 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iokt ,
								-1* SUM(case month(a.docdate) when 11 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) inov ,
								-1* SUM(case month(a.docdate) when 12 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ides ,
								-1* SUM( e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ))    Total 

							from orin a 
								inner join ocrd b on a.cardcode = b.cardcode 
								inner join oslp c on b.slpcode = c.slpcode 
								inner join ocrg d on b.groupcode = d.groupcode
								inner join rin1 e on a.docentry = e.docentry 
								inner join oitm f on e.itemcode = f.itemcode 
							where 
							a.canceled = 'N'
							and year(a.docdate) = @dateto 
							and  b.cardcode + b.cardname like '%' + isnull( @customer,'') + '%'
							and  c.slpname like '%' + @salesperson + '%'

							group by    isnull(c.memo,'NoGroup') ,
										c.slpName + ' ' + isnull(c.u_slsEmpName,'') ,
										f.u_group 
							) as a 
							group by    SalesGroup,
								SalesPerson ,
								u_group 
							order by    SalesGroup,
								SalesPerson,
								u_group 
			"""			 
			msg_sql5 = """
							declare @dateto 		varchar(20) ,
									@customer 		varchar(50) ,
									@salesperson 	varchar(50) ,
									@item varchar(100) ,
									@igroup varchar(100) ,
									@subgroup varchar(50) ,
									@brand varchar(50)

							set @dateto =  '""" + self.dateto.strftime("%Y")   + """'
							set @customer ='""" + cardname   + """'
							set @salesperson =  '""" + salesperson   + """' 

							set @item 	=  '""" + item    + """' 
							set @igroup  =  '""" + igroup    + """' 
							set @subgroup =  '""" + subgroup    + """' 
							set @brand 		= '""" + ibrand    + """' 

							select 
									'""" + str(comp.name) + """' company_id,
									u_group ,
									u_subgroup,
									itemcode ,
									ItemName,
									uom,
									SUM(ijan) jan ,
									SUM(ifeb) feb ,
									SUM(imar) mar ,
									SUM(iapr) apr ,
									SUM(imay) may ,
									SUM(ijun) jun ,
									SUM(ijul) jul ,
									SUM(iags) ags ,
									SUM(isep) sep ,
									SUM(iokt) okt ,
									SUM(inov) nov ,
									SUM(ides) des ,
									SUM(Total)Total 
								from 
								(
								select  f.u_group ,
										f.u_subgroup,
										f.itemcode ,
										f.ItemName,
										f.InvntryUom uom,
									SUM(case month(a.docdate) when 1 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )   else 0 end) ijan ,
									SUM(case month(a.docdate) when 2 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ifeb ,
									SUM(case month(a.docdate) when 3 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) imar ,
									SUM(case month(a.docdate) when 4 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iapr ,
									SUM(case month(a.docdate) when 5 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) imay ,
									SUM(case month(a.docdate) when 6 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ijun ,
									SUM(case month(a.docdate) when 7 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ijul ,
									SUM(case month(a.docdate) when 8 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iags ,
									SUM(case month(a.docdate) when 9 then  e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) isep ,
									SUM(case month(a.docdate) when 10 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iokt ,
									SUM(case month(a.docdate) when 11 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) inov ,
									SUM(case month(a.docdate) when 12 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ides ,
									SUM(e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) )    Total 

								from oinv a 
									inner join ocrd b on a.cardcode = b.cardcode 
									inner join oslp c on b.slpcode = c.slpcode 
									inner join ocrg d on b.groupcode = d.groupcode
									inner join inv1 e on a.docentry = e.docentry 
									inner join oitm f on e.itemcode = f.itemcode 
								where 
								a.canceled = 'N'
								and year(a.docdate) = @dateto 
								and  b.cardcode + b.cardname like '%' + isnull( @customer,'') + '%'
								and  c.slpname like '%' + @salesperson + '%'

								group by f.u_group ,
										f.u_subgroup,
										f.itemcode ,
										f.ItemName,
										f.InvntryUom 
								union all 
								select       f.u_group ,
										f.u_subgroup,
										f.itemcode ,
										f.ItemName,
										f.InvntryUom  ,
									-1* SUM(case month(a.docdate) when 1 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )  else 0 end) ijan ,
									-1* SUM(case month(a.docdate) when 2 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ifeb ,
									-1* SUM(case month(a.docdate) when 3 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) imar ,
									-1* SUM(case month(a.docdate) when 4 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iapr ,
									-1* SUM(case month(a.docdate) when 5 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) imay ,
									-1* SUM(case month(a.docdate) when 6 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ijun ,
									-1* SUM(case month(a.docdate) when 7 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ijul ,
									-1* SUM(case month(a.docdate) when 8 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iags ,
									-1* SUM(case month(a.docdate) when 9 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )  else 0 end) isep ,
									-1* SUM(case month(a.docdate) when 10 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iokt ,
									-1* SUM(case month(a.docdate) when 11 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) inov ,
									-1* SUM(case month(a.docdate) when 12 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ides ,
									-1* SUM( e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) )    Total 

								from orin a 
									inner join ocrd b on a.cardcode = b.cardcode 
									inner join oslp c on b.slpcode = c.slpcode 
									inner join ocrg d on b.groupcode = d.groupcode
									inner join rin1 e on a.docentry = e.docentry 
									inner join oitm f on e.itemcode = f.itemcode 
								where 
								a.canceled = 'N'
								and year(a.docdate) = @dateto 
								and  b.cardcode + b.cardname like '%' + isnull( @customer,'') + '%'
								and  c.slpname like '%' + @salesperson + '%'

								group by     f.u_group ,
										f.u_subgroup,
										f.itemcode ,
										f.ItemName,
										f.InvntryUom 
								) as a 
								group by     u_group ,
									u_subgroup,
									itemcode ,
									ItemName,
									uom
								order by      u_group ,
									u_subgroup,
									itemcode ,
									ItemName,
									uom 
			"""
			msg_sql6 = """
							declare @dateto 		varchar(20) ,
									@customer 		varchar(50) ,
									@salesperson 	varchar(50) ,
									@item varchar(100) ,
									@igroup varchar(100) ,
									@subgroup varchar(50) ,
									@brand varchar(50)

							set @dateto =  '""" + self.dateto.strftime("%Y")   + """'
							set @customer ='""" + cardname   + """'
							set @salesperson =  '""" + salesperson   + """' 

							set @item 	=  '""" + item    + """' 
							set @igroup  =  '""" + igroup    + """' 
							set @subgroup =  '""" + subgroup    + """' 
							set @brand 		= '""" + ibrand    + """' 

							select 
								'""" + str(comp.name) + """' company_id,
								u_group  ,
								SUM(ijan) jan ,
								SUM(ifeb) feb ,
								SUM(imar) mar ,
								SUM(iapr) apr ,
								SUM(imay) may ,
								SUM(ijun) jun ,
								SUM(ijul) jul ,
								SUM(iags) ags ,
								SUM(isep) sep ,
								SUM(iokt) okt ,
								SUM(inov) nov ,
								SUM(ides) des ,
								SUM(Total)Total 
							from 
							(
							select  f.u_group ,
								SUM(case month(a.docdate) when 1 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )   else 0 end) ijan ,
								SUM(case month(a.docdate) when 2 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ifeb ,
								SUM(case month(a.docdate) when 3 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) imar ,
								SUM(case month(a.docdate) when 4 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iapr ,
								SUM(case month(a.docdate) when 5 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) imay ,
								SUM(case month(a.docdate) when 6 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ijun ,
								SUM(case month(a.docdate) when 7 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ijul ,
								SUM(case month(a.docdate) when 8 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iags ,
								SUM(case month(a.docdate) when 9 then  e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) isep ,
								SUM(case month(a.docdate) when 10 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iokt ,
								SUM(case month(a.docdate) when 11 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) inov ,
								SUM(case month(a.docdate) when 12 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ides ,
								SUM( e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) )    Total 

							from oinv a 
								inner join ocrd b on a.cardcode = b.cardcode 
								inner join oslp c on b.slpcode = c.slpcode 
								inner join ocrg d on b.groupcode = d.groupcode
								inner join inv1 e on a.docentry = e.docentry 
								inner join oitm f on e.itemcode = f.itemcode 
							where 
							a.canceled = 'N'
							and year(a.docdate) = @dateto 
							and  b.cardcode + b.cardname like '%' + isnull( @customer,'') + '%'
							and  c.slpname like '%' + @salesperson + '%'

							group by f.u_group 
							union all 
							select       f.u_group  ,
								-1* SUM(case month(a.docdate) when 1 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ijan ,
								-1* SUM(case month(a.docdate) when 2 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ifeb ,
								-1* SUM(case month(a.docdate) when 3 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) imar ,
								-1* SUM(case month(a.docdate) when 4 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iapr ,
								-1* SUM(case month(a.docdate) when 5 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) imay ,
								-1* SUM(case month(a.docdate) when 6 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ijun ,
								-1* SUM(case month(a.docdate) when 7 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ijul ,
								-1* SUM(case month(a.docdate) when 8 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iags ,
								-1* SUM(case month(a.docdate) when 9 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) isep ,
								-1* SUM(case month(a.docdate) when 10 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iokt ,
								-1* SUM(case month(a.docdate) when 11 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) inov ,
								-1* SUM(case month(a.docdate) when 12 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ides ,
								-1* SUM(e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) )    Total 

							from orin a 
								inner join ocrd b on a.cardcode = b.cardcode 
								inner join oslp c on b.slpcode = c.slpcode 
								inner join ocrg d on b.groupcode = d.groupcode
								inner join rin1 e on a.docentry = e.docentry 
								inner join oitm f on e.itemcode = f.itemcode 
							where 
							a.canceled = 'N'
							and year(a.docdate) = @dateto 
							and  b.cardcode + b.cardname like '%' + isnull( @customer,'') + '%'
							and  c.slpname like '%' + @salesperson + '%'

							group by     f.u_group  
							) as a 
							group by     u_group  
							order by      u_group 
			"""
			msg_sql7 = """
							declare @dateto 		varchar(20) ,
									@customer 		varchar(50) ,
									@salesperson 	varchar(50) ,
									@item varchar(100) ,
									@igroup varchar(100) ,
									@subgroup varchar(50) ,
									@brand varchar(50)

							set @dateto =  '""" + self.dateto.strftime("%Y")   + """'
							set @customer ='""" + cardname   + """'
							set @salesperson =  '""" + salesperson   + """' 

							set @item 	=  '""" + item    + """' 
							set @igroup  =  '""" + igroup    + """' 
							set @subgroup =  '""" + subgroup    + """' 
							set @brand 		= '""" + ibrand    + """' 

							select 
								'""" + str(comp.name) + """' company_id,
								groupname  ,
								SUM(ijan) jan ,
								SUM(ifeb) feb ,
								SUM(imar) mar ,
								SUM(iapr) apr ,
								SUM(imay) may ,
								SUM(ijun) jun ,
								SUM(ijul) jul ,
								SUM(iags) ags ,
								SUM(isep) sep ,
								SUM(iokt) okt ,
								SUM(inov) nov ,
								SUM(ides) des ,
								SUM(Total)Total 
							from 
							(
							select  d.groupname ,
								SUM(case month(a.docdate) when 1 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )  else 0 end) ijan ,
								SUM(case month(a.docdate) when 2 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )  else 0 end) ifeb ,
								SUM(case month(a.docdate) when 3 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) imar ,
								SUM(case month(a.docdate) when 4 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iapr ,
								SUM(case month(a.docdate) when 5 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) imay ,
								SUM(case month(a.docdate) when 6 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ijun ,
								SUM(case month(a.docdate) when 7 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ijul ,
								SUM(case month(a.docdate) when 8 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iags ,
								SUM(case month(a.docdate) when 9 then  e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) isep ,
								SUM(case month(a.docdate) when 10 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iokt ,
								SUM(case month(a.docdate) when 11 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )  else 0 end) inov ,
								SUM(case month(a.docdate) when 12 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ides ,
								SUM( e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) )    Total 

							from oinv a 
								inner join ocrd b on a.cardcode = b.cardcode 
								inner join oslp c on b.slpcode = c.slpcode 
								inner join ocrg d on b.groupcode = d.groupcode
								inner join inv1 e on a.docentry = e.docentry 
								inner join oitm f on e.itemcode = f.itemcode 
							where 
							a.canceled = 'N'
							and year(a.docdate) = @dateto 
							and  b.cardcode + b.cardname like '%' + isnull( @customer,'') + '%'
							and  c.slpname like '%' + @salesperson + '%'

							group by  d.groupname
							union all 
							select        d.groupname,
								-1* SUM(case month(a.docdate) when 1 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )  else 0 end) ijan ,
								-1* SUM(case month(a.docdate) when 2 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )  else 0 end) ifeb ,
								-1* SUM(case month(a.docdate) when 3 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )  else 0 end) imar ,
								-1* SUM(case month(a.docdate) when 4 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )  else 0 end) iapr ,
								-1* SUM(case month(a.docdate) when 5 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )  else 0 end) imay ,
								-1* SUM(case month(a.docdate) when 6 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )  else 0 end) ijun ,
								-1* SUM(case month(a.docdate) when 7 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )  else 0 end) ijul ,
								-1* SUM(case month(a.docdate) when 8 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iags ,
								-1* SUM(case month(a.docdate) when 9 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )  else 0 end) isep ,
								-1* SUM(case month(a.docdate) when 10 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )  else 0 end) iokt ,
								-1* SUM(case month(a.docdate) when 11 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) inov ,
								-1* SUM(case month(a.docdate) when 12 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )  else 0 end) ides ,
								-1* SUM( e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )  )    Total 

							from orin a 
								inner join ocrd b on a.cardcode = b.cardcode 
								inner join oslp c on b.slpcode = c.slpcode 
								inner join ocrg d on b.groupcode = d.groupcode
								inner join rin1 e on a.docentry = e.docentry 
								inner join oitm f on e.itemcode = f.itemcode 
							where 
							a.canceled = 'N'
							and year(a.docdate) = @dateto 
							and  b.cardcode + b.cardname like '%' + isnull( @customer,'') + '%'
							and  c.slpname like '%' + @salesperson + '%'

							group by      d.groupname
							) as a 
							group by       groupname
							order by       groupname
			"""
			msg_sql8 = """
							declare @dateto 		varchar(20) ,
									@customer 		varchar(50) ,
									@salesperson 	varchar(50) ,
									@item varchar(100) ,
									@igroup varchar(100) ,
									@subgroup varchar(50) ,
									@brand varchar(50)

							set @dateto =  '""" + self.dateto.strftime("%Y")   + """'
							set @customer ='""" + cardname   + """'
							set @salesperson =  '""" + salesperson   + """' 

							set @item 	=  '""" + item    + """' 
							set @igroup  =  '""" + igroup    + """' 
							set @subgroup =  '""" + subgroup    + """' 
							set @brand 		= '""" + ibrand    + """' 

							select 
								'""" + str(comp.name) + """' company_id,
								u_group  ,
								u_subgroup  ,
								SUM(ijan) jan ,
								SUM(ifeb) feb ,
								SUM(imar) mar ,
								SUM(iapr) apr ,
								SUM(imay) may ,
								SUM(ijun) jun ,
								SUM(ijul) jul ,
								SUM(iags) ags ,
								SUM(isep) sep ,
								SUM(iokt) okt ,
								SUM(inov) nov ,
								SUM(ides) des ,
								SUM(Total)Total 
							from 
							(
							select  f.u_group ,
								f.u_subgroup  ,
								SUM(case month(a.docdate) when 1 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )  else 0 end) ijan ,
								SUM(case month(a.docdate) when 2 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )  else 0 end) ifeb ,
								SUM(case month(a.docdate) when 3 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) imar ,
								SUM(case month(a.docdate) when 4 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iapr ,
								SUM(case month(a.docdate) when 5 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) imay ,
								SUM(case month(a.docdate) when 6 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ijun ,
								SUM(case month(a.docdate) when 7 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ijul ,
								SUM(case month(a.docdate) when 8 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iags ,
								SUM(case month(a.docdate) when 9 then  e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) isep ,
								SUM(case month(a.docdate) when 10 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iokt ,
								SUM(case month(a.docdate) when 11 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )  else 0 end) inov ,
								SUM(case month(a.docdate) when 12 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) ides ,
								SUM( e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) )    Total 

							from oinv a 
								inner join ocrd b on a.cardcode = b.cardcode 
								inner join oslp c on b.slpcode = c.slpcode 
								inner join ocrg d on b.groupcode = d.groupcode
								inner join inv1 e on a.docentry = e.docentry 
								inner join oitm f on e.itemcode = f.itemcode 
							where 
							a.canceled = 'N'
							and year(a.docdate) = @dateto 
							and  b.cardcode + b.cardname like '%' + isnull( @customer,'') + '%'
							and  c.slpname like '%' + @salesperson + '%'

							group by f.u_group  ,
									 f.u_subgroup  

							union all 
							select        								
								f.u_group  ,
								f.u_subgroup  ,
								-1* SUM(case month(a.docdate) when 1 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )  else 0 end) ijan ,
								-1* SUM(case month(a.docdate) when 2 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )  else 0 end) ifeb ,
								-1* SUM(case month(a.docdate) when 3 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )  else 0 end) imar ,
								-1* SUM(case month(a.docdate) when 4 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )  else 0 end) iapr ,
								-1* SUM(case month(a.docdate) when 5 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )  else 0 end) imay ,
								-1* SUM(case month(a.docdate) when 6 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )  else 0 end) ijun ,
								-1* SUM(case month(a.docdate) when 7 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )  else 0 end) ijul ,
								-1* SUM(case month(a.docdate) when 8 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) iags ,
								-1* SUM(case month(a.docdate) when 9 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )  else 0 end) isep ,
								-1* SUM(case month(a.docdate) when 10 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )  else 0 end) iokt ,
								-1* SUM(case month(a.docdate) when 11 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum ) else 0 end) inov ,
								-1* SUM(case month(a.docdate) when 12 then e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )  else 0 end) ides ,
								-1* SUM( e.linetotal - ((e.linetotal / ( a.doctotal -a.vatsum+a.DiscSum))*a.DiscSum )  )    Total 

							from orin a 
								inner join ocrd b on a.cardcode = b.cardcode 
								inner join oslp c on b.slpcode = c.slpcode 
								inner join ocrg d on b.groupcode = d.groupcode
								inner join rin1 e on a.docentry = e.docentry 
								inner join oitm f on e.itemcode = f.itemcode 
							where 
							a.canceled = 'N'
							and year(a.docdate) = @dateto 
							and  b.cardcode + b.cardname like '%' + isnull( @customer,'') + '%'
							and  c.slpname like '%' + @salesperson + '%'

							group by     f.u_group,
								f.u_subgroup 
							) as a 
							group by
								u_group  ,
								u_subgroup   

							order by       	u_group,
											u_subgroup   
			"""			
			if self.export_to == "list":
				sql = msg_sql
			elif self.export_to == "xls":
				sql = msg_sql
			elif self.export_to == "xls2":
				sql = msg_sql2
			elif self.export_to == "xls3":
				sql = msg_sql3
			elif self.export_to == "xls4":
				sql = msg_sql4
			elif self.export_to == "xls5":
				sql = msg_sql5
			elif self.export_to == "xls6":
				sql = msg_sql6
			elif self.export_to == "xls7":
				sql = msg_sql7
			elif self.export_to == "xls8":
				sql = msg_sql8
			elif self.export_to == "pdf":
				sql = msg_sql
			 

			data = pandas.io.sql.read_sql(sql,conn)
			listfinal.append(data)

		df = pd.concat(listfinal)
		
		
		datalist2 = df.values.tolist()



		#print(datalist2)
		if self.export_to=="list":

			self.env.cr.execute ("""DELETE FROM cnw_awr28_penjualanpertahun WHERE write_uid =""" + str(self.env.user.id) + """ """ ) 
			#if listinuser :


			for line in datalist2:

				self.env["cnw.awr28.penjualanpertahun"].create({ 
											"company_id"		: line[0],
											"customergroup"		: line[1],
											"salesperson"		: line[2],
											"cardname"			: line[3],
											"jan"				: line[4],
											"feb"				: line[5],
											"mar"				: line[6],
											"apr"				: line[7],
											"mei"				: line[8],
											"jun"				: line[9],
											"jul"				: line[10],
											"ags"				: line[11],
											"sep"				: line[12],
											"okt"				: line[13],
											"nov"				: line[14],
											"des" 				: line[15],
											"total"				: line[16] 
											})
			return {
				"type": "ir.actions.act_window",
				"res_model": "cnw.awr28.penjualanpertahun",  
				#"view_id":view_do_list_tree, 
				"view_mode":"tree,pivot",
				"act_window_id":"cnw_awr28_penjualanpertahun_action"}


		elif self.export_to=="xls" :
			df.loc['Total'] = df.select_dtypes(pd.np.number).sum().reindex(df.columns, fill_value='')
			filename = filenamexls 
			df.to_excel(mpath + '/temp/'+ filenamexls)  

		elif self.export_to =="pdf" : 
				# JINJA 2 Template
				
			filename = filenamepdf
			env = Environment(loader=FileSystemLoader(mpath + '/awr_template/'))
			template = env.get_template("awr_template_report.html")            
			template_var = {"logo":logo,
							"igu_title" :igu_title,
							"igu_tanggal" :igu_tanggal ,
							"igu_remarks" :igu_remarks ,
							"detail": df.to_html(index=True,float_format='{:20,.2f}'.format)}
			
			html_out = template.render(template_var)
			pdfkit.from_string(html_out,mpath + '/temp/'+ filenamepdf,options=options,css=cssfile) 

		elif self.export_to =="xls2" :
			df.loc['Total'] = df.select_dtypes(pd.np.number).sum().reindex(df.columns, fill_value='')
			filename = filenamexls 
			df.to_excel(mpath + '/temp/'+ filenamexls)  			

		elif self.export_to =="xls3" :
			df.loc['Total'] = df.select_dtypes(pd.np.number).sum().reindex(df.columns, fill_value='')
			filename = filenamexls 
			df.to_excel(mpath + '/temp/'+ filenamexls)  			

		elif self.export_to =="xls4" :
			df.loc['Total'] = df.select_dtypes(pd.np.number).sum().reindex(df.columns, fill_value='')
			filename = filenamexls 
			df.to_excel(mpath + '/temp/'+ filenamexls)  			

		elif self.export_to =="xls5" :
			df.loc['Total'] = df.select_dtypes(pd.np.number).sum().reindex(df.columns, fill_value='')
			filename = filenamexls 
			df.to_excel(mpath + '/temp/'+ filenamexls)  			

		elif self.export_to =="xls6" :
			df.loc['Total'] = df.select_dtypes(pd.np.number).sum().reindex(df.columns, fill_value='')
			filename = filenamexls 
			df.to_excel(mpath + '/temp/'+ filenamexls)  			

		elif self.export_to =="xls7" :
			df.loc['Total'] = df.select_dtypes(pd.np.number).sum().reindex(df.columns, fill_value='')
			filename = filenamexls 
			df.to_excel(mpath + '/temp/'+ filenamexls)  			
		elif self.export_to =="xls8" :
			df.loc['Total'] = df.select_dtypes(pd.np.number).sum().reindex(df.columns, fill_value='')
			filename = filenamexls 
			df.to_excel(mpath + '/temp/'+ filenamexls)  
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

 