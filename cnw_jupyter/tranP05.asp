<!-- #include file ="../../lib/libmain.asp" -->
<%
strproc						= request("strproc")
inv_delivery_no			= request("inv_delivery_no")
dt_dari   = request("dt_dari")
dt_sampai = request("dt_sampai")
hal 				= request("hal")
inv_DO 		= REQUEST("inv_DO")
inv_OrderBy	= REQUEST("inv_OrderBy")
inv_no						= request("inv_no")
inv_no2						= request("inv_no2")
inv_no1						= request("inv_no1")
inv_fktPjk				= request("inv_fktPjk")
glb_usr_Code=session("glb_usr_Code")
set rs		= server.CreateObject ("ADODB.RecordSet")
set con	= server.CreateObject ("ADODB.Connection")
con.Open Application("appOLEDB")

varquery = "hal=" & hal & "&dt_dari=" & dt_dari & "&dt_sampai=" & dt_sampai & "&inv_OrderBy=" & inv_OrderBy & "&inv_no2=" & inv_no2 & "" & "&inv_no1=" & inv_no1 & ""
varquery = varquery & "&inv_DO=" & inv_DO & "&"
select case strproc
case "NN"
		
		if len(inv_delivery_no)>0 then 
			strSQL = "SELECT	dlv_no,    dlv_ordNo , " & _
						"			CONVERT(VARCHAR,CONVERT(SMALLDATETIME,dlv_date,112),105)dlv_date, " & _
						"				CONVERT(VARCHAR,CONVERT(SMALLDATETIME,(DATEADD (DAY, CONVERT(SMALLINT,ISNULL(cod_DESC1,0)),GETDATE())),112),105) dlv_due_date,   " & _
						"				dlv_customer,ctm_Name,  isnull(dlv_invNo,'') dlv_invNo,dlv_tax,   " & _
						"				dlv_remark     " & _
						"FROM trade.t_t_sDelivery_master  A     " & _
						"	INNER JOIN trade.t_m_customer B     " & _
						"		ON A.dlv_customer =B.ctm_CODE    " & _
						"	LEFT OUTER JOIN trade.t_m_code C    " & _
						"		ON CONVERT(VARCHAR,B.ctm_TPayment) = C.cod_CODE AND cod_HEAD_CODE='TO'    " & _
						" WHERE dlv_no='" & inv_delivery_no &"'"
			rs.open strSQL,con,1,3
			if not rs.eof then  
					if len(rs("dlv_invNo"))>0 then
						Response.Write "<script>"
						Response.Write "alert('DO no " & inv_delivery_no & " sudah pernah dibuat faktur !');" & vbcrlf
						Response.Write "self.location.replace('?');" & vbcrlf
						Response.Write "</script>"
					else
						dlv_ordNo  = rs("dlv_ordNo")
						strSQLy = "select   			distinct  " & _
											"						dlv_materialSO,           " & _
											"						left(Deskripsi, 28) Deskripsi,    " & _
											"						isnull(d2.ord_UPrice, d.ord_UPrice) dlv_UPrice,             " & _
											"						dlv_qty,                " & _
											"						0 qty_terima,     " & _
											"						dlv_qty *  isnull(d2.ord_UPrice, d.ord_UPrice)  dlv_Amt,                " & _
											"						0 disc_rt,              " & _
											"						0 amt_disc,             " & _
											"						0 ttl,   " & _
											"						Deskripsi sDeskripsi, " & _
											"						convert(smallint, isnull(d2.ord_Seq, d.ord_Seq )),'', prd_tax  " & _
											"		from trade.t_t_sDelivery_detail A     " & _
											"			inner join   trade.vw_produk B     " & _
											"				on prd_code=dlv_materialSO    " & _
											"			INNER JOIN   " & _
											"				(SELECT 	ord_no,   " & _
											"								ord_material,   " & _
											"								ord_UPrice ,   " & _
											"								ord_Amt  , " & _
											"								ord_Seq " & _
											"					FROM 	trade.t_t_sorder_detail    " & _
											"				WHERE ord_no = '" & dlv_ordNo & "' ) d ON a.dlv_materialSO = d.ord_material   " & _
											"			INNER JOIN   " & _
											"				(SELECT 	ord_no,   " & _
											"								ord_material,   " & _
											"								ord_UPrice ,   " & _
											"								ord_Amt  , " & _
											"								ord_Seq " & _
											"					FROM 	trade.t_t_sorder_detail    " & _
											"				WHERE ord_no = '" & dlv_ordNo & "' ) d2  " & _
											"				ON a.dlv_materialSO = d2.ord_material  and a.dlv_Seq = d2.ord_Seq  " & _
											" WHERE dlv_no ='" & inv_delivery_no & "' order by convert(smallint, isnull(d2.ord_Seq, d.ord_Seq )) "
						

												
						inv_duedate = rs("dlv_due_date")
						inv_customer = rs("dlv_customer")
						inv_date			= rs("dlv_date")
						inv_customerdesc = rs("ctm_Name")
						inv_remark = rs("dlv_remark")
						inv_tax				= rs("dlv_tax")
						dlv_tax				= rs("dlv_tax")
					end if
			else
				subalertNofound		
			end if 
			rs.close
		end if 
