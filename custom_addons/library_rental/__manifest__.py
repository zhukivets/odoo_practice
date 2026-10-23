{
    'name': 'Library Rental',
    'version': '1.0',
    'category': 'Services',
    'summary': 'Library Rental Management Module',
    'author': 'Oleksandra Zhukivets',
    'depends': ['base', 'web'],
    'data': [
        'security/library_security.xml',
        'security/ir.access.csv',
        'views/library_views.xml',
    ],
    'demo': [
        'demo/library_demo.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}