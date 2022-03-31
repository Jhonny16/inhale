# -*- coding: utf-8 -*-
# from odoo import http


# class L10nCrInhale(http.Controller):
#     @http.route('/l10n_cr_inhale/l10n_cr_inhale/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_cr_inhale/l10n_cr_inhale/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_cr_inhale.listing', {
#             'root': '/l10n_cr_inhale/l10n_cr_inhale',
#             'objects': http.request.env['l10n_cr_inhale.l10n_cr_inhale'].search([]),
#         })

#     @http.route('/l10n_cr_inhale/l10n_cr_inhale/objects/<model("l10n_cr_inhale.l10n_cr_inhale"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_cr_inhale.object', {
#             'object': obj
#         })