case "QQ"	
	if len(inv_no)>0 then 
			strSQL = "SELECT	inv_no, " & _
						"				CONVERT(VARCHAR,CONVERT(SMALLDATETIME,inv_date,112), 105)inv_date, " & _
						"				CONVERT(VARCHAR,CONVERT(SMALLDATETIME,inv_duedate,112), 105)inv_duedate, " & _
						"				dlv_customer inv_customer, B.ctm_Shortname ctm_Name, dlv_tax, " & _
						"				inv_delivery_no,cast (inv_tax as varchar) inv_tax,inv_account_slip_no, " & _
						"				inv_remark, dlv_ordNo, inv_fktPjk  " & _
						"	FROM  trade.t_t_sInvoice_master A " & _
						"		INNER JOIN trade.t_t_sDelivery_master C " & _
						"			ON  C.dlv_no = A.inv_delivery_no " & _
						"		left outer JOIN  trade.t_m_customer B " & _
						"			ON C.dlv_customer = B.ctm_CODE " & _
						"WHERE inv_no ='"& inv_no &"'"
						
				rs.open strSQL,con,1,3
				'dispend strSQL
				if not rs.eof then 
					inv_date = rs("inv_date")
					inv_duedate = rs("inv_duedate")
					inv_fktPjk	= rs("inv_fktPjk")
					inv_customer =rs("inv_customer")
					inv_customerdesc= rs("ctm_Name")
					inv_account_slip_no = rs("inv_account_slip_no")
					inv_tax = rs("inv_tax")
					inv_delivery_no = rs("inv_delivery_no")
					inv_remark =rs("inv_remark")
					dlv_tax=rs("dlv_tax")
					strSQLy ="select	inv_material,  " & _
									"			left(Deskripsi,28) Deskripsi,                      " & _
									"			ord_UPrice inv_up,  " & _
									"			dlv_qty, " & _
									"			isnull(inv_qty, 0) inv_qty,  " & _
									"			isnull(inv_Amt, 0) inv_Amt, " & _
									"			isnull(inv_DiscRate,0) inv_DiscRate,   " & _
									"			isnull((0.01 * inv_DiscRate * inv_Amt),0) amt_disc, " & _
									"			(1-(0.01 * inv_DiscRate)) * inv_Amt ttl, Deskripsi sDeskripsi " & _
									"from trade.t_t_sInvoice_detail A " & _
									"	inner join trade.t_t_sInvoice_master B " & _
									"		on A.inv_no = B.inv_no " & _
									"	inner join trade.vw_produk C " & _
									"		on C.prd_code = A.inv_material   " & _
									"	inner join trade.t_t_sDelivery_detail	D " & _
									"		on D.dlv_no=B.inv_delivery_no " & _
									"		and A.inv_material=D.dlv_materialSO  " & _
									"	INNER JOIN trade.t_t_sDelivery_master x " & _
									"		ON x.dlv_no=B.inv_delivery_no   " & _
									"	INNER JOIN trade.t_t_sOrder_detail y " & _
									"		ON x.dlv_ordNo = y.ord_no " & _
									"		AND d.dlv_MaterialSO = y.ord_material " & _
									"where A.inv_no='" & inv_no & "' ORDER BY convert(smallint,inv_seq) asc "
									strSQLy = "exec trade.p_k_tranP05 '" & strProc & "','" & inv_no & "','" & inv_delivery_no & "'"
									
						strSQLy ="SELECT distinct dlv_materialSO,     " &_
										"				left(Deskripsi,28) Deskripsi,                         " &_
										"				ISNULL(ISNULL(y.ord_UPrice,y2.ord_Uprice),ISNULL(a.inv_UP, a2.inv_UP))  inv_UP,     " &_
										"				dlv_qty,    " &_
										"				isnull(ISNULL(a.inv_qty, a2.inv_Qty), 0) inv_Qty ,     " &_
										"				isnull(ISNULL(ISNULL(y.ord_UPrice,y2.ord_Uprice),ISNULL(a.inv_UP, a2.inv_UP))  * ISNULL(a.inv_qty, a2.inv_Qty),0) inv_Amt,     " &_
										"				ISNULL(a.inv_DiscRate, a2.inv_DiscRate)inv_DiscRate,     " &_
										"				(0.01 * ISNULL(a.inv_DiscRate, a2.inv_DiscRate) * ISNULL(ISNULL(y.ord_UPrice,y2.ord_Uprice),ISNULL(a.inv_UP, a2.inv_UP))  * ISNULL(a.inv_qty, a2.inv_Qty)) amt_disc,    " &_
										"				(1-(0.01 * ISNULL(a.inv_DiscRate, a2.inv_DiscRate))) *  ISNULL(ISNULL(y.ord_UPrice,y2.ord_Uprice),ISNULL(a.inv_UP, a2.inv_UP))  * ISNULL(a.inv_qty, a2.inv_Qty) ttl, Deskripsi sDeskripsi, ISNULL(y.ord_Seq, y2.ord_Seq)ord_Seq, isnull( A.inv_remark1 ,A2.INV_REMARK1) inv_remark1 ,prd_tax " &_
										"FROM trade.t_t_sDelivery_detail	D    " &_
										"	INNER JOIN   " &_
										"		(SELECT * FROM trade.t_t_sInvoice_master   " &_
										"			WHERE inv_no='" & inv_no & "'   " &_
										"		) AS B    " &_
										"		ON d.dlv_no = b.inv_delivery_no  " &_
										"	LEFT OUTER JOIN   " &_
										"		(SELECT * FROM trade.t_t_sInvoice_detail   " &_
										"			WHERE inv_no='" & inv_no & "' " &_
										"		) AS A    " &_
										"		ON d.dlv_materialSO = a.inv_material  " &_
										"		AND A.inv_no = B.inv_no  " &_
										"		AND d.dlv_seq = a.inv_Seq  " &_
										"	LEFT OUTER JOIN   " &_
										"		(SELECT * FROM trade.t_t_sInvoice_detail   " &_
										"			WHERE inv_no='" & inv_no & "' " &_
										"		) AS A2    " &_
										"		ON d.dlv_materialSO = a2.inv_material  " &_
										"		AND A2.inv_no = B.inv_no  " &_
										"	INNER JOIN trade.vw_produk C    " &_
										"		on C.prd_code = d.dlv_materialSO  " &_
										"	INNER JOIN trade.t_t_sDelivery_master x " &_  
										"		ON x.dlv_no=B.inv_delivery_no     " &_
										"	left outer JOIN trade.t_t_sOrder_detail y  " &_ 
										"		ON x.dlv_ordNo = y.ord_no   " &_
										"		AND d.dlv_MaterialSO = y.ord_material    " &_
										"		AND d.dlv_seq = y.ord_seq   		" &_
										"	left outer JOIN trade.t_t_sOrder_detail y2 " &_
										"		ON x.dlv_ordNo = y2.ord_no   " &_
										"		AND d.dlv_MaterialSO = y2.ord_material  and d.dlv_Seq = y2.ord_Seq  " 
'										"ORDER BY convert(smallint,ISNULL(y.ord_Seq, y2.ord_Seq)) ASC   "

'RESPONSE.WRITE 			strSQLy			
'			RESPONSE.END 		
				end if 
				rs.close
	end if 
case "SV"	

case "DD"	

end select

