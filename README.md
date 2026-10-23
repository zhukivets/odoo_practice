# Модуль Library Rental для Odoo 19

## Що згенерував AI
- Базову конфігурацію .gitignore для Odoo та Python.
- Початкову структуру модуля: custom_addons/library_rental/ з файлами __init__.py та __manifest__.py.
- Шаблон маніфесту модуля з мінімальною конфігурацією (depends: ['base'], installable: True, pplication: True).
- Покрокові команди Git для фіксації історії розробки.

## Що виправлено вручну
- Вручну налаштовано шлях ddons_path у файлі odoo.conf для завантаження модуля сервером.
- Виправлено налаштування системного середовища для виявлення Git після встановлення.
- Перевірено та обмежено список залежностей у маніфесті до обов'язкового ase.
- Виконано активацію режиму розробника, оновлення списку додатків та успішне встановлення модуля через вебінтерфейс Odoo.

## Дизайн моделей і зв'язків

- **Book → Copy** (`One2many` / `Many2one`): одна книга має багато фізичних примірників. У `library.copy` поле `book_id` має `ondelete='restrict'`: книгу з примірниками видалити не можна, щоб не втратити облік фізичного фонду.
- **Copy → Loan** (`One2many` / `Many2one`): примірник може мати багато видач (історія). `copy_id` у `library.loan` має `ondelete='restrict'`: примірник з історією видач видалити не можна.
- **Member → Loan** (`One2many` / `Many2one`): читач може мати багато видач. `member_id` має `ondelete='restrict'`, щоб не втратити історію видач.
- **Member** реалізований за варіантом (б): `library.member` з `_inherits = {'res.partner': 'partner_id'}`. Читач автоматично отримує name, email, phone та інші поля партнера без дублювання. `partner_id` має `ondelete='cascade'`: це «розширення» партнера, і без партнера запис читача не має сенсу. Поле `membership_number` обов'язкове.

## Чому restrict, а не cascade

`cascade` мовчки видалив би записи про фізичні примірники та історію видач разом із книгою чи читачем. Для бібліотеки це втрата даних, тому скрізь, крім `partner_id`, вибрано `restrict`.

## AI-generated / вручну виправлено

### Згенеровано AI
- Структура модуля та файли моделей `book.py`, `copy.py`, `member.py`, `loan.py`.
- Поля моделей, представлення (форми та списки), меню Library і демо-дані.

### Виправлено вручну
- **Файл прав доступу.** У цій збірці Odoo 19.5 він називається `ir.access.csv` (а не `ir.model.access.csv`), має іншу структуру колонок (`model_id`, `group_id/id`, `operation`) і підключений у `__manifest__.py` першим у `data`. Без цього модуль не встановлювався (помилка `KeyError: 'ir.model.access'`).
- **Ondelete.** Перевірено вручну кожне поле Many2one: `book_id`, `copy_id`, `member_id` мають `restrict`, `partner_id` має `cascade`.
- **Обов'язкові поля.** `due_date` у `library.loan` тепер обчислюване (`compute`, `store=True`), тому при створенні видачі його вказувати не потрібно: воно рахується з `loan_date`.
- **Налаштування середовища.** `addons_path` у `odoo.conf`, режим розробника, оновлення списку додатків, встановлення модуля через веб-інтерфейс.

## ORM-запити в Odoo shell

1. Книги автора: `env['library.book'].search([('author', '=', 'George Orwell')])`
2. Вільні примірники книги «1984»: `len(book.copy_ids.filtered(lambda c: not c.loan_ids.filtered(lambda l: l.state == 'active')))`
3. Прострочені видачі: `env['library.loan'].search([('state', '=', 'active'), ('due_date', '<', fields.Date.today())])`
4. Створення видачі через `create()` і закриття через `write({'state': 'returned', 'return_date': ...})`.

## Лабораторна 3: Loan (обчислювані поля, onchange, constrains)

### Параметри
- Термін видачі: **14 днів** (`LOAN_DAYS`).
- Ставка штрафу: **5 грн за кожен день прострочення** (`FINE_PER_DAY`).

### Обчислювані поля (`library.loan`)
- `due_date`: `compute` + `store=True`, `@api.depends('loan_date')`. Дата видачі + 14 днів.
- `fine_amount`: `compute` + `store=True`. Рахується лише для повернених прострочених видач (`state == 'returned'` і `return_date > due_date`), сума = дні прострочення × 5.
- `is_overdue`: нестор-поле (без `store`). `True`, якщо видача активна і `due_date` раніше за сьогодні. Без `store`, бо залежить від поточної дати.

### onchange
- `copy_id`: якщо для примірника вже є активна видача, показується попередження (warning), збереження не блокується.

### Обмеження (`@api.constrains`)
1. Заборонено дві активні видачі на один примірник (поточний запис виключається через `id != rec.id`).
2. `due_date` має бути пізніше за `loan_date`.
3. `return_date` (якщо задана) не може бути раніше за `loan_date`.

### Правки після AI-генерації
- «Активна видача» визначається полем `state == 'active'`, а не порожнім `return_date`, бо в моделі вже є `state`.
- В onchange додано виключення `self._origin.id`, щоб запис не конфліктував сам із собою.
- У constrains явно виключений поточний запис (`id != rec.id`).
- `fine_amount` рахується лише для повернених прострочених видач.
- Синтаксис view під Odoo 19: `invisible="..."` замість `attrs`, `<list>` замість `<tree>`.
- Смужка статусу не була клікабельною, тому додана кнопка **Return** (`action_return`), яка ставить статус Returned.

### Скриншоти
- `screenshots/fine_overdue.png`: форма з `fine_amount` на простроченій видачі.
- `screenshots/due_date_recalc.png`: перерахунок `due_date` при зміні `loan_date`.