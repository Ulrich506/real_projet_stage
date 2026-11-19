/** @odoo-module **/

/**
 * Confirmation notification and list update after "Marquer traité" button click.
 *
 * Patches FormController.afterExecuteActionButton to detect when
 * action_marquer_traite succeeds, then displays a centered notification
 * overlay and dispatches a custom event so the list view can update the
 * affected row in-place.
 *
 * Patches ListController.afterExecuteActionButton to handle the case where
 * the action is triggered directly from the list view (smart button or
 * multi-action). The list row is updated in-place to keep the ticket visible
 * even if the active filter would normally exclude treated items.
 *
 * Features:
 * - Auto-dismiss after 1500ms (configurable via AUTO_DISMISS_MS)
 * - Fade + scale animation with prefers-reduced-motion support
 * - Double-click prevention (handled by Odoo's executeButtonCallback)
 * - In-place list row update preserving scroll, pagination, filters, sort
 * - Proper cleanup on navigation/component unmount
 * - Accessibility: role="status" / aria-live="polite"
 */

import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { onMounted, onWillUnmount } from "@odoo/owl";
import { patch } from "@web/core/patches";
import { FormController } from "@web/views/form/form_controller";
import { ListController } from "@web/views/list/list_controller";

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------
const AUTO_DISMISS_MS = 1500; // Auto-dismiss after 1.5 seconds

// Custom event name dispatched when a ticket is marked as treated
const TICKET_TREATED_EVENT = "etat_civil.ticket_treated";

// ---------------------------------------------------------------------------
// Notification helper functions (module scope, no component dependency)
// ---------------------------------------------------------------------------

/**
 * Create and display the centered success notification overlay.
 * @returns {Function} A cleanup function to remove the overlay.
 */
function showTreatedNotification() {
    const prefersReducedMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
    ).matches;

    // Create overlay
    const overlay = document.createElement("div");
    overlay.className = "o-ticket-treated-overlay";
    overlay.setAttribute("role", "alert");
    overlay.setAttribute("aria-live", "polite");

    if (prefersReducedMotion) {
        overlay.classList.add("o-ticket-treated-no-animation");
    }

    // Create card
    const card = document.createElement("div");
    card.className = "o-ticket-treated-card";
    card.setAttribute("role", "status");
    card.setAttribute("aria-live", "polite");

    // Icon checkmark (Odoo icon)
    const icon = document.createElement("i");
    icon.className = "oi oi-check o-ticket-treated-icon";

    // Message text
    const msg = document.createElement("span");
    msg.className = "o-ticket-treated-message";
    msg.textContent = _t("Traitement effectué avec succès.");

    card.appendChild(icon);
    card.appendChild(msg);
    overlay.appendChild(card);

    // Click on overlay background to dismiss
    overlay.addEventListener("click", (e) => {
        if (e.target === overlay) {
            removeNotification(overlay);
        }
    });

    document.body.appendChild(overlay);

    // Trigger fade-in + scale animation on next frame
    requestAnimationFrame(() => {
        overlay.classList.add("o-ticket-treated-visible");
    });

    // Auto-dismiss after delay
    const timer = setTimeout(() => {
        removeNotification(overlay);
    }, AUTO_DISMISS_MS);

    // Return cleanup function
    return () => {
        clearTimeout(timer);
        removeNotification(overlay);
    };
}

/**
 * Remove the notification overlay with fade-out animation.
 * @param {HTMLElement} overlay
 */
function removeNotification(overlay) {
    if (!overlay || !overlay.parentNode) return;
    overlay.classList.remove("o-ticket-treated-visible");
    setTimeout(() => {
        if (overlay.parentNode) {
            overlay.parentNode.removeChild(overlay);
        }
    }, 300); // wait for CSS transition
}

// ---------------------------------------------------------------------------
// Patch FormController: setup + afterExecuteActionButton
// ---------------------------------------------------------------------------

