// Flomfy nodes: show sizes on the node after it runs.
const { app } = window.comfyAPI.app;

function setLabel(node, name, text) {
    const slot = node.outputs?.find((o) => o.name === name);
    if (slot) slot.label = text;
}

app.registerExtension({
    name: "Flomfy.Nodes",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "FlomfyLetterbox" && nodeData.name !== "FlomfyRemoveLetterbox") return;
        const remove = nodeData.name === "FlomfyRemoveLetterbox";
        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            const r = onExecuted?.apply(this, arguments);
            const s = message?.flomfy_size;
            if (s && s.length >= 6) {
                const [w, h, ow, oh, left, top] = s.map(Number);
                setLabel(this, "image", `image ${w}×${h} → ${ow}×${oh}`);
                if (remove) {
                    setLabel(this, "width", `width ${ow}`);
                    setLabel(this, "height", `height ${oh}`);
                    this.setDirtyCanvas?.(true, true);
                    return r;
                }
                setLabel(this, "original_width", `original_width ${w}`);
                setLabel(this, "original_height", `original_height ${h}`);
                setLabel(this, "width", `width ${ow}`);
                setLabel(this, "height", `height ${oh}`);
                setLabel(this, "pad_left", `pad_left ${left}`);
                setLabel(this, "pad_top", `pad_top ${top}`);
                this.setDirtyCanvas?.(true, true);
            }
            return r;
        };
    },
});
