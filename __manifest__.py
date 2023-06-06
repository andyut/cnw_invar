# -*- coding: utf-8 -*-
{
    'name': "Indoguna-Invoice AR Report (WebApps 2)",

    'summary': """
        Indoguna-Invoice AR (WebApps 2)""",

    'description': """
        Accounting Report (WebApps 2)
    """,

    'author': "Indoguna Utama, Andy Utomo",
    'website': "http://www.indoguna.co.id",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'extra',
    'version': '0.1.1',
    'application': True,


    # any module necessary for this one to work correctly
    'depends': ['base','mail','cnw_telegram','cnw_numbering'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/user_groups.xml',
        'jas_views/saldopiutangdetail_views.xml',
        'jas_views/kartupiutang_views.xml',
        'jas_views/dolist_views.xml',
        'jas_views/kartupiutangmdl_views.xml',
        'jas_views/kartupiutangmdl2_views.xml',
        'jas_views/jas_invoiceb1logo_views.xml',
        'jas_views/jas_invoicec2long_views.xml',
        'jas_views/jas_invoicec4short_views.xml',
        'jas_views/cetakan_invoice_views.xml',
        'jas_views/cetakan_invoice2_views.xml',
        'jas_views/cetakan_invoice3_views.xml',
        'jas_views/cetakan_invoice4_views.xml',
        'inv_views/invoice_wizard_views.xml', 
        'inv_views/invoice_list_views.xml',
        'inv_views/invoice_fp_list_views.xml',
        'inv_views/invoice_fp_setting_views.xml',
        'inv_views/invoice_scanfp_views.xml',
        'inv_views/lap_tfbk_views.xml',
        'inv_views/lap_proyeksi_views.xml',
        'inv_views/lap_proyeksisummary_views.xml',
        'inv_views/invoice_updatefp_views.xml',
        'inv_views/invoice_fpchecklist_wiz_models.xml',
        'inv_views/inv_saldopiutangdetailemail.xml',
        'inv_views/jas_lap_emailaddress_views.xml',
        'ar_views/sap_penjualandetailitem_views.xml',
        'ar_views/sap_penjualandetail_views.xml',
        'inv_views/invoice_item_views.xml',
        'inv_views/invoice_item_wizard_views.xml',
        'inv_views/ar_collector_views.xml',
        'inv_views/ar_jalur_views.xml',
        'inv_views/invoice_tfprint.xml',
        'inv_views/invoice_checklist_wiz_models.xml',
        'inv_views/saldopiutangmodels_views.xml',
        'inv_views/audittrail_views.xml',
        #'inv_views/sap_do_notinvoice.xml',
        'tf_views/tf_wizard_views.xml',
        'ar_views/sap_bp.xml',
        'ar_views/sap_bp_outlet.xml',
        'ar_views/sap_bp_contact.xml',
        'ar_views/sap_bp_contact_get.xml',
        'tf_views/tf_views.xml',
        'tf_views/tf_wizard_views.xml',
        'tf_views/tagihan_number.xml',
        'ar_views/sap_do_notinvoice.xml',
        'ar_views/sap_inv_notkwitansi.xml', 
        'ar_views/sap_rincian_ar.xml',
        'ar_views/cnw_followup.xml',
        'ar_views/cnw_followup_report.xml',
        'ar_views/cnw_followup_number.xml',
        'ar_views/sap_bp_tfnotes.xml',
        'ar_views/cnw_followup_wizard.xml', 
        'kwt_models/kwt_numbering.xml', 
        'kwt_models/kwt_wizard_views.xml', 
        'kwt_models/kwt_views.xml', 
        'inv_views/cnw_home.xml',
        'menu/act-menu.xml', 
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}