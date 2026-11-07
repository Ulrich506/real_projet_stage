/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { useFileViewer } from "@web/core/file_viewer/file_viewer_hook";
import { FileModel } from "@web/core/file_viewer/file_model";
import { registry } from "@web/core/registry";
import { Many2ManyBinaryField } from "@web/views/fields/many2many_binary/many2many_binary_field";

const PREVIEWABLE_MIMETYPES = new Set([
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
]);

export class PieceAttachmentPreviewField extends Many2ManyBinaryField {
    static template = "etat_civil.PieceAttachmentPreviewField";

    setup() {
        super.setup();
        this.fileViewer = useFileViewer();
    }

    getViewerFile(file) {
        const viewerFile = new FileModel();
        Object.assign(viewerFile, {
            id: file.id,
            name: file.name,
            mimetype: file.mimetype,
            type: "binary",
        });
        return viewerFile;
    }

    canPreview(file) {
        return PREVIEWABLE_MIMETYPES.has(file.mimetype) && this.getViewerFile(file).isViewable;
    }

    openPreview(file) {
        const viewerFiles = this.files
            .map((attachment) => this.getViewerFile(attachment))
            .filter(
                (attachment) =>
                    PREVIEWABLE_MIMETYPES.has(attachment.mimetype) &&
                    attachment.isViewable
            );
        const selected = viewerFiles.find((attachment) => attachment.id === file.id);
        if (selected) {
            this.fileViewer.open(selected, viewerFiles);
        }
    }
}

registry.category("fields").add("etat_civil_piece_attachments", {
    component: PieceAttachmentPreviewField,
    supportedOptions: [
        {
            label: _t("Accepted file extensions"),
            name: "accepted_file_extensions",
            type: "string",
        },
        {
            label: _t("Number of files"),
            name: "number_of_files",
            type: "integer",
        },
    ],
    supportedTypes: ["many2many"],
    isEmpty: () => false,
    relatedFields: [
        { name: "name", type: "char" },
        { name: "mimetype", type: "char" },
        { name: "create_date", type: "datetime" },
        { name: "create_uid", type: "many2one", relation: "res.users" },
    ],
    extractProps: ({ attrs, options }) => ({
        acceptedFileExtensions: options.accepted_file_extensions,
        className: attrs.class,
        numberOfFiles: options.number_of_files,
    }),
});
