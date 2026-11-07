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

## Лабораторна 4: групи, права доступу, record rule

### Групи
- Створені `res.groups` **«Бібліотекар»** і **«Читач»** в одній категорії **Library** (через `res.groups.privilege`, у цій збірці Odoo 19.5 група прив'язується до категорії саме так).
- `library.member.user_id` (Many2one на `res.users`) зв'язує читача бібліотеки з користувачем Odoo. Через це поле працює record rule.

### Права доступу (`security/ir.access.csv`)
У цій збірці Odoo 19.5 замість `ir.model.access.csv` і `ir.rule` використовується одна модель `ir.access` (колонки `operation`, `domain`).

| Модель | Бібліотекар | Читач |
|---|---|---|
| library.book | crud | r |
| library.copy | crud | r |
| library.loan | crud | r (лише власні, див. нижче) |
| library.member | crud | немає доступу |

Рядки не скопійовані з Бібліотекаря: у Читача свої права, а для `library.member` рядка немає зовсім.

### Логіка record rule
- Модель `ir.rule` у цій версії відсутня (`KeyError: 'ir.rule'`), тому правило задане доменом у рядку `ir.access.csv` для `library.loan` і групи Читач.
- Домен: `[('member_id.user_id', '=', user.id)]`. Читач бачить лише видачі, де читач прив'язаний до нього.
- Група в рядку вказана (`group_id/id`), тому правило не глобальне. Бібліотекар має рядок без домену й бачить усі видачі.

### Меню
- `Library`, `Books`, `Copies`, `Loans` доступні групам Читач і Бібліотекар.
- `Members` доступне лише Бібліотекарю (атрибут `groups` на `menuitem`).

### Тестування під Читачем
Створено користувача `Reader` з роллю User і групою Читач, читача бібліотеки прив'язано до нього через `user_id`. Під цим користувачем: у меню немає `Members`, у `Loans` видно лише його видачу, кнопки «Новий» немає.
Скриншот: `screenshots/reader_test.png`.

## Лабораторна 5: wizard «Оформити повернення» та QWeb-звіт

### Wizard `library.return.wizard`
- `models.TransientModel`, поля: `loan_id` (Many2one на `library.loan`, обов'язкове), `condition_on_return` (Selection з тими самими значеннями, що й `library.copy.condition`: new/good/damaged), `notes` (Text).
- `default_get`: бере `default_loan_id` з контексту, а якщо його немає, то `active_id`, але лише коли `active_model == 'library.loan'`. Також підставляє поточний стан примірника як значення за замовчуванням.
- `action_confirm()`: `self.ensure_one()`, далі робота лише з `self.loan_id`. Після підтвердження:
  - видача: `state = 'returned'`, `return_date = сьогодні`, примітки зберігаються в нове поле `return_notes`;
  - примірник: `condition = condition_on_return`;
  - `fine_amount` перераховується автоматично, бо це `compute`/`store` поле з `@api.depends('due_date', 'return_date', 'state')`. Ручний запис у нього не потрібен: його затер би наступний перерахунок.
  - Повторне повернення вже повернутої видачі блокується `UserError`.

### Views
- `wizard/library_return_wizard_views.xml`: форма wizard з кнопками «Підтвердити» / «Скасувати» і дія-вікно `ir.actions.act_window` з `target="new"`.
- На формі Loan кнопку **Return** замінено кнопкою **«Оформити повернення»** (`type="action"`, `context="{'default_loan_id': id}"`). Кнопка прихована для повернених видач.
- Файл wizard підключено в `__manifest__.py` **перед** `views/library_views.xml`, бо кнопка на формі Loan посилається на `%(action_library_return_wizard)d`.
- Права на wizard (`crud`) має лише група Бібліотекар (`ir.access.csv`).

### QWeb-звіт «Історія видач читача»
- `ir.actions.report` з `model = library.member`, `report_type = qweb-pdf`, кнопка друку прив'язана до форми/списку читачів (`binding_model_id`).
- Шаблон: `web.html_container` → `t-foreach="docs" t-as="member"` → `web.external_layout`. Усередині вкладений цикл `member.loan_ids`: книга, інвентарний номер, дати, статус, штраф і підсумкова сума штрафів.

### AI-рев'ю: що перевірено вручну
1. **`ensure_one()` / multi-record.** AI-чернетка `action_confirm()` мала стиль `for rec in self`, як в `action_return`. Для wizard це неправильно: кнопка wizard завжди викликається на одному записі, тому стоїть `self.ensure_one()` і робота йде з `self.loan_id`, без циклу. Якщо метод викликати на кількох записах, буде помилка, а не мовчазна обробка лише першого.
2. **`default_get`.** Перевірено, що `active_id` береться лише за `active_model == 'library.loan'`, тож wizard не підставить id запису з іншої моделі.
3. **`fine_amount`.** AI пропонував записувати штраф прямо у `write()`. Прибрано, бо поле обчислюване: правильно змінити `state` і `return_date`, а штраф перерахує `_compute_fine_amount`.
4. **Поля примірника.** AI-чернетка писала у неіснуюче поле `library.copy.state`. У моделі є лише `condition`, а «вільність» примірника визначається відсутністю активної видачі. Тому оновлюється тільки `condition`.
5. **Відповідність моделі звіту.** `ir.actions.report.model = library.member`, тому `docs` — це записи `library.member`, і саме їх ітерує `t-foreach="docs" t-as="member"`. Видачі ітеруються вкладеним `member.loan_ids`, а не через `docs`. Модель дії й те, що реально ітерується, збігаються.
6. **`report_name`** має префікс технічної назви модуля: `library_rental.report_member_loan_history`.
7. **`report_file` у звіті.** AI-код містив поле `report_file` в `ir.actions.report`. У збірці Odoo 19.5 його немає, і модуль не оновлювався (`ValueError: Invalid field 'report_file'`). Поле видалено.
8. **`t-esc` у QWeb.** AI-код виводив підсумки через `t-esc`, і в PDF вони були порожні. В Odoo 19 замінено на `t-out`.

### Скриншоти
- `return_wizard.png`: заповнений wizard «Оформити повернення» (додано до здачі окремо).
- `member_loan_history.pdf`: згенерований PDF-звіт «Історія видач читача» (додано до здачі окремо).
