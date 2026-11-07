from odoo import api, fields, models
from odoo.exceptions import UserError


class LibraryReturnWizard(models.TransientModel):
    _name = 'library.return.wizard'
    _description = 'Оформлення повернення книги'

    loan_id = fields.Many2one(
        'library.loan',
        string='Loan',
        required=True,
        ondelete='cascade',
    )
    # Ті самі значення, що й у library.copy.condition
    condition_on_return = fields.Selection([
        ('new', 'New'),
        ('good', 'Good'),
        ('damaged', 'Damaged'),
    ], string='Condition on Return', required=True, default='good')
    notes = fields.Text(string='Notes')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        ctx = self.env.context
        # 1) явно передане з кнопки default_loan_id, 2) інакше active_id з контексту
        loan_id = ctx.get('default_loan_id')
        if not loan_id and ctx.get('active_model') == 'library.loan':
            loan_id = ctx.get('active_id')
        if loan_id:
            loan = self.env['library.loan'].browse(loan_id)
            if 'loan_id' in fields_list:
                res['loan_id'] = loan.id
            # За замовчуванням пропонуємо поточний стан примірника
            if 'condition_on_return' in fields_list and loan.copy_id.condition:
                res['condition_on_return'] = loan.copy_id.condition
        return res

    def action_confirm(self):
        # Wizard обробляє рівно один запис, а не список
        self.ensure_one()
        loan = self.loan_id
        if loan.state == 'returned':
            raise UserError('This loan has already been returned.')

        # Стан видачі і дата повернення.
        # fine_amount — compute/store поле з @api.depends('due_date', 'return_date', 'state'),
        # тому Odoo перерахує його автоматично після цього write().
        loan.write({
            'state': 'returned',
            'return_date': fields.Date.context_today(self),
            'return_notes': self.notes,
        })
        # Стан примірника
        loan.copy_id.write({'condition': self.condition_on_return})

        return {'type': 'ir.actions.act_window_close'}
