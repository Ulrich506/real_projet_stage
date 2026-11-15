/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { SelectionPopup } from "@point_of_sale/app/utils/input_popups/selection_popup";
import { TextInputPopup } from "@point_of_sale/app/utils/input_popups/text_input_popup";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { usePos } from "@point_of_sale/app/store/pos_hook";

const DOCUMENT_TYPES = [
    { id: "naissance", label: _t("Acte de naissance") },
    { id: "mariage", label: _t("Acte de mariage") },
    { id: "deces", label: _t("Acte de décès") },
];
const COPY_KINDS = [
    { id: "copie_integrale", label: _t("Copie intégrale") },
    { id: "extrait", label: _t("Extrait") },
];

export class GuichetTicketButton extends Component {
    static template = "etat_civil_pos.GuichetTicketButton";

    setup() {
        this.pos = usePos();
        this.orm = useService("orm");
        this.popup = useService("popup");
        this.action = useService("action");
        this.pendingTicketPayload = null;
    }

    async _text(title, startingValue = "") {
        return this.popup.add(TextInputPopup, {
            title,
            startingValue,
            placeholder: title,
        });
    }

    async _select(title, values) {
        const { confirmed, payload } = await this.popup.add(SelectionPopup, {
            title,
            list: values.map((value) => ({
                id: value.id,
                label: value.label,
                item: value,
            })),
        });
        return confirmed ? payload : null;
    }

    async _prepareTicket() {
        const centers = await this.orm.call(
            "etat.civil.demande.guichet",
            "pos_get_available_centers",
            [this.pos.pos_session.id]
        );
        const center = centers.length === 1
            ? centers[0]
            : await this._select(_t("Choisir le centre"), centers);
        if (!center) {
            return null;
        }

        const { confirmed: requesterConfirmed, payload: requesterName } =
            await this._text(_t("Nom du demandeur"));
        if (!requesterConfirmed) {
            return null;
        }
        const phoneResult = await this._text(_t("Téléphone (facultatif)"));
        const phone = phoneResult.confirmed ? phoneResult.payload : "";

        const { confirmed: personConfirmed, payload: personName } =
            await this._text(_t("Nom de la personne concernée"));
        if (!personConfirmed) {
            return null;
        }

        const documentType = await this._select(
            _t("Type de document"),
            DOCUMENT_TYPES
        );
        if (!documentType) {
            return null;
        }
        const copyKind = await this._select(_t("Format de copie"), COPY_KINDS);
        if (!copyKind) {
            return null;
        }
        const { confirmed: quantityConfirmed, payload: quantityValue } =
            await this.popup.add(NumberPopup, {
                title: _t("Nombre de copies"),
                startingValue: 1,
                isInputSelected: true,
                confirmText: _t("Continuer"),
            });
        if (!quantityConfirmed) {
            return null;
        }
        const quantity = Number(String(quantityValue).replace(",", "."));
        if (!Number.isSafeInteger(quantity) || quantity <= 0) {
            throw new Error(_t("Le nombre de copies doit être un entier positif."));
        }

        const referenceResult = await this._text(
            _t("Numéro ou référence de l'acte (facultatif)")
        );
        const cryptoApi = globalThis.crypto;
        const requestUuid = cryptoApi?.randomUUID
            ? cryptoApi.randomUUID()
            : `pos-${Date.now()}-${Math.random().toString(36).slice(2)}`;

        return {
            center_id: center.id,
            requester_name: requesterName.trim(),
            phone: phone.trim(),
            person_name: personName.trim(),
            document_type: documentType.id,
            copy_kind: copyKind.id,
            copy_quantity: quantity,
            act_reference: referenceResult.confirmed
                ? referenceResult.payload.trim()
                : "",
            request_uuid: requestUuid,
        };
    }

    async click() {
        const order = this.pos.get_order();
        if (order.orderlines.length || order.paymentlines.length) {
            await this.popup.add(ErrorPopup, {
                title: _t("Commande non vide"),
                body: _t("Terminez ou annulez la commande avant de créer un ticket."),
            });
            return;
        }

        let result;
        try {
            if (!this.pendingTicketPayload) {
                this.pendingTicketPayload = await this._prepareTicket();
            }
            if (!this.pendingTicketPayload) {
                return;
            }

            result = await this.orm.call(
                "etat.civil.demande.guichet",
                "pos_create_ticket",
                [this.pos.pos_session.id, this.pendingTicketPayload]
            );
            this.pendingTicketPayload = null;
        } catch (error) {
            await this.popup.add(ErrorPopup, {
                title: _t("Création du ticket impossible"),
                body: error.message || _t("Le serveur n'a pas pu enregistrer le ticket."),
            });
            return;
        }

        try {
            await this.action.doAction("etat_civil_pos.action_report_guichet_ticket", {
                additionalContext: { active_ids: [result.id] },
            });
        } catch (error) {
            await this.popup.add(ErrorPopup, {
                title: _t("Ticket créé, impression impossible"),
                body: _t(
                    "Le ticket %s a été enregistré. Vous pouvez le réimprimer depuis la file d'attente. Détail : %s",
                    result.ticket_number,
                    error.message || _t("erreur d'impression")
                ),
            });
        }
    }
}

ProductScreen.addControlButton({
    component: GuichetTicketButton,
    condition: function () {
        return Boolean(this.pos.pos_session);
    },
});
