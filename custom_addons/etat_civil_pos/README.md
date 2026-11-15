# État civil — Encaissement au point de vente

This optional Odoo 17 addon depends on `etat_civil_account` and
`point_of_sale`. It records cashier payments against the existing copy-request
invoice; it must not create a second customer invoice.

## Operation

1. The Régisseur or État Civil administrator creates and posts the request's
   invoice in `etat_civil_account`.
2. The POS cashier opens a session in the same company and currency as the
   invoice, then chooses **Encaisser une copie**.
3. The cashier selects a request and enters the amount received. The POS
   checkout records a real payment against the request's invoice. Partial
   payments are allowed; the request cannot be delivered until its invoice is
   fully paid.
4. The POS payment remains linked to the POS order and invoice, and a technical
   quittance is created for the reconciled amount.

The server validates the role, center, session, partner, invoice, currency,
technical payment product, taxes, discount, amount and real POS payment before
reconciliation. It also checks the POS payment source again before authorizing
delivery.

Odoo POS orders use the company's accounting currency. An invoice in a
different currency is intentionally excluded from the POS selection and must
be collected through the accounting payment wizard instead. The commune must
validate the legal status and numbering of the technical quittance before
using it as an official receipt.

## Administrative ticket intake

The POS **Nouveau ticket de demande** button records an unpaid request and
prints its ticket. It accepts birth, marriage, and death copies in integral or
excerpt format; no other services are enabled. A ticket is not a payment and
does not create an invoice. The cashier can only create tickets in an open POS
session and for an assigned center. Repeating the same POS request after a
network interruption returns the existing ticket.

An agent opens the ticket and uses **Créer la demande de copie**, selects the
identified act, and saves the financial request. The configured tariff must
use the product mapped to the ticket. The existing first birth-copy
entitlement remains in effect. After the invoice is posted, the cashier uses
**Encaisser une copie**; the receipt records the ticket, cashier, center, and
payment time. The act PDF remains available only through the existing
authorized delivery workflow.

The six standard service products are administrative product references, not
direct POS sale lines. They are hidden from the normal product catalog and
cannot be charged as an ordinary order. Configure one active tariff per
document type, copy format, center, company, and effective period. Tariffs
carry the payable amount (MGA by default); the products themselves have no
POS sale price.

Use Odoo's native **Daily Sales Report** from the POS session for daily totals
and cash-control figures. Session opening, cash counts, differences, and
closing remain under the native POS workflow; this addon does not reset or
close a session automatically. If `pos_restaurant` is installed, disable its
restaurant option in each administrative POS configuration after checking
that there are no active table orders. Existing POS configurations are not
changed automatically.
