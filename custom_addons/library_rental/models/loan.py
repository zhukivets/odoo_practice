from datetime import timedelta
from odoo import api, fields, models
from odoo.exceptions import ValidationError

LOAN_DAYS = 14
FINE_PER_DAY = 5.0


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
    due_date = fields.Date(string='Due Date', compute='_compute_due_date', store=True)
    return_date = fields.Date(string='Return Date')
    state = fields.Selection([
        ('active', 'Active'),
        ('returned', 'Returned')
    ], string='Status', default='active', required=True)
    fine_amount = fields.Float(string='Fine', compute='_compute_fine_amount', store=True)
    is_overdue = fields.Boolean(string='Overdue', compute='_compute_is_overdue')

    # ---------- Computed fields ----------
    @api.depends('loan_date')
    def _compute_due_date(self):
        for rec in self:
            if rec.loan_date:
                rec.due_date = rec.loan_date + timedelta(days=LOAN_DAYS)
            else:
                rec.due_date = False

    @api.depends('due_date', 'return_date', 'state')
    def _compute_fine_amount(self):
        # fine only for RETURNED OVERDUE loans
        for rec in self:
            if rec.state == 'returned' and rec.return_date and rec.due_date \
                    and rec.return_date > rec.due_date:
                rec.fine_amount = (rec.return_date - rec.due_date).days * FINE_PER_DAY
            else:
                rec.fine_amount = 0.0

    # non-stored: depends on today's date
    @api.depends('due_date', 'state')
    def _compute_is_overdue(self):
        today = fields.Date.context_today(self)
        for rec in self:
            rec.is_overdue = bool(
                rec.state == 'active' and rec.due_date and rec.due_date < today
            )

    # ---------- onchange: warning only ----------
    @api.onchange('copy_id')
    def _onchange_copy_id(self):
        if not self.copy_id:
            return
        domain = [('copy_id', '=', self.copy_id.id), ('state', '=', 'active')]
        if self._origin.id:
            domain.append(('id', '!=', self._origin.id))
        if self.search_count(domain):
            return {'warning': {
                'title': 'Warning',
                'message': 'This copy already has an active loan.',
            }}

    # ---------- Constraints ----------
    @api.constrains('copy_id', 'state')
    def _check_single_active_loan(self):
        for rec in self:
            if rec.state == 'active':
                clash = self.search_count([
                    ('copy_id', '=', rec.copy_id.id),
                    ('state', '=', 'active'),
                    ('id', '!=', rec.id),
                ])
                if clash:
                    raise ValidationError('This copy is already on loan: two active loans are not allowed.')

    @api.constrains('loan_date', 'due_date')
    def _check_due_after_loan(self):
        for rec in self:
            if rec.due_date and rec.loan_date and rec.due_date <= rec.loan_date:
                raise ValidationError('Due date must be later than loan date.')

    @api.constrains('loan_date', 'return_date')
    def _check_return_date(self):
        for rec in self:
            if rec.return_date and rec.loan_date and rec.return_date < rec.loan_date:
                raise ValidationError('Return date cannot be earlier than loan date.')
       # ---------- Button ----------
    def action_return(self):
           for rec in self:
               rec.write({
                   'state': 'returned',
                   'return_date': rec.return_date or fields.Date.context_today(rec),
               })