# -*- coding: utf-8 -*-
from odoo import http

# class /data/iguItDev/iguActreport(http.Controller):
#     @http.route('//data/igu_it_dev/igu_actreport//data/igu_it_dev/igu_actreport/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('//data/igu_it_dev/igu_actreport//data/igu_it_dev/igu_actreport/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('/data/igu_it_dev/igu_actreport.listing', {
#             'root': '//data/igu_it_dev/igu_actreport//data/igu_it_dev/igu_actreport',
#             'objects': http.request.env['/data/igu_it_dev/igu_actreport./data/igu_it_dev/igu_actreport'].search([]),
#         })

#     @http.route('//data/igu_it_dev/igu_actreport//data/igu_it_dev/igu_actreport/objects/<model("/data/igu_it_dev/igu_actreport./data/igu_it_dev/igu_actreport"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('/data/igu_it_dev/igu_actreport.object', {
#             'object': obj
#         })