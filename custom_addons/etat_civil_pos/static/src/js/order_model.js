/** @odoo-module */

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Order.prototype, {
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.etatCivilCopyRequestId = json.etat_civil_copy_request_id || false;
    },

    export_as_JSON() {
        return {
            ...super.export_as_JSON(...arguments),
            etat_civil_copy_request_id: this.etatCivilCopyRequestId || false,
        };
    },
});
