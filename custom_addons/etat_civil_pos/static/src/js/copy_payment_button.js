/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { SelectionPopup } from "@point_of_sale/app/utils/input_popups/selection_popup";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { roundPrecision } from "@web/core/utils/numbers";

export class CopyPaymentButton extends Component {
    static template = "etat_civil_pos.CopyPaymentButton";

    setup() {
        this.pos = usePos();
        this.orm = useService("orm");
        this.popup = useService("popup");
    }

    async click() {
        const order = this.pos.get_order();
        if (order.orderlines.length || order.paymentlines.length) {
            await this.popup.add(ErrorPopup, {
                title: _t("Commande non vide"),
                body: _t("Créez une nouvelle commande POS avant d'encaisser une demande de copie."),
            });
            return;
        }

        try {
            const requests = await this.orm.call(
                "etat.civil.copy.request",
                "pos_get_pending_copy_requests",
                [this.pos.pos_session.id]
            );
            if (!requests.length) {
                await this.popup.add(ErrorPopup, {
                    title: _t("Aucune demande payable"),
                    body: _t("Aucune demande facturée dans la devise du point de vente n'est à encaisser."),
                });
                return;
            }
            const selection = requests.map((request) => ({
                id: request.id,
                label: `${request.name} — ${request.partner_name} — ${request.subject} — ${request.amount_due} ${request.currency_name}`,
                item: request,
            }));
            const { confirmed, payload: request } = await this.popup.add(SelectionPopup, {
                title: _t("Choisir une demande de copie"),
                list: selection,
            });
            if (!confirmed || !request) {
                return;
            }

            const { confirmed: amountConfirmed, payload } = await this.popup.add(NumberPopup, {
                title: _t("Montant du versement"),
                subtitle: _t("Solde dû : %s %s", request.amount_due, request.currency_name),
                startingValue: request.amount_due,
                nbrDecimal: this.pos.currency.decimal_places,
                isInputSelected: true,
            });
            if (!amountConfirmed) {
                return;
            }
            const amount = Number(String(payload).replace(",", "."));
            if (
                !Number.isFinite(amount) ||
                amount <= 0 ||
                amount > request.amount_due ||
                Math.abs(
                    amount - roundPrecision(amount, this.pos.currency.rounding)
                ) > this.pos.currency.rounding * 1e-6
            ) {
                await this.popup.add(ErrorPopup, {
                    title: _t("Montant invalide"),
                    body: _t("Saisissez un montant positif qui ne dépasse pas le solde et respecte l'arrondi de la devise."),
                });
                return;
            }

            const partners = await this.orm.call(
                "pos.session",
                "get_pos_ui_res_partner_by_params",
                [[this.pos.pos_session.id], { domain: [["id", "=", request.partner_id]] }]
            );
            this.pos.addPartners(partners);
            const partner = this.pos.db.get_partner_by_id(request.partner_id);
            const paymentProduct = this.pos.db.get_product_by_id(request.payment_product_id);
            if (!partner || !paymentProduct) {
                throw new Error(_t("Le demandeur ou le produit d'encaissement n'est pas chargé dans le POS."));
            }

            order.set_partner(partner);
            order.etatCivilCopyRequestId = request.id;
            order.to_invoice = true;
            await order.add_product(paymentProduct, {
                price: amount,
                quantity: 1,
                merge: false,
            });
        } catch (error) {
            await this.popup.add(ErrorPopup, {
                title: _t("Encaissement impossible"),
                body: error.message || _t("Le serveur n'a pas pu préparer cet encaissement."),
            });
        }
    }
}

ProductScreen.addControlButton({
    component: CopyPaymentButton,
    condition: function () {
        return Boolean(this.pos.pos_session);
    },
});
