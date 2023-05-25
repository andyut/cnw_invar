                    select  
                                   a.cardcode ,
                                   b.cardname ,
                                   b.CntctPrsn ,
                                   b.LicTradNum npwp,
                                   b.U_AR_Person ,
                                   b.balance ,
                                   b.U_locktimeout,
                                   a.DocNum ,
                                   convert(varchar,a.docdate,23) docdate,
                                   a.NumAtCard so_number,
                                   a.U_IDU_FPajak ,
                                   a.U_Kw_No,
                                   a.DocTotal ,
                                   a.DocTotal - a.paidsys invoice_balance 


                    from OINV A 
                        inner join ocrd b on a.cardcode = b.cardcode 
                    where a.canceled='N'
                        and a.doctotal - a.paidsum <>0
                        and a.DocStatus ='O' 
                        and convert(varchar,DATEADD(month,-1 * isnull(b.u_locktimeout,2) ,convert(varchar,getdate(),112)) ,112)>= convert(varchar,a.docdate,112) 
                        --and b.u_lockstatus<>'pass'  
                        AND A.CARDCODE ='UM0864'
                order by a.cardcode, a.docdate   