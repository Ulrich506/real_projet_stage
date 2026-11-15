/** @odoo-module **/

/**
 * Auto-save for État Civil forms.
 *
 * Watches for field changes on the current form view and triggers a save
 * after a configurable debounce delay (default 2 seconds).  A small status
 * indicator is shown in the form header so the user can see whether their
 * work has been persisted to the server.
 *
 * The indicator has three states:
 *   - "En attente..."  (changes detected, waiting for debounce)
 *   - "Sauvegarde..."  (save in progress)
 *   - "Enregistré"     (last save succeeded)
 *   - "Erreur"         (last save failed — user must click Enregistrer)
 */

import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { onMounted, onWillUnmount } from "@odoo/owl";
import { patch } from "@web/core/patches";
import { FormController } from "@web/views/form/form_controller";
import { Component } from "@odoo/owl";

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------
const DEBOUNCE_MS = 2000; // 2 seconds after last change

// ---------------------------------------------------------------------------
// Auto-save status component (rendered in the form header)
// ---------------------------------------------------------------------------

export class AutoSaveStatus extends Component {
    static template = "etat_civil.AutoSaveStatus";
    static props = {};

    setup() {
        this.state = "idle"; // idle | pending | saving | saved | error
        this.timer = null;
        this.busService = useService("bus");
        this.notification = useService("notification");

        // Listen for auto-save events dispatched by the patched FormController
        this.busService.on("auto_save:changed", () => this._onChanged(), { target: this });
        this.busService.on("auto_save:reset", () => this._reset(), { target: this });
    }

    onWillUnmount() {
        if (this.timer) {
            clearTimeout(this.timer);
        }
    }

    _onChanged() {
        this.state = "pending";
        if (this.timer) {
            clearTimeout(this.timer);
        }
        this.timer = setTimeout(() => this._doSave(), DEBOUNCE_MS);
    }

    async _doSave() {
        this.state = "saving";
        if (this.timer) {
            clearTimeout(this.timer);
            this.timer = null;
        }
        // Trigger the form controller to save via bus event
        this.busService.trigger("auto_save:execute_save", {
            onSuccess: () => {
                this.state = "saved";
                // Fade out after 3 seconds
                setTimeout(() => {
                    if (this.state === "saved") this.state = "idle";
                }, 3000);
            },
            onError: (error) => {
                this.state = "error";
                this.notification.add(_t("Auto-save failed. Please click Save manually."), {
                    type: "danger",
                    sticky: true,
                });
                console.error("[etat_civil] Auto-save error:", error);
            },
        });
    }

    _reset() {
        if (this.timer) {
            clearTimeout(this.timer);
            this.timer = null;
        }
        this.state = "idle";
    }
}

// ---------------------------------------------------------------------------
// Patch FormController to detect changes and trigger auto-save
// ---------------------------------------------------------------------------
patch(FormController.prototype, "etat_civil.auto_save", {
    setup() {
        super.setup();
        this.busService = useService("bus");
        this._autoSaveChanged = this._autoSaveChanged.bind(this);

        onMounted(() => {
            // Subscribe to field change events
            document.addEventListener("auto_save_field_changed", this._autoSaveChanged);
            // Listen for execute_save requests from AutoSaveStatus
            this.busService.on(
                "auto_save:execute_save",
                (payload) => this._handleAutoSave(payload),
                { target: this }
            );
        });

        onWillUnmount(() => {
            document.removeEventListener("auto_save_field_changed", this._autoSaveChanged);
        });
    },

    _autoSaveChanged() {
        // Notify the AutoSaveStatus component
        this.busService.trigger("auto_save:changed");
    },

    async _handleAutoSave(payload) {
        try {
            await this.save();
            if (payload.onSuccess) payload.onSuccess();
        } catch (error) {
            if (payload.onError) payload.onError(error);
        }
    },

    /**
     * Override save to also notify the auto-save status component.
     */
    async save() {
        const result = await super.save();
        // After a manual save, reset the auto-save state
        this.busService.trigger("auto_save:reset");
        return result;
    },
});

// ---------------------------------------------------------------------------
// Global mutation observer to detect any input changes in the form
// ---------------------------------------------------------------------------
patch(FormController.prototype, "etat_civil.auto_save.input_listener", {
    onMounted() {
        super.onMounted?.call?.(this);
        // Add a global mutation observer to detect any input changes
        if (typeof window !== "undefined") {
            if (!window.__etat_civil_auto_save_observer) {
                const observer = new MutationObserver((mutations) => {
                    for (const mutation of mutations) {
                        if (mutation.type === "attributes") {
                            const el = mutation.target;
                            if (
                                el.tagName === "INPUT" ||
                                el.tagName === "TEXTAREA" ||
                                el.tagName === "SELECT" ||
                                el.classList.contains("o_input")
                            ) {
                                document.dispatchEvent(
                                    new CustomEvent("auto_save_field_changed")
                                );
                                break;
                            }
                        }
                    }
                });
                observer.observe(document.body, {
                    attributes: true,
                    subtree: true,
                    attributeFilter: ["value", "checked", "selected"],
                });
                window.__etat_civil_auto_save_observer = observer;
            }
        }
    },
});
