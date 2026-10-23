from odoo import models, fields

class LibraryBook(models.Model):
    _name = 'library.book'
    _description = 'Library Book'

    name = fields.Char(string='Title', required=True)
    author = fields.Char(string='Author', required=True)
    isbn = fields.Char(string='ISBN')
    publish_year = fields.Integer(string='Publish Year')
    copy_ids = fields.One2many('library.copy', 'book_id', string='Copies')
