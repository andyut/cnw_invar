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


class AWR_PL(models.TransientModel):
    _name           = "cnw.awr28.pl"
    _description    = "cnw.awr28.pl"
    company_id      = fields.Many2many('res.company', string="Company",required=True)
    dateto          = fields.Date ("Date To", default=fields.Date.today()) 
    export_to       = fields.Selection([ ('xls', 'Excel'),
                                            ('pdf', 'PDF'),
                                            ('xlsmonthly', 'PL XLS Monthly'),
                                            ('xlsgabungan', 'PL XLS Gabungan'),
                                            ('xlsmonthly4', 'PL XLS Monthly Lvl 4')
                                            ],string='Export To', default='xlsmonthly')
    filexls         = fields.Binary("File Output")    
    filenamexls     = fields.Char("File Name Output")
    
    
    
    def view_pl(self): 
        mpath       = get_module_path('cnw_awr28')
        filename    = 'PL_'+ self.env.user.company_id.db_name +  self.dateto.strftime("%Y%m%d")  + '.xlsx'
        filenamexls    = 'PL_'+ self.env.user.company_id.db_name +   self.dateto.strftime("%Y%m%d")  + '.xlsx'
        filenamexls2    = 'PL_'+  self.env.user.company_id.db_name +  self.dateto.strftime("%Y%m%d")  + '.xlsx'
        filenamepdf = 'PL_'+  self.env.user.company_id.db_name +  self.dateto.strftime("%Y%m%d")  + '.pdf'
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
            
            #conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+host+';DATABASE='+database+';UID='+user+';PWD='+ password + ';TrustServerCertificate=yes')
            conn = pymssql.connect(host=host, user=user, password=password, database=database)
            listcom.append(comp.code_base)
            cursor = conn.cursor()
            pl5 = """
                        declare 

                                    @i_yyyymm 	varchar(10),
                                    @i_cab				varchar(50)

                            set @i_yyyymm = '"""+  self.dateto.strftime("%Y%m%d")  + """'
                            set @i_cab = '""" + comp.code_base + """'

                            DECLARE @MONTH VARCHAR(10) 
                            DECLARE @TABLE TABLE (  cab varchar (50) ,
                                                    ketr    varchar(200) ,
                                                    code varchar(5) ,
                                                    header    varchar(200) ,
                                                    acctcode varchar(50),
                                                    acctName varchar(200),
                                                    thismonth numeric(19,6),
                                                    thisyear numeric(19,6)
                                                )
                                                    
                            DECLARE 	@v_TMjualTotal		numeric(19,6),		@v_jualTotal		numeric(19,6),	
                                        @v_TMretDisC		numeric(19,6),		@v_retDisC			numeric(19,6),	
                                        @v_TMlabaKotor		numeric(19,6),		@v_labaKotor		numeric(19,6),	
                                        @v_TMBiaya			numeric(19,6),		@v_Biaya			numeric(19,6),	
                                        @v_TMPend			numeric(19,6),		@v_Pend				numeric(19,6),	
                                        @v_TMBiaya8			numeric(19,6),		@v_Biaya8			numeric(19,6),	
                                        @v_TMLabaOp			numeric(19,6),  	@v_LabaOp			numeric(19,6),
                                        @v_TMLaba_Pend      numeric(19,6),  	@v_Laba_Pend        numeric(19,6),
                                        @v_TMProfit			numeric(19,6),  	@v_Profit			numeric(19,6),
                                        @v_TMHPP 			numeric(19,6),		@v_HPP 				numeric(19,6)
                                
                            SET @MONTH = left(@i_yyyymm 	,6)
                            insert into @TABLE
                            select    @i_cab ,
                                    'Periode ' + left(@i_yyyymm,4) + '0101' + '-' + @i_yyyymm,
                                    CASE LEFT(ACCOUNT,1) 
                                    WHEN '4' THEN 'A'
                                    WHEN '5' THEN 'B'
                                    WHEN '6' THEN 'D'
                                    WHEN '7' THEN 'J'
                                    WHEN '8' THEN 'K'
                                    end ,
                                    c.acctCode + '-' + c.AcctName,
                                    CASE LEFT(ACCOUNT,1) 
                                    WHEN '4' THEN 'A' + isnull(ACCOUNT,'')
                                    WHEN '5' THEN 'B'+ isnull(ACCOUNT,'')
                                    WHEN '6' THEN 'D'+ isnull(ACCOUNT,'')
                                    WHEN '7' THEN 'J'+ isnull(ACCOUNT,'')
                                    WHEN '8' THEN 'K'+ isnull(ACCOUNT,'')
                                    end ,
                                    isnull(ACCOUNT,'') + '-' + b.acctname,
                                    sum(case LEFT(CONVERT(VARCHAR,RefDate,112) ,6)
                                            when @MONTH then 
                                                                CASE LEFT(ACCOUNT,1) 
                                                                        WHEN '4' THEN credit - debit
                                                                        WHEN '5' THEN debit - credit
                                                                        WHEN '6' THEN debit - credit 
                                                                        WHEN '7' THEN credit - debit 
                                                                        WHEN '8' THEN debit - credit 
                                                                end 
                                                        else 0 end) ,
                                    sum(case when LEFT(CONVERT(VARCHAR,RefDate,112) ,6) <= @MONTH 
                                                        then 
                                                                CASE LEFT(ACCOUNT,1) 
                                                                        WHEN '4' THEN credit - debit
                                                                        WHEN '5' THEN debit - credit
                                                                        WHEN '6' THEN debit - credit 
                                                                        WHEN '7' THEN credit - debit 
                                                                        WHEN '8' THEN debit - credit 
                                                                end 
                                                        else 0 end)  
                                                                    /*
                                                    sum( CASE LEFT(ACCOUNT,1) 
                                                                        WHEN '4' THEN credit - debit
                                                                        WHEN '5' THEN debit - credit
                                                                        WHEN '6' THEN debit - credit 
                                                                        WHEN '7' THEN credit - debit 
                                                                        WHEN '8' THEN debit - credit 
                                                                end )*/
                                        
                                From JDT1 (nolock) A 
                                inner join OACT  (nolock) B ON A.account = b.acctCode
                                inner join OACT (nolock) C on b.fatherNum = c.acctCode
                            where left(account,1) in ('4','5','6','7','8')
                                AND convert(VARCHAR,RefDate,112) <= @i_yyyymm  and convert(VARCHAR,RefDate,112) >=left(@i_yyyymm,4) + '0101'
                            and transtype>0
                            group by ACCOUNT,c.acctCode + '-' + c.AcctName,b.acctname
                            order by ACCOUNT

                            select @v_jualTotal     = sum(thisyear) from @table where left(rtrim(substring(acctcode ,2,50)),4)  = '4110'
                            select @v_retDisC       = sum(thisyear) from @table where left(rtrim(substring(acctcode ,2,50)),4)  in( '4120','4130')
                            select @v_HPP           = sum(thisyear) from @table where left(rtrim(substring(acctcode ,2,50)),1)  ='5'
                            select @v_Biaya           = sum(thisyear) from @table where left(rtrim(substring(acctcode ,2,50)),1)  ='6'
                            select @v_Pend           = sum(thisyear) from @table where left(rtrim(substring(acctcode ,2,50)),1)  ='7'
                            select @v_Biaya8          = sum(thisyear) from @table where left(rtrim(substring(acctcode ,2,50)),1)  ='8'


                            select @v_TMjualTotal     = sum(thismonth) from @table where left(rtrim(substring(acctcode ,2,50)),4)  = '4110'
                            select @v_TMretDisC       = sum(thismonth) from @table where left(rtrim(substring(acctcode ,2,50)),4) in( '4120','4130')
                            select @v_TMHPP           = sum(thismonth) from @table where left(rtrim(substring(acctcode ,2,50)),1)  ='5'
                            select @v_TMBiaya           = sum(thismonth) from @table where left(rtrim(substring(acctcode ,2,50)),1)  ='6'
                            select @v_TMPend           = sum(thismonth) from @table where left(rtrim(substring(acctcode ,2,50)),1)  ='7'
                            select @v_TMBiaya8          = sum(thismonth) from @table where left(rtrim(substring(acctcode ,2,50)),1)  ='8'


                                SET @v_labaKotor		=	ISNULL((ISNULL(@v_jualTotal,0)	+ISNULL(@v_retDisC,0))  - isnull(@v_HPP,0),0)
                                SET @v_TMlabaKotor      =	(ISNULL(@v_TMjualTotal,0)	+ ISNULL(@v_TMretDisC,0))  - isnull(@v_TMHPP,0)
                                SET @v_LabaOp 			=   isnull(@v_LabaKotor,0)  - isnull(@v_Biaya,0)
                                SET @v_TMLabaOp 		=   isnull(@v_TMLabaKotor,0)  - isnull(@v_TMBiaya,0)
                                SET @v_Laba_Pend		=	isnull(@v_Pend,0)
                                SET @v_TMLaba_Pend      =	isnull(@v_TMPend,0)
                                SET @v_Profit			=	isnull(@v_LabaOp,0) +isnull( @v_Laba_Pend,0) - isnull(@v_Biaya8	,0)
                                SET @v_TMProfit			=	isnull(@v_TMLabaOp,0) + isnull(@v_TMLaba_Pend,0) - isnull(@v_TMBiaya8,0)	

                            insert into @table 
                                select  @i_cab  ,'Periode ' + left(@i_yyyymm,4) + '0101' + '-' + @i_yyyymm ,  'C','C-Penjualan','C', 'Penjualan', isnull((ISNULL(@v_TMjualTotal,0)	+ ISNULL(@v_TMretDisC,0)) ,0), (ISNULL(@v_jualTotal,0)	+ ISNULL(@v_retDisC,0))	
                                UNION ALL 
                                select  @i_cab  ,'Periode ' + left(@i_yyyymm,4) + '0101' + '-' + @i_yyyymm ,  'C','C-HPP','C', 'HPP', isnull(@v_TMHPP,0), isnull(@v_HPP,0)	
                                UNION ALL 
                                select  @i_cab ,'Periode ' + left(@i_yyyymm,4) + '0101' + '-' + @i_yyyymm ,  'C','C-Laba Kotor','C', 'Laba Kotor', isnull(@v_TMlabaKotor,0), isnull(@v_labaKotor,0)	
                                UNION ALL 
                                
                                SELECT   @i_cab  ,'Periode ' + left(@i_yyyymm,4) + '0101' + '-' + @i_yyyymm ,  'H','H-Total Biaya', 'H', 'Total Biaya', @v_TMBiaya , @v_Biaya 
                                
                                UNION ALL 
                                
                                SELECT  @i_cab ,'Periode ' + left(@i_yyyymm,4) + '0101' + '-' + @i_yyyymm , 'I','I-Laba Operasi','I', 'Laba Operasi', @v_TMLabaOp, @v_LabaOp
                                
                                UNION ALL
                                
                                SELECT  @i_cab  ,'Periode ' + left(@i_yyyymm,4) + '0101' + '-' + @i_yyyymm , 'L','L-Total Pendapatan lain Lain','L', 'Total Pendapatan Lain-lain', @v_TMLaba_Pend, @v_Laba_Pend
                                
                                UNION ALL

                                SELECT  @i_cab  ,'Periode ' + left(@i_yyyymm,4) + '0101' + '-' + @i_yyyymm , 'M' ,'M-Total Biaya Lain Lain','M' , 'Total Biaya Lain-lain', @v_TMBiaya8, @v_Biaya8

                                UNION ALL
                                
                                SELECT  @i_cab  ,'Periode ' + left(@i_yyyymm,4) + '0101' + '-' + @i_yyyymm , 'N','N-Profit','N', 'Profit', @v_TMProfit	, @v_Profit	

                            


                            SELECT * FROM @TABLE order by code,acctcode 

                            
            """
            if self.export_to == "xlsmonthly":
                msg_sql=  "exec [dbo].[IGU_ACT_PL3] '" +  self.dateto.strftime("%Y%m%d") + "','"+ comp.code_base + "' "
            elif self.export_to == "xlsmonthly4":
                msg_sql=  "exec [dbo].[IGU_ACT_PL4] '" +  self.dateto.strftime("%Y%m%d") + "','"+ comp.code_base + "' "
            elif self.export_to == "xlsgabungan":
                msg_sql=  pl5
            else :
                msg_sql=  "exec [dbo].[IGU_ACT_PL] '" +  self.dateto.strftime("%Y%m%d") + "','"+ comp.code_base + "' "
            #msg_sql=  "exec [dbo].[IGU_ACT_PL] '" +  self.dateto.strftime("%Y%m%d") + "','"+ comp.code_base + "' "

            data = pandas.io.sql.read_sql(msg_sql,conn)
            listfinal.append(data)

 
        df = pd.concat(listfinal)
        dflist = df.values.tolist() 

        if self.export_to =="xls":
            filename = filenamexls2 
            #report = df.groupby(["Group","AR Person"]).sum()
            df.to_excel(mpath + '/temp/'+ filenamexls2,index=False)
        if self.export_to =="xlsgabungan":
            filename = filenamexls2 
            df.pivot_table(index=["acctcode","acctName"],columns=["cab"],aggfunc=np.sum,values=["thismonth","thisyear"],fill_value=0).sort_index().to_excel(mpath + '/temp/'+ filenamexls2)
            #report = df.groupby(["Group","AR Person"]).sum()
            #df.to_excel(mpath + '/temp/'+ filenamexls2,index=False)
        if self.export_to =="xlsmonthly":
            filename = filenamexls2 
            #report = df.groupby(["Group","AR Person"]).sum()
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
                worksheet.set_column(6,18,20)

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
                worksheet.write (2,18,"Total",header_format2)                 

                for ln in comdata.values.tolist(): 
                    if ln[4]=='9999001':

                        worksheet.write(3+line,1, ln[0],moneyb_format)
                        worksheet.write(3+line,2, ln[1],moneyb_format)
                        worksheet.write(3+line,3, ln[2],moneyb_format)
                        worksheet.write(3+line,4, ln[3],moneyb_format)
                        worksheet.write(3+line,5, ln[4],moneyb_format)
                        worksheet.write(3+line,6, ln[5],moneyb_format)
                        worksheet.write(3+line,7, ln[6],moneyb_format)
                        worksheet.write(3+line,8 ,ln[7],moneyb_format)
                        worksheet.write(3+line,9, ln[8],moneyb_format)
                        worksheet.write(3+line,10, ln[9],moneyb_format)
                        worksheet.write(3+line,11, ln[10],moneyb_format)
                        worksheet.write(3+line,12, ln[11],moneyb_format)
                        worksheet.write(3+line,13, ln[12],moneyb_format)
                        worksheet.write(3+line,14, ln[13],moneyb_format)
                        worksheet.write(3+line,15, ln[14],moneyb_format)
                        worksheet.write(3+line,16, ln[15],moneyb_format)
                        worksheet.write(3+line,17, ln[16],moneyb_format)  
                        worksheet.write(3+line,18, ln[17],moneyb_format)  
                    elif  ln[4]=='9999002':
                        worksheet.write(3+line,1, ln[0],moneyc_format)
                        worksheet.write(3+line,2, ln[1],moneyc_format)
                        worksheet.write(3+line,3, ln[2],moneyc_format)
                        worksheet.write(3+line,4, ln[3],moneyc_format)
                        worksheet.write(3+line,5, ln[4],moneyc_format)
                        worksheet.write(3+line,6, ln[5],moneyc_format)
                        worksheet.write(3+line,7, ln[6],moneyc_format)
                        worksheet.write(3+line,8 ,ln[7],moneyc_format)
                        worksheet.write(3+line,9, ln[8],moneyc_format)
                        worksheet.write(3+line,10, ln[9],moneyc_format)
                        worksheet.write(3+line,11, ln[10],moneyc_format)
                        worksheet.write(3+line,12, ln[11],moneyc_format)
                        worksheet.write(3+line,13, ln[12],moneyc_format)
                        worksheet.write(3+line,14, ln[13],moneyc_format)
                        worksheet.write(3+line,15, ln[14],moneyc_format)
                        worksheet.write(3+line,16, ln[15],moneyc_format)
                        worksheet.write(3+line,17, ln[16],moneyc_format)     
                        worksheet.write(3+line,18, ln[17],moneyc_format)           
                    else:
                        worksheet.write(3+line,1, ln[0])
                        worksheet.write(3+line,2, ln[1])
                        worksheet.write(3+line,3, ln[2])
                        worksheet.write(3+line,4, ln[3])
                        worksheet.write(3+line,5, ln[4])
                        worksheet.write(3+line,6, ln[5])
                        worksheet.write(3+line,7, ln[6])
                        worksheet.write(3+line,8 ,ln[7])
                        worksheet.write(3+line,9, ln[8])
                        worksheet.write(3+line,10, ln[9])
                        worksheet.write(3+line,11, ln[10])
                        worksheet.write(3+line,12, ln[11])
                        worksheet.write(3+line,13, ln[12])
                        worksheet.write(3+line,14, ln[13])
                        worksheet.write(3+line,15, ln[14])
                        worksheet.write(3+line,16, ln[15])
                        worksheet.write(3+line,17, ln[16])          
                        worksheet.write(3+line,18, ln[17])            
                    line+=1

            workbook.close()
        if self.export_to =="xlsmonthly4":
            filename = filenamexls2 
            #report = df.groupby(["Group","AR Person"]).sum()
            df.to_excel(mpath + '/temp/'+ filenamexls2,index=False)
                                     
        if self.export_to =="pdf":
            filename = filenamepdf
            
            env = Environment(loader=FileSystemLoader(mpath + '/template/'))
            template = env.get_template("pl_template.html")            
            template_var = {"company":self.env.user.company_id.name,
                            "igu_title" :"Profit & Lost",
                            "datetime" :igu_tanggal ,
                            "dateto" :self.dateto.strftime("%Y-%m-%d") ,
                            "igu_remarks" :"Profit & Lost" ,
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

 