import logging
from datetime import timedelta
from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

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
    return_notes = fields.Text(string='Return Notes')
    state = fields.Selection([
        ('active', 'Active'),
        ('returned', 'Returned')
    ], string='Status', default='active', required=True)
    fine_amount = fields.Float(string='Fine', compute='_compute_fine_amount', store=True)
    is_overdue = fields.Boolean(string='Overdue', compute='_compute_is_overdue')
    # Заповнюються щоденним cron-завданням
    overdue_days = fields.Integer(string='Overdue Days', readonly=True)
    last_overdue_check = fields.Date(string='Last Overdue Check', readonly=True)

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

    # ---------- Cron ----------
    @api.model
    def _cron_check_overdue_loans(self):
        """Щоденна перевірка прострочених видач (викликається з ir.cron).

        Лише ORM (search/write), без сирого SQL. Кожен запис обробляється
        в окремому try/except із savepoint: помилка на одному записі
        відкочує лише його зміни і не зупиняє обробку решти пакета.
        """
        today = fields.Date.context_today(self)
        loans = self.search([
            ('state', '=', 'active'),
            ('due_date', '<', today),
        ])
        _logger.info('Library cron: found %s overdue loan(s)', len(loans))

        processed = failed = 0
        for loan in loans:
            try:
                with self.env.cr.savepoint():
                    loan._process_overdue_loan(today)
                processed += 1
            except Exception:
                failed += 1
                _logger.exception('Library cron: failed to process loan id=%s', loan.id)

        _logger.info('Library cron: done, processed=%s, failed=%s', processed, failed)
        return True

    def _process_overdue_loan(self, today):
        self.ensure_one()
        days = (today - self.due_date).days
        self.write({
            'overdue_days': days,
            'last_overdue_check': today,
        })
        _logger.info(
            'Library cron: loan id=%s, copy %s, member %s: overdue %s day(s), expected fine %.2f',
            self.id, self.copy_id.inventory_number, self.member_id.name,
            days, days * FINE_PER_DAY,
        )
