{
    "name": "État civil — Passerelle comptable",
    "version": "17.0.1.0.0",
    "category": "Services/Accounting",
    "summary": "Relie les demandes de copies à Odoo Accounting",
    "depends": ["etat_civil", "account"],
    "data": [
        "data/sequences.xml",
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/copy_request_views.xml",
        "report/copy_document.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}

