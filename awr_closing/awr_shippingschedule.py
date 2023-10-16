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


class AWR_ShippingScheduleReport(models.TransientModel):
	_name           = "cnw.awr28.shippingschedule"
	_description    = "cnw.awr28.shippingschedule"
	company_id      = fields.Many2many('res.company', string="Company",required=True)
	datefrom        = fields.Date ("Date From", default=fields.Date.today()) 
	dateto          = fields.Date ("Date To", default=fields.Date.today()) 
	partner         = fields.Char("Partner")
	item            = fields.Char("Item")
	igroup          = fields.Selection([ ('','All'),('Lokal', 'Lokal'), ('Import', 'Import'), ('Cabang', 'Cabang'), ('Group', 'Group'),],string='Vendor Group', default='')
	
	export_to       = fields.Selection([ ('xls', 'Excel'),('xlssummary', 'Excel Summary'),],string='Export To', default='xlssummary')
	filexls         = fields.Binary("File Output")    
	filenamexls     = fields.Char("File Name Output")
	
	
	
	def view_pl(self): 
		mpath           = get_module_path('cnw_awr28')
		filename        = 'ShippingSchedule'+ self.env.user.company_id.db_name +  self.dateto.strftime("%Y%m%d")  + '.xlsx'
		filenamexls     = 'ShippingSchedule'+ self.env.user.company_id.db_name +   self.dateto.strftime("%Y%m%d")  + '.xlsx'
		filenamexls2    = 'ShippingSchedule'+  self.env.user.company_id.db_name +  self.dateto.strftime("%Y%m%d")  + '.xlsx'
		filenamepdf     = 'ShippingSchedule'+  self.env.user.company_id.db_name +  self.dateto.strftime("%Y%m%d")  + '.pdf'
		filepath        = mpath + '/temp/'+ filename
		logo            = mpath + '/awr_template/logoigu.png' 
		listfinal       = []
		options         = {
							'orientation': 'portrait',
							}        
		igu_tanggal     = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")

		pd.options.display.float_format = '{:,.2f}'.format        

		partner     	= self.partner if self.partner else ""
		item        	= self.item if self.item else ""
		igroup      	= self.igroup if self.igroup else ""
		
		for comp in self.company_id:

			host        = comp.server2
			database    = comp.db_name2
			user        = comp.db_usr2
			password    = comp.db_pass2
			database2   = comp.db_name
			#conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';UID='+user+';PWD='+ password + ';TrustServerCertificate=yes')
			conn = pymssql.connect(host=host, user=user, password=password, database=database)
			cursor      = conn.cursor()


			if self.export_to =="xls":
				msg_sql=  """
								declare @datefrom varchar(10) , @dateto varchar(10), @partner varchar(100) , @item varchar(50), @igroup varchar(50)

								set @datefrom = '""" +  self.datefrom.strftime("%Y%m%d") + """'
								set @dateto = '""" +  self.dateto.strftime("%Y%m%d") + """'
								set @partner = '""" +  partner + """'
								set @item = '""" +  item + """'
								set @igroup = '""" +  igroup + """'

								select   
										'"""+ comp.code_base + """' + convert(varchar,a.Id) + '_' + convert(varchar,b.Id) id,
										'"""+ comp.code_base + """' Company,
										a.TransNo ,
										c.docnum PO_SAP,
									convert(varchar,a.transDate,23) Payment, 
									
									convert(varchar,a.DueDate,23) ETA, 
									a.BpCode  CardCode,
									a.BpName CardName, 
									a.refNo ,
									a.Container ,
									a.Vessel ,
									a.AwBillNo,
									case a.status 
											when 'Draft' Then 'Purchase Request' 
											when 'Posted' then 'Purchase Order'
											when 'Cancel' then 'Cancel'
									else a.status 
									end iStatus,
									isnull(c.docstatus,'') SAP_Status,
									a.vendDOno,
									b.ItemCode ,
									d.itemname ,
									d.u_brand,
									d.u_group ,
									d.u_subgroup, 
									d.u_spegroup ,
									d.u_hs_Code,
									b.PiNumber, 
									b.Slaughterhouse  ,      
									a.DocCur ,
									a.CurRate,
									isnull(b.OldFreeText,'')freetxt,
									b.Quantity ,d.InvntryUom,
									b.PackagingQty ,b.PackagingUom,
									b.Price ,
									b.Total,
									isnull(a.Remarks,'') remarks
								from 
								Tx_PurchaseOrder a 
									inner join Tx_PurchaseOrder_Content b on a.Id = b.DetId
									inner join """+ database2 + """.dbo.oitm d on b.ItemCode = d.itemcode 
									left outer join  """+ database2 + """.dbo.opor c on a.SapPurchaseOrderId = c.docentry    
								where convert(varchar,a.DueDate,112) between @datefrom and @dateto 
								and  a.BpCode + a.BpName like '%' +  @partner + '%' 
								and  d.itemcode + d.itemname like '%' + @item  + '%'
								and isnull(d.U_group,'') + isnull(d.u_subgroup,'') + isnull(d.u_spegroup,'')  like '%' + @igroup  +'%'
								order by  convert(varchar,a.DueDate,23) 

												
				"""
				print(msg_sql)
			
			if self.export_to =="xlssummary":
				msg_sql=  """
								declare @datefrom varchar(10) , @dateto varchar(10), @partner varchar(100) , @item varchar(50), @igroup varchar(50)

								set @datefrom = '""" +  self.datefrom.strftime("%Y%m%d") + """'
								set @dateto = '""" +  self.dateto.strftime("%Y%m%d") + """'
								set @partner = '""" +  partner + """'
								set @item = '""" +  item + """'
								set @igroup = '""" +  igroup + """'

								 select 
										'"""+ comp.code_base + """' company, 
									a.transNo,
									a.Container ,
									a.Vessel ,
									a.AwBillNo,
									case a.status 
											when 'Draft' Then 'Purchase Request' 
											when 'Posted' then 'Purchase Order'
											when 'Cancel' then 'Cancel'
									else a.status 
									end iStatus,
									a.vendDOno,
									'[' + b.ItemCode +'] '+ d.itemname  itemname,
									d.u_brand,
									b.Slaughterhouse  , 
									isnull(b.OldFreeText,'')freetxt,
									b.PiNumber,      
									d.u_hs_Code,
									a.DocCur ,
									b.Price ,
									b.PackagingQty ,b.PackagingUom,
									b.Quantity ,d.InvntryUom,
									convert(varchar,a.duedate ,23) ETA,
									isnull(a.Remarks,'') remarks
								from 
								Tx_PurchaseOrder a 
									inner join Tx_PurchaseOrder_Content b on a.Id = b.DetId
									inner join """+ database2 + """.dbo.oitm d on b.ItemCode = d.itemcode 
									left outer join  """+ database2 + """.dbo.opor c on a.SapPurchaseOrderId = c.docentry    
								where convert(varchar,a.DueDate,112) between @datefrom and @dateto 
								and  a.BpCode + a.BpName like '%' +  @partner + '%' 
								and  d.itemcode + d.itemname like '%' + @item  + '%'
								and isnull(d.U_group,'') + isnull(d.u_subgroup,'') + isnull(d.u_spegroup,'')  like '%' + @igroup  +'%'
								order by  convert(varchar,a.DueDate,23) 
											 
				"""
 

			data = pandas.io.sql.read_sql(msg_sql,conn)
			listfinal.append(data)

 

		df = pd.concat(listfinal)
		#dflist = df.values.tolist() 

		#filename = filenamexls2 
 
		if self.export_to =="xls" :
			df.to_excel(mpath + '/temp/'+ filenamexls2,index=False)
		if self.export_to =="xlssummary" :
			df.to_excel(mpath + '/temp/'+ filenamexls2,index=False)
 
			   
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

 