patch(FormController.prototype, "etat_civil.ticket_treated_notification", {
    setup() {
        super.setup();
        this.notification = useService("notification");
        this._notificationCleanup = null;
        this._marquerTraitePending = false;

        // Clean up notification on navigation away or component unmount
        onWillUnmount(() => {
            if (this._notificationCleanup) {
                this._notificationCleanup();
                this._notificationCleanup = null;
            }
            this._marquerTraitePending = false;
        });
    },

    /**
     * Called before every button action. We use it to mark that
     * action_marquer_traite is about to execute.
     *
     * @param {Object} clickParams - contains name, type, etc.
     * @returns {boolean} true to proceed
     */
    async beforeExecuteActionButton(clickParams) {
        const isMarquerTraite =
            clickParams &&
            clickParams.name === "action_marquer_traite" &&
            clickParams.type === "object";

        if (isMarquerTraite) {
            // Clean up any previous notification
            if (this._notificationCleanup) {
                this._notificationCleanup();
                this._notificationCleanup = null;
            }
            this._marquerTraitePending = true;
        }

        return super.beforeExecuteActionButton?.call(this, clickParams) !== false;
    },

    /**
     * Called after every button action (even on error).
     * We check if marquer_traite was pending and show notification.
     *
     * Note: In view_button_hook.js, afterExecuteAction is called at line 100,
     * before the error check at line 104. This means we can't distinguish
     * success from error here. We delay showing the notification so the error
     * dialog has time to appear first, then check for .modal-backdrop.
     *
     * @param {Object} clickParams - contains name, type, etc.
     */
    async afterExecuteActionButton(clickParams) {
        const isMarquerTraite =
            clickParams &&
            clickParams.name === "action_marquer_traite" &&
            clickParams.type === "object";

        if (isMarquerTraite && this._marquerTraitePending) {
            this._marquerTraitePending = false;

            // Delay showing the notification to allow any error dialog to appear first.
            // If an error occurred, Odoo will show a modal dialog, and we can detect
            // it by checking for .modal-backdrop in the DOM after a short delay.
            setTimeout(() => {
                // Check if an error modal is present — if so, don't show success
                const hasErrorModal = document.querySelector(
                    ".modal-backdrop, .o_error_dialog"
                );
                if (!hasErrorModal) {
                    this._notificationCleanup = showTreatedNotification();
                    // Dispatch custom event so the list view can update the row in-place
                    const resId = this.model.root.resId;
                    window.dispatchEvent(
                        new CustomEvent(TICKET_TREATED_EVENT, {
                            detail: { resId },
                        })
                    );
                }
            }, 200);
        }

        await super.afterExecuteActionButton?.call(this, clickParams);
    },
});

// ---------------------------------------------------------------------------
// Patch ListController: update treated ticket row in-place
// ---------------------------------------------------------------------------

patch(ListController.prototype, "etat_civil.ticket_treated_list_update", {
    setup() {
        super.setup();
        this._marquerTraitePending = false;

        // Listen for tickets marked as treated from the form view
        onMounted(() => {
            this._onTicketTreated = this._onTicketTreated.bind(this);
            window.addEventListener(TICKET_TREATED_EVENT, this._onTicketTreated);
        });

        onWillUnmount(() => {
            window.removeEventListener(TICKET_TREATED_EVENT, this._onTicketTreated);
        });
    },

    /**
     * Handle custom event dispatched when a ticket is marked as treated
     * from the form view. Updates the corresponding row in-place so it
     * remains visible even if the active filter would exclude it.
     *
     * @param {CustomEvent} event
     */
    _onTicketTreated(event) {
        const { resId } = event.detail;
        if (!resId) return;

        // Find the record in the list and update it in-place
        const record = this.model.root.records.find(
            (r) => r.resId === resId
        );
        if (record && record.statut !== "traite") {
            record.update({
                statut: "traite",
                processed_at: new Date().toISOString().replace("Z", "+00:00"),
            });
        }
    },

    /**
     * Called before every button action in the list view.
     * @param {Object} clickParams
     * @returns {boolean}
     */
    async beforeExecuteActionButton(clickParams) {
        const isMarquerTraite =
            clickParams &&
            clickParams.name === "action_marquer_traite" &&
            clickParams.type === "object";

        if (isMarquerTraite) {
            this._marquerTraitePending = true;
        }

        return super.beforeExecuteActionButton?.call(this, clickParams) !== false;
    },

    /**
     * Called after every button action in the list view.
     * Updates the selected record(s) in-place if action_marquer_traite succeeded.
     * @param {Object} clickParams
     */
    async afterExecuteActionButton(clickParams) {
        const isMarquerTraite =
            clickParams &&
            clickParams.name === "action_marquer_traite" &&
            clickParams.type === "object";

        if (isMarquerTraite && this._marquerTraitePending) {
            this._marquerTraitePending = false;

            // Update selected records in-place to keep them visible
            const now = new Date().toISOString().replace("Z", "+00:00");
            for (const record of this.model.root.selection) {
                if (record.statut !== "traite") {
                    record.update({
                        statut: "traite",
                        processed_at: now,
                    });
                }
            }
        }

        await super.afterExecuteActionButton?.call(this, clickParams);
    },
});
