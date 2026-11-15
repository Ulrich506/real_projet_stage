# État civil — Facturation

This Odoo 17 integration keeps copy tariffs and accounting links outside the
core `etat_civil` module. It depends on `etat_civil` and `account`.

## Configuration

1. Install `etat_civil_account` on the test database.
2. Create service products in Odoo and configure their income accounts and
   customer taxes according to the commune's chart of accounts.
3. As an État Civil administrator, create a tariff for each document type and
   copy kind. Tariffs are scoped by company, optionally by center, and by
   effective dates. The initial price defaults to **2,000 MGA**.
4. Birth tariffs default to the first-copy-free rule; marriage and death
   tariffs do not. This rule is enforced by the server.
5. If the company's accounting currency is not MGA, configure a valid MGA
   exchange rate for the invoice date. The accounting invoice remains in MGA;
   Odoo converts it to the company's ledger currency.
6. Assign a center to each Régisseur. The role can create/read only invoices
   linked to copy requests in assigned centers; it does not imply the general
   Odoo accounting-invoice group.
7. Régisseurs can create and process copy requests, record payments, reprint
   receipts, and deliver eligible copies only in their assigned centers.
   Officers have no copy-request, payment, or receipt access. Copy import and
   export remain restricted to État Civil administrators in the core module.

## Copy and invoice flow

A copy request must identify exactly one validated act and the requesting
contact. On submission, the server snapshots the active tariff, taxes, price,
copy quantity, and first-copy entitlement. For a first birth-copy request, one
copy is free; any additional copies are billed. Further requests for that act
are payable. The entitlement is released if the request is cancelled before
delivery. Draft customer invoices are created through Odoo Accounting and
linked to their copy request; duplicate invoice creation is guarded.

## Point-of-sale payments

The optional `etat_civil_pos` addon links a POS order to the existing copy
invoice and reconciles each actual POS payment against that invoice. It does
not create a second invoice. The POS user must be a Régisseur or État Civil
administrator with access to the request's center. POS sessions can collect
full or partial payments; the request remains undeliverable until the invoice
is fully paid. Each reconciled POS payment receives a technical quittance that
can be reprinted.

Odoo POS orders use the company's accounting currency. Therefore the POS
currency must match the copy invoice currency; foreign-currency invoices are
not offered by the POS bridge. Before production use, the commune must validate
its accounting accounts, taxes, exchange rates, tariff values, quittance
legal status and numbering, and operational procedures.
