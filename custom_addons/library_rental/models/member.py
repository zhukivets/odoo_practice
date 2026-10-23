from odoo import models, fields

class LibraryMember(models.Model):
    _name = 'library.member'
    _description = 'Library Member'
    _inherits = {'res.partner': 'partner_id'}

    partner_id = fields.Many2one(
        'res.partner', 
        string='Partner', 
        required=True, 
        ondelete='cascade'
    )
    membership_number = fields.Char(string='Membership Number', required=True, copy=False)
    loan_ids = fields.One2many('library.loan', 'member_id', string='Loans')