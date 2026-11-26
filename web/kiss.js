// Flomfy node kissing, like Flame: while dragging a node, hold Alt and tap Shift.
// A pip sticks out of one of the node's inputs; touch its tip to another node's
// output and let go of the mouse to connect them. Each extra Shift tap (Alt still
// held) moves the pip to the next input. Connected inputs are included, so you can
// kiss again to replace a connection. Esc hides the pip. Ctrl+Z undoes the kiss.
//
// Classic (canvas) node rendering only; it does nothing with Nodes 2.0 (Vue nodes).
const { app } = window.comfyAPI.app;

const SETTING = "Flomfy.NodeKiss.Enabled";
const PIP_LENGTH = 70;   // graph units from the input slot to the pip tip
const HIT_RADIUS = 22;   // graph units around an output slot that count as a touch

const kiss = {
    node: null,      // node the pip belongs to
    order: [],       // input indexes, cycled by Shift
    pos: 0,          // position in order
    target: null,    // { node, slot } currently touched
};

const swallowed = new Set();  // keys whose keydown we hid from the canvas

function enabled() {
    const store = app.extensionManager?.setting;
    const v = store?.get ? store.get(SETTING) : app.ui?.settings?.getSettingValue?.(SETTING);
    return v ?? true;
}

function canvas() {
    return app.canvas;
}

function active() {
    return kiss.node !== null;
}

function inputIndex() {
    return kiss.order[kiss.pos];
}

function reset() {
    kiss.node = null;
    kiss.order = [];
    kiss.pos = 0;
    kiss.target = null;
}

function redraw() {
    canvas()?.setDirty(true, false);
}

function isNode(item) {
    return item && Array.isArray(item.inputs) && Array.isArray(item.pos) && item.size;
}

function selectedNodes() {
    const items = canvas()?.selectedItems;
    return items ? [...items].filter(isNode) : [];
}

function contains(node, x, y) {
    if (typeof node.isPointInside === "function") return node.isPointInside(x, y);
    const title = window.LiteGraph?.NODE_TITLE_HEIGHT ?? 30;
    const [nx, ny] = node.pos;
    const [w, h] = node.size;
    return x >= nx && x <= nx + w && y >= ny - title && y <= ny + h;
}

// The node under the pointer among the dragged ones; with a single node, that one.
function draggedNode() {
    const nodes = selectedNodes();
    if (nodes.length <= 1) return nodes[0] ?? null;
    const [x, y] = canvas().graph_mouse;
    return nodes.find((n) => contains(n, x, y)) ?? nodes[0];
}

// Socket inputs first, then inputs that belong to widgets.
function inputOrder(node) {
    const idx = node.inputs.map((_, i) => i);
    return [...idx.filter((i) => !node.inputs[i].widget), ...idx.filter((i) => node.inputs[i].widget)];
}

function typesMatch(outType, inType) {
    const lg = window.LiteGraph;
    if (lg?.isValidConnection) return lg.isValidConnection(outType, inType);
    return outType === inType || outType === "*" || inType === "*";
}

function slotColor(type) {
    const c = canvas();
    const LGC = window.LGraphCanvas;
    return c?.default_connection_color_byType?.[type]
        ?? LGC?.link_type_colors?.[type]
        ?? c?.default_link_color
        ?? "#9A9";
}

function inputName(slot) {
    return slot.label || slot.localized_name || slot.name;
}

function pipGeometry() {
    const slot = kiss.node.getConnectionPos(true, inputIndex());
    return { slot: [slot[0], slot[1]], tip: [slot[0] - PIP_LENGTH, slot[1]] };
}

function findTarget() {
    const c = canvas();
    const input = kiss.node.inputs[inputIndex()];
    if (!c?.graph || !input) return null;
    const { tip } = pipGeometry();
    const skip = new Set(selectedNodes());
    skip.add(kiss.node);
    let best = null;
    let bestDist = HIT_RADIUS;
    for (const node of c.graph._nodes ?? c.graph.nodes ?? []) {
        if (skip.has(node) || !node.outputs?.length) continue;
        for (let i = 0; i < node.outputs.length; i++) {
            if (!typesMatch(node.outputs[i].type, input.type)) continue;
            const p = node.getConnectionPos(false, i);
            const d = Math.hypot(p[0] - tip[0], p[1] - tip[1]);
            if (d < bestDist) {
                bestDist = d;
                best = { node, slot: i };
            }
        }
    }
    return best;
}

function start() {
    const node = draggedNode();
    if (!node || !node.inputs?.length) return;
    kiss.node = node;
    kiss.order = inputOrder(node);
    kiss.pos = 0;
    kiss.target = findTarget();
    redraw();
}