%>
<HTML>
<HEAD>
<%
subHead " Faktur Jual "
%>
<!--style>
.text1{font-family:Tahoma;font-size:9px}
.text2{font-family:Tahoma;font-size:9px}
.inp{font-family:Tahoma;font-size:9;border:solid 1 px #333333}
</style-->
<script>
<%
hehe = 	"SELECT cod_CODE, " & _
			"				curr_Kurs " & _
			"FROM  " & _
			"				trade.t_m_code A  " & _
			"INNER   JOIN  " & _
			"			(	SELECT Curr_Code, MAX(curr_KursTengah) curr_Kurs " & _
			"				FROM  " & _
			"							trade.t_m_currency  " & _
			"				WHERE  " & _
			"							curr_excDate=( " & _
			"																SELECT MAX(curr_excDate) " & _
			"																FROM  " & _
			"																			trade.t_m_currency " & _
			"														) " & _
			"				GROUP BY Curr_Code  " & _
			"			)B " & _
			"ON   " & _
			"			A.cod_CODE = B.Curr_Code  " & _
			"WHERE  " & _
			"			cod_HEAD_CODE ='CR' AND cod_CODE<>'*'"
subArrJv hehe,"arrCurr",arrData
%>
	function jvChangeCurr(param)
	{
		var i;
		for (i=0;i< arrCurr.length;i++)
		{
			arrtemp = arrCurr[i].split(":");
			if (param==arrtemp[0])
			{
				frm.inv_CurrRate.value  = jvCurrency(arrtemp[1]);
			}
		}
	}
	function jvF1(param)
	{
		if(param.name=="inv_delivery_no"  && param.readOnly==false)
		{
			jvFindData("../popup/popTranP02.asp?param=inv_delivery_no&strProc=NN",550,500);
		}
		if(param.name=="inv_no"  && param.readOnly==false)
		{
			jvFindData("../popup/popTranP05.asp?param=inv_no&strProc=QQ",450,400);
		}
		if(param.name=="ord_usercode"  && param.readOnly==false)
		{
			jvFindData("../popup/popTranP01sales.asp?param=ord_usercode",450,400);
		}
		if(param.name=="inv_material"  && param.readOnly==false)
		{
			jvFindData("../popup/popTranPrd.asp?param=inv_material",450,400);
		}
	}
	function jvQuery(param)
		{
			if(event.keyCode==13 || event.keyCode==9)
			{
				//alert("test");
				if(frm.inv_no.value!="")
				{
					if(frm.strProc.value=="")
					{
						frm.strProc.value="NN";
					}	
					frm.submit();
				} 	
			}	
		}
		
	function jvF2()
	{
		self.location.replace ("?<% = varquery %>strProc=QQ") 
	}	
	
	function jvF5()
	{
		self.location.replace ("?<% = varquery %>strProc=NN") 
	}
	
	function jvF10()
	{
	if (frm.inv_no.value== "" && frm.inv_no.value=="" )
	{alert("maaf, no Faktur Jual tidak boleh kosong. !");
		return false;		
	}
	else
	{
				jvFindData("tranP05r.asp?strCount=1&strCode=" + frm.inv_no.value + "&strProc=SV",600,500);
	}
	}
	
	function jvF8()
	{
		if(frm.inv_delivery_no.value == "" || frm.inv_customerdesc.value == ""  || frm.inv_date.value=="")
		{
			alert("Lengkapi data. !")
			return false;
		}
			else
				{
					frm.strProc.value="SV";
//					frm.btnF8.disabled  = true;
//					frm.btnF7.disabled  = true;
					jvSave();
				}
		
	}
	
	function jvF7()
	{
		if(frm.inv_no.value==""  || frm.inv_delivery_no.value == "" || tabC.rows.length<1   )
		{
			alert("Anda belum memilih data yang akan dihapus !")
			return false;
		}
			else
				{
					a=self.confirm ("Anda yakin akan menghapus data ini ");
					if (a)
					{
						frm.strProc.value="DD";
						frm.btnF8.disabled  = true;
						frm.btnF7.disabled  = true;
						jvSave();
					}					
				}
		
	}


function GetProduk(vari,vari2)
{
if (frm.dlv_material.value!="")
{
	var xmlobj = new ActiveXObject("Microsoft.XMLHTTP");
	var xmlobj2 = new ActiveXObject("Microsoft.XMLDOM");
	xmlobj2.async=false;		
	xmlobj.open ("POST","tranP01XMLsave.asp",false);
	xmlobj.send ("<root><data fnc='3'><dat1>" + vari + "</dat1><dat2>" + vari2 + "</dat2></data></root>");

//	alert(xmlobj.responseText);

	arrtemp=xmlobj.responseText.split("~");
	if (arrtemp[0]!="GA")
	{
		if (arrtemp[0].length<50)
		{
			frm.ord_materialdesc.value = arrtemp[0];
			prdunit.innerText= arrtemp[1];
			frm.inv_up.value = arrtemp[2];
			frm.ord_qty.focus();
			
		}else
			{
				alert("Ada kesalahan di server, hubungi bagian administrasi");
				frm.ord_material.value="";
				frm.ord_material.focus();

			}
		
	}
else
	{
		alert("Produk tidak ada ");
		frm.ord_material.value="";
		frm.ord_material.select();
		frm.ord_material.focus();
		return false;
	}
	
	//return false;
}
}
function GetSalesOrder(vari)
{
if (frm.ord_no.value!="")
{
	var xmlobj = new ActiveXObject("Microsoft.XMLHTTP");
	var xmlobj2 = new ActiveXObject("Microsoft.XMLDOM");
	xmlobj2.async=false;		
	xmlobj.open ("POST","tranP01XMLsave.asp",false);
	xmlobj.send ("<root><data fnc='2'>" + vari + "</data></root>");
	if (xmlobj.responseText!="GA")
	{
		if (xmlobj.responseText.length<15)
		{
			self.location.replace ("?<% = varquery %>strProc=QQ&ord_no=" + vari );
			
		}else
			{
				alert("Ada kesalahan di server, hubungi bagian administrasi");
				frm.ord_no.value="";
				frm.ord_no.focus();

			}
		
	}
else
	{
		alert("Produk tidak ada ");
		frm.ord_no.value="";
		frm.ord_no.select();
		frm.ord_no.focus();
		return false;
	}
	
	//return false;
}
}

function jvSave()
{
	var temp,i,strXML,errr;
		var objXMLhttp = new ActiveXObject("Microsoft.XMLHTTP")
		var objXMLdom = new ActiveXObject("Microsoft.XMLDOM")
		objXMLdom.async=false;
			temp="";
			strXML = "<root>";
			strXML += "<data ";
			strXML += "fnc = '4' ";
			strXML += "strProc = '" + frm.strProc.value + "' ";
			strXML += "inv_cab= '<%= session("glb_usr_cab")	%>' ";
			strXML += "inv_no = '" + frm.inv_no.value + "' ";
			strXML += "inv_date = '" + frm.inv_date.value + "' ";
			strXML += "inv_duedate = '" + frm.inv_duedate.value + "' ";
			strXML += "inv_customer = '" +   jvConvert4XML(frm.inv_customer.value) + "' ";
			//strXML += "inv_bank_code = '" + frm.inv_bank_code.value + "' ";
//			strXML += "inv_bank_account_code = '" + frm.inv_bank_account_code.value + "' ";
			strXML += "inv_amount = '" + dotrovCent(frm.inv_ttl_trm.value) + "' ";
			strXML += "inv_account_slip_no ='" + frm.inv_account_slip_no.value  +"' ";
			strXML += "inv_delivery_no = '" + frm.inv_delivery_no.value + "' ";
			strXML += "inv_tax = '" + frm.inv_tax.value + "' ";
			strXML += "inv_remark = '" +   jvConvert4XML(frm.inv_remark.value) + "' ";
			strXML += "inv_fktPjk = '" +   (frm.inv_fktPjk.value) + "'  ";
			strXML += "inv_inuser = '<%= glb_usr_Code %>' >";
					
			var counter;
			counter = tabC.rows.length - 1;
			for (i=0; i<=tabC.rows.length-1  ;i++)
			{
				strXML +=" <detail ";
				strXML +="inv_seq = '" +(i+1) + "' ";
				strXML +="inv_seq2 = '" + tabC.rows(i).cells(0).innerText  + "' ";
				strXML +="inv_material = '" +  jvConvert4XML(tabC.rows(i).cells(1).innerText ) + "' ";
				if (dotrovCent(tabC.rows(i).cells(5).innerText) == 0) 
				{
					alert("Qty Terima tidak Boleh 0 !");
					return false;
				}

				strXML +="inv_qty = '" + dotrovCent(tabC.rows(i).cells(5).innerText) + "' ";
				strXML +="inv_up = '" + dotrovCent(tabC.rows(i).cells(3).innerText ) + "' ";
				strXML +="inv_DiscRate = '" + dotrovCent(tabC.rows(i).cells(7).innerText)  + "' ";
				strXML +="inv_Amt = '" + dotrovCent(tabC.rows(i).cells(6).innerText)  + "' ";
				strXML +="inv_dremark = '" + (tabC.rows(i).cells(10).innerText)  + "' ";
				strXML +="inv_total = '" + tabC.rows(counter).cells(0).innerText  + "' ";
				strXML +=" />";
			}
		strXML +="</data></root>";
		//diverr.innerText =strXML
		//return false;
		//alert(strXML);
		//return false;
		objXMLhttp.open ("POST", "tranP05XMLsave.asp",false);
		objXMLhttp.send(strXML);
		//diverr.innerHTML = objXMLhttp.responseText;
		//frm.inv_remark.value = objXMLhttp.responseText;
		arrtemp=objXMLhttp.responseText.split("~");

		if (arrtemp[0]=="true")
		{
				if (frm.strProc.value=="DD")
					{
						alert("Data Sudah Dihapus");
						self.location.replace("?<% = varquery %>strProc=NN");
					}
					else
					{
						alert("Data Sudah Disimpan");
//						self.location.replace("TRANP05L.ASP?strProc=QQ" + arrtemp[1]);
						self.location.replace("TRANP05L.ASP?<% = varquery %>strProc=QQ" );
					}
		}else
			{
				alert("ada kesalahan diserver, hubungi bagian adminstrasi \n " + arrtemp[1] );
				frm.inv_no.focus();
			}

}
//function jvQuery(param)
//{
//	if (param.value!= "")
//	{
//		frm.strProc.value = "QQ";
//		frm.submit();
//	}
//}

function jvCalc()
{
		hrg=dotrovCent(frm.inv_up.value ) * (frm.inv_qty.value ); 
		frm.inv_amtOri.value=jvCurrency(dotrov(hrg));
		//diverr.innerText = hrg
		amtDisc = dotrovCent(frm.inv_DiscRate.value) * 0.01 * hrg ;
		frm.inv_DiscAmt.value = jvCurrency(dotrov(amtDisc));
		hrg = hrg - amtDisc ;
		
		frm.inv_harga.value = jvCurrency( dotrov(hrg) );
		jvCurr(frm.inv_up);
		//jvCurrCent(frm.inv_qty);
		jvCurrCent(frm.inv_DiscRate);
}
function jvGlbDisc()
{
	if (parseInt(dotrovCent(frm.inv_GlbDisc.value)) != 0 ) 
		{
			frm.inv_DiscRate.value = jvCurrencyCent(frm.inv_GlbDisc.value) ;
			frm.inv_DiscRate.readOnly = true;
			frm.inv_GlbDisc.value =jvCurrencyCent(frm.inv_GlbDisc.value);
		}else
			{
				frm.inv_DiscRate.value = jvCurrencyCent(frm.inv_GlbDisc.value) ;
				frm.inv_DiscRate.readOnly = false;
				frm.inv_GlbDisc.value =jvCurrencyCent(frm.inv_GlbDisc.value);
			}
	
}
function jvEsc()
{
	self.location.replace("tranP05l.asp?<% = varquery %>")  
}
</script>
</HEAD>
<BODY >
<form name=frm action=? method=post>
<%
if strProc="" then
	'InpAttr=" disabled "	
	'SlctAttr=" disabled "
end if
if usr_code<>"" then InpAttrUsr=" disabled "
'or strProc="NN" 
subHeader "Faktur Jual"
'response.write strSQLy
	Response.Write "<div id=diverr></div>"
	SubTblTR "Y", TblClass, TblID,tblAlign,TblWidth,TblAttr
		SubINp "No. Faktur ", "text", "inv_no", 16, 16, inv_no, InpClass, InpOnclick, InpOnFocus, "", InpOnChange, ",jvQuery(this)", "", InpAttrUsr, "  "," "
		subtxt "[F1 - List] "
		SubINp "No. Pengeluaran Brg ", "text", "inv_delivery_no", 16, 16, inv_delivery_no, InpClass, InpOnclick, InpOnFocus, " ", InpOnChange, ",jvQuery(this)", InpOnKeyUp, InpAttrUsr, " colspan=2 "," "
		subtxt "[F1 - List] "
	SubTblTR "", TblClass, TblID,tblAlign,TblWidth,TblAttr		
	if len(inv_date) = 0 then inv_date = right("0" & day(Date()),2) & "-" & right("0" & month(date()),2) & "-" & year(date())
		subInpDt "Tgl Faktur","inv_date",inv_date,InpOnChange,InpClass, InpAttr, InpTdAttr,"1",InpOnBlur,InpOnKeyUp,InpOnFocus,InpKeyPress
	if len(inv_duedate) = 0 then inv_duedate = right("0" & day(Date()),2) & "-" & right("0" & month(date()),2) & "-" & year(date())
		subInpDt "Tgl Jatuh Tempo &nbsp;&nbsp;&nbsp;","inv_duedate",inv_duedate,InpOnChange,InpClass, InpAttr, "  ","1",InpOnBlur,InpOnKeyUp,InpOnFocus,InpKeyPress
	SubTblTR "", TblClass, TblID,tblAlign,TblWidth,TblAttr		
		SubINpDesc "Customer", "text","inv_customer",10,30,10,inv_customer,inv_customerdesc,InpClass,InpOnclick, InpOnFocus, "", InpOnChange, InpOnKeyPress, InpOnKeyUp, " readonly " , " colspan=2 ","Y",InpTdClose	

	SubTblTR "", TblClass, TblID,tblAlign,TblWidth,TblAttr	
	strSQL="select cod_code,cod_name from trade.t_m_code where cod_Head_code='TX' and cod_code<>'*'"
		subQuery Con,Rs,strSQL,CurSorLocation,CursorType,LockType
		if not rs.EOF then
			arrtax=rs.GetRows 
		end if
		rs.close
		SubSelect "Pajak", "inv_tax", SlcClass, "vbCalcPjk()", arrtax,trim( inv_tax), SlcDefault, TdAttr, SlctAttr, SlcOnKeyPress, SlcOnBlur, TRClose
		SubINp "Nilai Pajak", "currency", "dlv_tax", 12, 12, dlv_tax, InpClass, InpOnclick, InpOnFocus, " ", InpOnChange, "", InpOnKeyUp, " readonly ", "  "," "

	SubTblTR "", TblClass, TblID,tblAlign,TblWidth,TblAttr	
		SubINp "Global Discount", "numeric", "inv_GlbDisc", 5, 5, inv_GlbDisc, InpClass, InpOnclick, InpOnFocus, " ,jvGlbDisc()", InpOnChange, "", InpOnKeyUp, InpAttrUsr, " colspan=2 "," "
		subtxt " %  "
	SubTblTR "", TblClass, TblID,tblAlign,TblWidth,TblAttr		
	strSQL="select 	'1','Code 1' union all  select '8','Code 8'   "
		subQuery Con,Rs,strSQL,CurSorLocation,CursorType,LockType
		if not rs.EOF then
			arrtax=rs.GetRows 
		end if
		rs.close
		SubSelect "Faktur Pajak", "inv_fktPjk", SlcClass, "", arrtax,trim( inv_fktPjk), SlcDefault, TdAttr, SlctAttr, SlcOnKeyPress, SlcOnBlur, TRClose

		
	SubTblTR "", TblClass, TblID,tblAlign,TblWidth,TblAttr		
		SubINp "Keterangan", "text", "inv_remark", 50, 50, inv_remark, InpClass, InpOnclick, InpOnFocus, InpOnBlur, InpOnChange, "", InpOnKeyUp, InpAttrUsr, "  colspan=2 "," "
	SubTblTR "", TblClass, TblID,tblAlign,TblWidth,TblAttr
		SubTD "<b>Harga Pengiriman ke Customer", 2, TDRowspan, TDClass,TDATTRIB
		SubTD "<b>Harga Pada Saat Barang Diterima Customer", 2, TDRowspan, TDClass,TDATTRIB
	SubTblTR "", TblClass, TblID,tblAlign,TblWidth,TblAttr		
		SubINp "Harga", "currency", "inv_hrgkrm", 18, 18, inv_hrgkrm, InpClass, InpOnclick, InpOnFocus, InpOnBlur, InpOnChange, "", InpOnKeyUp, "readonly", "  "," "
		SubINp "Harga", "currency", "inv_hrgtrm", 18, 18, inv_hrgtrm, InpClass, InpOnclick, InpOnFocus, InpOnBlur, InpOnChange, "", InpOnKeyUp, "readonly", " colspan=2 "," "	
	SubTblTR "", TblClass, TblID,tblAlign,TblWidth,TblAttr		
		SubINp "Discount", "currency", "inv_ttldisc_krm", 18, 18, inv_ttldisc_krm, InpClass, InpOnclick, InpOnFocus, InpOnBlur, InpOnChange, "", InpOnKeyUp, "readonly", "  "," "
		SubINp "Discount", "currency", "inv_ttldisc_trm", 18, 18, inv_ttldisc_trm, InpClass, InpOnclick, InpOnFocus, InpOnBlur, InpOnChange, "", InpOnKeyUp, "readonly", " colspan=2 "," "			
	SubTblTR "", TblClass, TblID,tblAlign,TblWidth,TblAttr		
		SubINp "Pajak", "currency", "inv_ttlPjk_krm", 18, 18, inv_ttlPjk_krm, InpClass, InpOnclick, InpOnFocus, InpOnBlur, InpOnChange, "", InpOnKeyUp, "readonly", "  "," "
		SubINp "Pajak", "currency", "inv_ttlPjk_trm", 18, 18, inv_ttlPjk_trm, InpClass, InpOnclick, InpOnFocus, InpOnBlur, InpOnChange, "", InpOnKeyUp, "readonly", " colspan=2 "," "				
	SubTblTR "", TblClass, TblID,tblAlign,TblWidth,TblAttr		
		SubINp "Total", "currency", "inv_ttl_krm", 18, 18, inv_ttl_krm, InpClass, InpOnclick, InpOnFocus, InpOnBlur, InpOnChange, "", InpOnKeyUp, "readonly", "  "," "
		SubINp "Total", "currency", "inv_ttl_trm", 18, 18, inv_ttl_trm, InpClass, InpOnclick, InpOnFocus, InpOnBlur, InpOnChange, "", InpOnKeyUp, "readonly", " colspan=2 "," "					
		
		'hidden
	SubTblTR "", TblClass, TblID,tblAlign,TblWidth,TblAttr		
		SubINp "Acc Code", "readonly", "inv_account_slip_no", 20, 20, inv_account_slip_no, InpClass, InpOnclick, InpOnFocus, InpOnBlur, InpOnChange, "", InpOnKeyUp, InpAttrUsr, "   "," "
		
	subtblclose	
		%>
		<div id="tblhead1" style="border:solid black 0px;z-index:2;width:570;overflow-X:hidden;overflow-y:hidden" >		
		<table height=40 class=GrdHead width=100% cellpadding=2 CELLSPACING=0 border=1 borderColorLight=#666666 borderColorDark=white   style="background-color:#ffffff">
			<COL WIDTH=35 align=center><!--No-->
			<COL WIDTH=105 align=center><!--Kode Produk-->
			<COL WIDTH=175 align=center style="display:none" ><!--Deskripsi-->
			<COL WIDTH=80 align=center><!--Harga Satuan-->
			<COL  WIDTH=70 align=center><!--QTY Kirim-->
			<COL  WIDTH=70 align=center><!--QTY Diterima-->
			<COL WIDTH=100 align=center><!--Harga-->
			<COL WIDTH=60 align=center  style="display:none"><!--Disc-->
			<COL WIDTH=110 align=center  ><!--Disc Amt-->
			<COL WIDTH=100 align=center  style="display:none"><!--Harga terima-->
			<!-- <col width =40><!--Del-->
			<tr class=text1 style="font-weight:bold;color:#666666" bgcolor=#B5BED6 height=20>
				<td align=center >
					No
				</td>
				<td align=center >
					Kode Produk
				</td>
				<td align=center >
					Deskripsi
				</td>
				<td align=center >
					Harga Satuan
				</td>
				<td align=center >
					Qty Kirim
				</td>
				<td align=center >
					Qty Diterima
				</td>
				<td align=center >
					Harga
				</td>
				<td align=center >
					Disc. (%)
				</td>
				<td align=center >
					Nilai Disc.
				</td>
				<td align=center >
					Harga Terima
				</td>
				<td align=center >
					Remark
				</td>
				<!--<td align=center >
					
				</td> -->
				</tr>
		</table>
		</div>
		<div  id="tblcontent1"  onscroll="scrlTbl(tblcontent1,tblhead1)" 
		style="z-index:1;border:inset 1.5px;width:570;height:150;overflow-y:scroll;overflow-x:scroll" >
		<table  id="tabC"  class=text1 bgcolor=#e1e1e1  bordercolor="#999999" style="cursor:hand;background-color:white;border-collapse:collapse;table-layout:fixed" 
		cellpadding=2 CELLSPACING=0  border=1 bordercolor=black  onmouseover="tabCover()" onmouseout="tabCout()" >
			<COL WIDTH=33 align=center><!--No-->
			<COL WIDTH=105 align=center ><!--Kode Produk-->
			<COL WIDTH=175 align=left  style="display:none" ><!--Deskripsi-->
			<COL WIDTH=80 align=right><!--Harga Satuan-->
			<COL  WIDTH=70 align=right><!--QTY Kirim-->
			<COL  WIDTH=70 align=right><!--QTY Diterima5-->
			<COL WIDTH=100 align=right><!--Harga-->
			<COL WIDTH=60 align=right  style="display:none"><!--Disc7-->
			<COL WIDTH=90 align=right  ><!--Disc Amt-->
			<COL WIDTH=100 align=right  style="display:none"><!--Harga Terima9-->
			<COL WIDTH=100 align=right  style="display:none"><!--Remark-->
			<!-- <col width =20> -->
			<%
				totalAMT=0
				if len(strSQLy)>0 then
					on error resume next
					
					rs.open strSQLy,con,1,3
					'response.write strSQLy
					if not rs.EOF then
						arrDtl = rs.GetRows
						for i=0 to ubound(arrDtl,2) 
							totalAMT = totalAMT + ccur(arrDtl(8,i))
						if arrDtl(12,i) = "0" then 
								response.write "<tr  >" & vbcrlf
						else	
								response.write "<tr style='color:blue;' >" & vbcrlf						
						end if 
													
'							Response.Write "<tr>"
							Response.Write "<td>"
							Response.Write arrDtl(10,i) 
							Response.Write "</td>"
							Response.Write "<td>"
							Response.Write arrDtl(0,i) ' kd prod
							Response.Write "</td>"
							Response.Write "<td>"
							Response.Write arrDtl(1,i) ' desc prd
							Response.Write "</td>"
							Response.Write "<td>"
							Response.Write formatNumber(arrDtl(2,i),0) 'u/p
							Response.Write "</td>"
							Response.Write "<td>"
							Response.Write formatNumber(arrDtl(3,i),3) ' qty kirim
							Response.Write "</td>"
							Response.Write "<td>"
							Response.Write formatNumber(arrDtl(4,i),3) ' qty terima
							Response.Write "</td>"
							Response.Write "<td>"
							Response.Write formatNumber(arrDtl(5,i),0) ' hrg
							Response.Write "</td>"
							Response.Write "<td>"
							Response.Write formatNumber(arrDtl(6,i),2) ' disc rate
							Response.Write "</td>"
							Response.Write "<td>"
							Response.Write formatNumber(arrDtl(7,i),2) ' disc amt
							Response.Write "</td>"
							Response.Write "<td>"
							Response.Write formatNumber(arrDtl(8,i),0) ' total
							Response.Write "</td>"
							Response.Write "<td>"
							Response.Write arrDtl(11,i)' remark
							Response.Write "</td>"
							Response.Write "</tr>"
						next
					end if
					rs.close
				end if
			%>
		
		</table>	
		</div>
<div id="tblfoot" style="border:solid black 0px;z-index:2;width:570;overflow-X:hidden;overflow-y:hidden" >
	<table class=GrdHead style="table-layout:fixed" id=tabH cellpadding=2 Height=40 CELLSPACING=0 border=1 borderColorLight=#666666 borderColorDark=white   style="background-color:'#B5BED6'" >
			<COL WIDTH=35 align=center><!--No-->
			<COL WIDTH=105 align=center><!--Kode Produk-->
			<COL WIDTH=175 align=center style="display:none" ><!--Deskripsi-->
			<COL WIDTH=80 align=center><!--Harga Satuan-->
			<COL  WIDTH=70 align=center><!--QTY Kirim-->
			<COL  WIDTH=70 align=center><!--QTY Diterima-->
			<COL WIDTH=100 align=center><!--Harga-->
			<COL WIDTH=60 align=center  style="display:none"><!--Disc-->
			<COL WIDTH=70 align=center  ><!--Disc Amt-->
			<COL WIDTH=100 align=center  style="display:none"><!--Harga terima-->
			<COL WIDTH=100 align=center  style="display:none"><!--Remark-->
			<col width =40><!--Del-->

		<tr>
			<td colspan=5  style="color:red" rowspan=2 align=right><span id='deskripsi'>&nbsp;</span></td>
			<td align=right >Total</td>
			<td align=right style="color:red" colspan=2><span id='totalAMT'><%=formatnumber(totalAMT,2) %></span></td>
		</tr>

	</table>
</div>
		<input type=hidden name="grdRowAct" value="">
		<input type=hidden name="grdRowActOver" value="">

		<%	
	SubTblTR "Y", TblClass, TblID,tblAlign,TblWidth,TblAttr
		SubINpDesc "Kode Barang", "text","inv_material",20,30,20,inv_material,inv_materialdesc,InpClass,InpOnclick, InpOnFocus, "", InpOnChange, InpOnKeyPress, InpOnKeyUp, InpAttr, " colspan=2 ","Y",InpTdClose
	SubTblTR "", TblClass, TblID,tblAlign,TblWidth,TblAttr		
		SubINp "Harga Satuan", "currency", "inv_up", 15, 15, inv_up, InpClass, InpOnclick, ",this.select()", ",jvCalc()", InpOnChange, "", InpOnKeyUp, "readonly", "  "," "
'		SubTblTR "", TblClass, TblID,tblAlign,TblWidth,TblAttr		
			SubINp "Qty Terima", "numeric", "inv_qty", 9, 9, inv_qty, InpClass, InpOnclick, ",this.select()", ",jvCalc()", InpOnChange, "", InpOnKeyUp, InpAttrUsr, "  "," "
			subtxt "<span id='prdunit'></span>"
		SubTblTR "", TblClass, TblID,tblAlign,TblWidth,TblAttr		
			SubINp "Harga", "currency", "inv_amtOri", 15, 15, inv_amtOri, InpClass, InpOnclick, InpOnFocus, InpOnBlur, InpOnChange, "", InpOnKeyUp, "readonly", "  "," "

		SubTblTR "", TblClass, TblID,tblAlign,TblWidth,TblAttr		
			SubINp "Discount ", "text", "inv_DiscRate", 10, 10, inv_DiscRate, InpClass, InpOnclick, ",this.select()", ",jvCalc()", InpOnChange, "", InpOnKeyUp, InpAttrUsr, "  "," "
			SubINp "", "currency", "inv_DiscAmt", 15, 15, inv_DiscAmt, InpClass, InpOnclick, ",this.select()", ",jvCalc()", InpOnChange, "", InpOnKeyUp, "readonly", "  ",""
'		SubTblTR "", TblClass, TblID,tblAlign,TblWidth,TblAttr		
			SubINp "Harga Terima", "currency", "inv_harga", 15, 15, inv_harga, InpClass, InpOnclick, ",this.select()", ",jvCalc()", InpOnChange, "", InpOnKeyUp,  " readonly " , "  "," "
		SubTblTR "", TblClass, TblID,tblAlign,TblWidth,TblAttr		
				SubINp "Keterangan", "text", "ord_remark_dtl", 10, 10, ord_remark_dtl, InpClass, InpOnclick, InpOnFocus, InpOnBlur, InpOnChange, "", InpOnKeyUp, InpAttrUsr, " colspan=2 "," "	
		SubTblTR "", TblClass, TblID,tblAlign,TblWidth,TblAttr		
			SubButton " Insert ","insRow()"
			subtblclose
subFooter
%>
</form>

<script language="vbScript">

rowActive=1
numRows=1

	'______________________________
	private function tabC_onmouseover()
			rows=tabC.rows    
			if window.event.srcElement.tagName ="TD" or window.event.srcElement.tagName = "td" then
					set e=window.event.srcElement.parentElement
					rowInd=e.rowIndex
					rowActive=rowInd
					frm.grdRowActOver.value=rowInd
					
					set oRow								= tabC.rows(rowInd)
					deskripsi.innerText=left(oRow.cells(2).innerText,50)
			end if      
	end function    
	'______________________________
	private function tabC_onmouseout()
			rows=tabC.rows    
			if window.event.srcElement.tagName ="TD" or window.event.srcElement.tagName = "td" then
					set e=window.event.srcElement.parentElement
			end if      
								deskripsi.innerText=" "
	end function 
		'______________________________
	function vbInsOn()
			frm.btnIns.disabled=false
		end function
  
	'______________________________
	private function tabC_onclick()
			rows=tabC.rows
			if window.event.srcElement.tagName ="TD" or window.event.srcElement.tagName = "td" then
				if window.event.srcElement.ID<>"cellDel" then
					set e=window.event.srcElement.parentElement
					rowInd=e.rowIndex
					rowActive=rowInd
					frm.grdRowAct.value=rowInd

					set oRow									= tabC.rows(rowInd)
					frm.inv_material.value			= oRow.cells(1).innerText
					frm.inv_materialdesc.value	= oRow.cells(2).innerText
					frm.inv_up.value 					= oRow.cells(3).innerText
					'prdunit.innerText					= oRow.cells(4).innerText
					frm.inv_qty.value					= oRow.cells(5).innerText
					frm.inv_amtOri.value				= oRow.cells(6).innerText
					if frm.inv_DiscRate.readOnly=false then 
						frm.inv_DiscRate.value 			= oRow.cells(7).innerText
					end if 
					frm.inv_DiscAmt.value 			= oRow.cells(8).innerText
					frm.inv_harga.value				= oRow.cells(9).innerText
					
					frm.ord_remark_dtl.value = oRow.cells(10).innerText
					'msgbox oRow.cells(10).innerText
					frm.inv_material.focus() 
				else
						functDelRow tabC,window.event.srcElement.parentElement.rowIndex,frm.inv_material 
						frm.inv_material.focus() 
				end if
			else
	
			end if
		end function
'____________________________________________		
	function insRow()
		dim i	
	if frm.inv_material.value ="" or frm.inv_materialdesc.value ="" or frm.inv_qty.value="" then 
		msgbox "Produk dan jumlah terima harus diisi "
		frm.inv_material.focus()
	else
		if  frm.grdRowAct.value<>"" then
					
					dim iRow
					iRow=cint(frm.grdRowAct.value)
					set oRow = tabC.rows(iRow)
					
		else
				
				if tabC.rows.length>0 then
				
						for i=0 to tabC.rows.length-1
							
							
							vDocu	= tabC.rows(i).cells(1).innerText
							if trim(frm.inv_material.value) = trim(vDocu) then
								msgbox "Data document ada yg double"
								frm.inv_material.focus()
								exit function
							end if
						next
				end if		
						set oRow = tabC.insertRow()
						g = oRow.rowIndex
				
						for i = 0 to  16
						  set oCell = oRow.insertCell()
						next
						'oRow.cells(0).innerText=g+1
				
				
					
					
			end if
			
						oRow.cells(1).innerText= frm.inv_material.value
						oRow.cells(2).innerText= frm.inv_materialdesc.value
						oRow.cells(3).innerText= frm.inv_up.value
						'oRow.cells(4).innerText= prdunit.innerText
						oRow.cells(5).innerText= formatnumber(frm.inv_qty.value ,3)
						oRow.cells(6).innerText= frm.inv_amtOri.value
						
						oRow.cells(7).innerText= frm.inv_DiscRate.value
						oRow.cells(8).innerText= frm.inv_DiscAmt.value
						oRow.cells(9).innerText= frm.inv_Harga.value
						oRow.cells(10).innerText= frm.ord_remark_dtl.value
					'	msgbox oRow.cells(10).innerText
						totalAMT.innerText=0
						for i=0 to tabC.rows.length-1
							totalAMT.innerText = ccur(replace(totalAMT.innerText,",","")) + ccur(replace(tabC.rows(i).cells(9).innerText,",",""))
						next
						totalAMT.innerText = formatnumber(totalAMT.innerText,2)
'						totalAMTq=0
'						totalDISCq=0
'						for i=0 to tabC.rows.length-1
'									totalAMTq = totalAMTq + dotrov(tabC.rows(i).cells(6).innerText)
'									totalDISCq=totalDISCq + dotrov(tabC.rows(i).cells(8).innerText)
'						next
'									frm.inv_hrgtrm.value=formatNumber(totalAMTq,0)
'									frm.inv_ttldisc_trm.value=formatNumber(totalDISCq,0)
'									hargaSetelahDisc = totalAMTq - totalDISCq
'						select case frm.inv_tax.value
'						case "0"
'							Vinv_ttlPjk_trm=0
'							frm.inv_ttlPjk_trm.value= 0
'							frm.inv_ttl_trm.value= formatNumber(hargaSetelahDisc,0)
'						case "1"
'							Vinv_ttlPjk_trm=0.1 * ( dotrov(frm.inv_hrgtrm.value) - totalDISCq )
'							frm.inv_ttlPjk_trm.value= formatNumber(Vinv_ttlPjk_trm,0)
'							frm.inv_ttl_trm.value=  formatNumber(1.1 * hargaSetelahDisc,0)
'						case "2"
'							Vinv_ttlPjk_trm=( dotrov(frm.inv_hrgtrm.value) - totalDISCq )/1.1
'							frm.inv_ttlPjk_trm.value= formatNumber(Vinv_ttlPjk_trm/11 + totalDISCq ,0)
'							frm.inv_ttl_trm.value=  formatNumber(hargaSetelahDisc,0)
'						end select
						
					vbCalcPjk()
									
						
						
						if  frm.grdRowAct.value="" then
						'	oRow.cells(15).innerText= "X"
						'	oRow.cells(15).ID="cellDel"
						else
						end if
						
						numRows = numRows + 1
						rowActive = rowActive + 1
						oRow.scrollIntoView
						vbBlnkInp()
						frm.inv_material.focus()
		end if 

		end function			
'______________________________
function vbCalcPjk()
	'invoice tax
			totalAMTq=0
			totalDISCq=0
			for i=0 to tabC.rows.length-1
						totalAMTq = totalAMTq + ((dotrovCent(tabC.rows(i).cells(3).innerText)  * dotrovCent(tabC.rows(i).cells(5).innerText)) )
						totalDISCq=totalDISCq + dotrovCent(tabC.rows(i).cells(8).innerText)
			next
						frm.inv_hrgtrm.value=formatNumber(totalAMTq,0)
						frm.inv_ttldisc_trm.value=formatNumber(totalDISCq,0)
						hargaSetelahDisc = totalAMTq - totalDISCq
			'MSGBOX   totalDISCq
			select case frm.inv_tax.value
				case "0"
					Vinv_ttlPjk_trm=0
					frm.inv_ttlPjk_trm.value= 0
					frm.inv_ttl_trm.value= formatNumber(hargaSetelahDisc,0)
				case "1"
					Vinv_ttlPjk_trm=0.1 * ( (frm.inv_hrgtrm.value) - totalDISCq )
					frm.inv_ttlPjk_trm.value= formatNumber(Vinv_ttlPjk_trm,0)
					frm.inv_ttl_trm.value=  formatNumber(1.1 * hargaSetelahDisc,0)
					frm.inv_ttldisc_krm.value=formatNumber(totalDISCq + Vinv_ttlPjk_krm,0)
				case "4"
					Vinv_ttlPjk_trm=0.11 * ( (frm.inv_hrgtrm.value) - totalDISCq )
					frm.inv_ttlPjk_trm.value= formatNumber(Vinv_ttlPjk_trm,0)
					frm.inv_ttl_trm.value=  formatNumber(1.1 * hargaSetelahDisc,0)
					frm.inv_ttldisc_krm.value=formatNumber(totalDISCq + Vinv_ttlPjk_krm,0)					
				case "2"
					Vinv_ttlPjk_trm=totalAMTq - (totalAMTq/1.1)
					frm.inv_ttlPjk_trm.value= formatNumber(Vinv_ttlPjk_trm ,0)
					if totalDISCq = 0 then 
						frm.inv_ttldisc_trm.value=formatNumber(Vinv_ttlPjk_trm ,0)
					else
						frm.inv_ttldisc_krm.value=formatNumber(totalDISCq + Vinv_ttlPjk_krm,0)
						
					end if 
					frm.inv_ttl_trm.value=  formatNumber(hargaSetelahDisc,0)
			end select
			'delivery tax
						totalAMTq=0
						totalDISCq=0
						for i=0 to tabC.rows.length-1
									totalAMTq = totalAMTq +  (dotrovCent(tabC.rows(i).cells(3).innerText)  * dotrovCent(tabC.rows(i).cells(4).innerText) ) 
'									totalDISCq=totalDISCq + dotrov(tabC.rows(i).cells(8).innerText)
						next
									frm.inv_hrgkrm.value=formatNumber(totalAMTq,0)
									frm.inv_ttldisc_krm.value=formatNumber(totalDISCq,0)
									hargaSetelahDisc = totalAMTq - totalDISCq
						'totalAMTq=0
						'totalDISCq=0

						select case frm.dlv_tax.value
						case "0"
							Vinv_ttlPjk_krm=0
							frm.inv_ttlPjk_krm.value= 0
							frm.inv_ttl_krm.value= formatNumber(hargaSetelahDisc,0)
						case "1"
							Vinv_ttlPjk_krm=0.1 * ( (frm.inv_hrgkrm.value) - totalDISCq )
							frm.inv_ttlPjk_krm.value= formatNumber(Vinv_ttlPjk_krm,0)
							frm.inv_ttl_krm.value=  formatNumber(1.1 * hargaSetelahDisc,0)							
						case "4"
							Vinv_ttlPjk_krm=0.11 * ( (frm.inv_hrgkrm.value) - totalDISCq )
							frm.inv_ttlPjk_krm.value= formatNumber(Vinv_ttlPjk_krm,0)
							frm.inv_ttl_krm.value=  formatNumber(1.1 * hargaSetelahDisc,0)
						case "2"
							Vinv_ttlPjk_krm=hargaSetelahDisc/11
							frm.inv_ttlPjk_krm.value= formatNumber(Vinv_ttlPjk_krm ,0)
							frm.inv_ttldisc_krm.value=formatNumber(totalDISCq + Vinv_ttlPjk_krm,0)
							frm.inv_ttl_krm.value=  formatNumber(hargaSetelahDisc,0)
						end select
						
end function						
'_______________________________________						
		function vbBlnkInp()

					frm.inv_material.value			= ""
					frm.inv_materialdesc.value		= ""
					frm.inv_up.value 					= ""
					frm.inv_qty.value					= ""
					frm.inv_amtOri.value				= ""

					'frm.inv_DiscRate.value 			= ""
					frm.inv_DiscAmt.value 			= ""
					frm.inv_harga.value				= ""

			end function
'______________________________		
		function functDelRow(tblID,param,prm)
					set rows = tblID.rows
					tempIndex=cint(param)
					
					if tempIndex=0 then
					tblID.rows(tempIndex).cells(0).scrollIntoView
					end if
					
					
					tblID.deleteRow(tempIndex)
					rowActive=rowActive-1
					'sortNum(tblID)
					vbBlnkInp()
					prm.focus()	
				
			end function	
'______________________________
			function sortNum(tblID)
			dim i 
				set rows = tblID.rows
				
				for i=0 to rows.length-1
					rows(i).cells(0).innerText=i+1 
				next
			end function
	
</script>

<script language=javascript>
if (frm.inv_no.value=="" )
	{
		if(frm.strProc.value!="QQ")
		{
		if (frm.inv_delivery_no.value !="")
		{
			//frm.inv_no.readOnly = true;
			frm.inv_date.focus();
		}else
			{
				frm.inv_delivery_no.focus();
			}
		}else
			{
				frm.inv_no.focus();
			}
	}else
		{
			frm.inv_date.focus();
			//frm.inv_no.readOnly=true;
			frm.inv_delivery_no.readOnly  = true;
		}
		vbCalcPjk()
		
</script>
</BODY>
</HTML>
<%
set rs		= nothing
set con	= nothing

'________________________________________________________________________________________________________________________
 Sub SubTblTR(NewTableTR, TblClass, TblID,tblAlign,TblWidth,TblAttr)
    If LCase(NewTableTR) = "y" Then
        response.write   "<table "
        if len(TblAttr)=0 then
					response.write   "cellPadding=1 cellSpacing=0  border=0 " 
        else
					response.write   TblAttr & " "
        end if
        if TblID<>"" then
				response.write   " id='" & TblID & "' "
        end if
        if TblWidth<>"" then
					response.write "width='" & TblWidth & "'" 
        end if
        if TblClass<>"" then
					response.write "class='" & TblClass & "'" 
				else
					response.write "class='text1'" 	
        end if
        response.write ">" & vbCrLf
        response.write   "<tr >" & vbCrLf
    Else
        response.write   "<tr "
        if TblClass<>"" then
        response.write "class='" & TblClass & "' " 
        end if
        if len(TblAttr)>0 then
        response.write TblAttr & " "
        end if
        response.write ">" & vbCrLf
    End If
  
End Sub
'___________________________________________________________________________________________
%>

%>