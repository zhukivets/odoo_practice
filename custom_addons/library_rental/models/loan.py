from odoo import models, fields

class LibraryLoan(models.Model):
    _name = 'library.loan'
    _description = 'Book Rental / Loan'

    copy_id = fields.Many2one(
        'library.copy', 
        string='Book Copy', 
        required=True, 
        ondelete='restrict'
    )
    member_id = fields.Many2one(
        'library.member', 
        string='Member', 
        required=True, 
        ondelete='restrict'
    )
    loan_date = fields.Date(string='Loan Date', default=fields.Date.context_today, required=True)
    due_date = fields.Date(string='Due Date', required=True)
    return_date = fields.Date(string='Return Date')
    state = fields.Selection([
        ('active', 'Active'),
        ('returned', 'Returned')
    ], string='Status', default='active', required=True)