function cycle() {
    kiss.pos = (kiss.pos + 1) % kiss.order.length;
    kiss.target = findTarget();
    redraw();
}

function commit() {
    const { node, target } = kiss;
    const slot = inputIndex();
    reset();
    redraw();
    if (!node || !target || slot === undefined) return;
    const c = canvas();
    if (!node.graph || node.graph !== target.node.graph) return;
    c.emitBeforeChange?.();
    try {
        target.node.connect(target.slot, node, slot);
    } finally {
        c.emitAfterChange?.();
    }
    c.setDirty(true, true);
}

function label(ctx, text, x, y, color) {
    ctx.font = "12px Arial";
    const w = ctx.measureText(text).width;
    ctx.fillStyle = "rgba(0,0,0,0.75)";
    ctx.beginPath();
    if (ctx.roundRect) ctx.roundRect(x - w - 10, y - 9, w + 8, 18, 4);
    else ctx.rect(x - w - 10, y - 9, w + 8, 18);
    ctx.fill();
    ctx.fillStyle = color;
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    ctx.fillText(text, x - w - 6, y);
}

function drawPip(ctx) {
    if (!active() || !kiss.node.graph) return;
    const input = kiss.node.inputs[inputIndex()];
    if (!input) return;
    const { slot, tip } = pipGeometry();
    const color = slotColor(input.type);
    ctx.save();
    ctx.lineWidth = 3;
    ctx.strokeStyle = color;
    ctx.beginPath();
    ctx.moveTo(slot[0], slot[1]);
    ctx.lineTo(tip[0], tip[1]);
    ctx.stroke();
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(tip[0], tip[1], 6, 0, Math.PI * 2);
    ctx.fill();
    const count = `${kiss.pos + 1}/${kiss.order.length}`;
    label(ctx, `${inputName(input)}  ${count}`, tip[0] - 8, tip[1] - 16, color);
    if (kiss.target) {
        const out = kiss.target.node.outputs[kiss.target.slot];
        const p = kiss.target.node.getConnectionPos(false, kiss.target.slot);
        ctx.strokeStyle = "#fff";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(p[0], p[1], 10, 0, Math.PI * 2);
        ctx.stroke();
        label(ctx, `← ${inputName(out)}`, p[0] - 14, p[1] + 18, "#fff");
    }
    ctx.restore();
}

function dragging() {
    const c = canvas();
    return !!c && c.isDragging && c.pointer?.isDown !== false;
}

function onKeyDown(e) {
    if (!enabled() || !dragging()) return;
    if (e.key === "Escape" && active()) {
        reset();
        redraw();
        e.preventDefault();
        e.stopImmediatePropagation();
        return;
    }
    if (e.key !== "Shift" && e.key !== "Alt") return;
    // Plain Shift keeps its snap-to-grid job. With Alt (or a pip up) the keys are ours:
    // the canvas must not see Shift, and the browser must not open the menu bar on Alt.
    if (e.key === "Shift" && !e.altKey && !active()) return;
    swallowed.add(e.key);
    e.preventDefault();
    e.stopImmediatePropagation();
    if (e.repeat) return;
    const tapped = (e.key === "Shift" && e.altKey) || (e.key === "Alt" && e.shiftKey);
    if (!tapped) return;
    if (!active()) start();
    else if (e.key === "Shift") cycle();
}

function onKeyUp(e) {
    if (!swallowed.delete(e.key)) return;
    e.preventDefault();
    e.stopImmediatePropagation();
}

function onPointerMove() {
    if (!active()) return;
    if (!dragging()) {
        reset();
        redraw();
        return;
    }
    const t = findTarget();
    if (t?.node !== kiss.target?.node || t?.slot !== kiss.target?.slot) {
        kiss.target = t;
        redraw();
    }
}

function onPointerUp() {
    if (!active()) return;
    // Let the drag finish first, so the move and the kiss are separate undo steps.
    setTimeout(commit, 0);
}

app.registerExtension({
    name: "Flomfy.NodeKiss",
    settings: [
        {
            id: SETTING,
            category: ["Flomfy", "Node kissing", "Enabled"],
            name: "Node kissing (drag a node, hold Alt, tap Shift)",
            type: "boolean",
            defaultValue: true,
        },
    ],
    setup() {
        const c = canvas();
        if (!c) return;
        const previous = c.onDrawForeground;
        c.onDrawForeground = function (ctx) {
            const r = previous?.apply(this, arguments);
            drawPip(ctx);
            return r;
        };
        window.addEventListener("keydown", onKeyDown, true);
        window.addEventListener("keyup", onKeyUp, true);
        window.addEventListener("pointermove", onPointerMove, true);
        window.addEventListener("pointerup", onPointerUp, true);
        window.addEventListener("blur", () => { if (active()) { reset(); redraw(); } });
    },
});
