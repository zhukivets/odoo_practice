from odoo import models, fields

class LibraryCopy(models.Model):
    _name = 'library.copy'
    _description = 'Physical Copy of a Book'
    _rec_name = 'inventory_number'

    book_id = fields.Many2one(
        'library.book', 
        string='Book', 
        required=True, 
        ondelete='restrict'
    )
    inventory_number = fields.Char(string='Inventory Number', required=True)
    condition = fields.Selection([
        ('new', 'New'),
        ('good', 'Good'),
        ('damaged', 'Damaged')
    ], string='Condition', default='good', required=True)
    loan_ids = fields.One2many('library.loan', 'copy_id', string='Loans History')
