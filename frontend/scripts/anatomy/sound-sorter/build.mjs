// Builds the sound sorter, an isometric machine that shows how Word Wiz checks a
// reading, sound by sound. Writes the art and data for the landing page's React
// component, plus a standalone page to review it.
//
//   node scripts/anatomy/sound-sorter/build.mjs            (from /frontend)
//   node scripts/anatomy/sound-sorter/build.mjs --audit    also prove the geometry
//
// The geometry is drawn with the anatomy kit in ../kit (iso-kit, lathe, tube, audit).
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import * as k from "../kit/iso-kit.mjs";
import * as G from "../kit/lathe.mjs";
import { tubePieces, tubeSvg } from "../kit/tube.mjs";
import * as A from "../kit/audit.mjs";
import * as esbuild from "esbuild";
import { BOXES, READINGS, SHAPE_OF, WORDS } from "../../../src/components/landing/soundSorter/model.ts";

const HERE = dirname(fileURLToPath(import.meta.url));
const FRONTEND = join(HERE, "..", "..", "..");
const OUT = join(HERE, "out");

const W = 760;
const H = 424;
const AZIMUTH = 60;
const ELEVATION = 35;

// ---------------------------------------------------------------- layout
const BASE = { x: -216, y: -74, w: 376, d: 146, r: 10 };
const BASE_H = 10;
const FOOT_H = 5;

// The sorting board stands still; the listening head walks along a rail behind it.
const BOARD_CX = 22;
const BOARD = { x: BOARD_CX - 104, y: -27, w: 208, d: 54, r: 4 };
const BOARD_Z = [7, 21];
const TOP = BOARD_Z[1];
const CELL = 18;
const WALL = 1.4;
const RIM = 2.6;
const WORD_GAP = 10;
const CELL_Y = [-CELL / 2, CELL / 2];
const FRAME_Y = [CELL_Y[0] - WALL, CELL_Y[1] + WALL];
const BLOCK_R = 6;
const BLOCK_H = 6;
const HOLE_PAD = 0.8;
const HOLE_DEPTH = 7;
const FLAG_Y = -19;

const wordBoxes = (() => {
  const widths = WORDS.map((word) => word.sounds.length * CELL + (word.sounds.length - 1) * WALL + 2 * WALL);
  const total = widths.reduce((a, b) => a + b, 0) + WORD_GAP * (WORDS.length - 1);
  let x = BOARD_CX - total / 2;
  return widths.map((w, i) => {
    const box = { x0: x, x1: x + w, cells: WORDS[i].sounds.map((_, j) => x + WALL + CELL / 2 + j * (CELL + WALL)) };
    x += w + WORD_GAP;
    return box;
  });
})();
const HOLE_X = wordBoxes.flatMap((box) => box.cells);

// The head's rail, its parking spot and the drop point under the spout (x = 0 in head space).
const RAIL_Y = -54;
const RAIL_X = [-126, 146];
const PARK = -100;
const STOPS = HOLE_X;
const HEAD = { x: -30, y: -24, w: 60, d: 44, r: 6 };
const HEAD_Z = [46, 86];
const FACE_Y = HEAD.y + HEAD.d;
const SPOUT_TIP = 32;
const HAT_AT = [-6, -6, HEAD_Z[1]];

// The tablet on its stand in the front corner, and the horn that speaks.
const STAND = { x: -214, y: 16, w: 88, d: 42, r: 5 };
const STAND_H = 7;
const TILT = (24 * Math.PI) / 180;
const T_N = [0, Math.cos(TILT), Math.sin(TILT)];
const T_UP = [0, -Math.sin(TILT), Math.cos(TILT)];
const T_W = 64;
const T_H = 44;
const T_D = 3.4;
const T_B = [-164, STAND.y + 22, STAND_H + T_D * Math.sin(TILT)];
const HORN_BOSS = [-206, STAND.y + 14, STAND_H];
const HORN_A = G.unit3([-0.5, 0.5, 0.7]);
const HORN_BALL = [HORN_BOSS[0], HORN_BOSS[1], HORN_BOSS[2] + 2.4 + 2.6];
const HORN_T = G.add3(HORN_BALL, G.mul3(HORN_A, 19));
const HORN_L = 30;
const horn = (s) => 1.7 + 12.6 * Math.pow(s / HORN_L, 2.4);
const hornSlope = (s) => (12.6 * 2.4 * Math.pow(Math.max(1e-6, s / HORN_L), 1.4)) / HORN_L;

// ---------------------------------------------------------------- camera
const lastStop = STOPS[STOPS.length - 1];
const P = k.fitProjection(
  [
    ...k.boxCorners(BASE, -BASE_H - FOOT_H, 0),
    [PARK + HAT_AT[0], HAT_AT[1], HEAD_Z[1] + 35],
    [lastStop + HAT_AT[0], HAT_AT[1], HEAD_Z[1] + 35],
    [lastStop + HEAD.x + HEAD.w, HEAD.y + HEAD.d, HEAD_Z[0]],
    G.add3(HORN_T, G.mul3(HORN_A, HORN_L + 4)),
    G.add3(G.add3(HORN_T, G.mul3(HORN_A, HORN_L)), [-15, 0, 8]),
    G.add3(T_B, G.mul3(T_UP, T_H + 6)),
  ],
  W,
  H,
  { pad: 22, azimuth: AZIMUTH, elevation: ELEVATION },
);
const V = G.viewOf(P);
const KS = G.scaleOf(P);
const at = (p) => k.iso(p, P);
const S = (paths, style) => k.solidSvg(paths, style);
const Ln = (d, style) => k.lineSvg(d, style);
const Dots = (points, style) => k.dotsSvg(points, style);
const path3 = (points, closed = false) => k.pathOf(points.map(at), closed);
const f2 = (v) => Math.round(v * 100) / 100;
const byDepth = (points) => [...points].sort((a, b) => k.depthOf([a[0], a[1], 0], P) - k.depthOf([b[0], b[1], 0], P));
const UP = [0, 0, 1];
const Z_FRAME = (o) => G.frameOf(o, UP, [1, 0, 0], [0, 1, 0]);
const Y_FRAME = (o) => G.frameOf(o, [0, 1, 0], [1, 0, 0], [0, 0, 1]);

/** A matrix that maps a plane's local (x right, y down) coordinates onto the screen. */
function planeMatrix(o, ex, ey) {
  const p0 = at(o);
  const px = at(G.add3(o, ex));
  const py = at(G.add3(o, ey));
  const v = (x) => x.toFixed(4);
  return `matrix(${v(px[0] - p0[0])} ${v(px[1] - p0[1])} ${v(py[0] - p0[0])} ${v(py[1] - p0[1])} ${p0[0].toFixed(2)} ${p0[1].toFixed(2)})`;
}

// ---------------------------------------------------------------- recording helpers
// One recorder per layer. The layers paint in this order, bench (BACK), the
// head's column, the board, the head, the tablet. The column and head layers
// are built at x = 0 and slid along the rail.
const BACK = A.recorder(P);
const COLUMN = A.recorder(P);
const HEADR = A.recorder(P);
const TABLET = A.recorder(P);
let R = BACK;
const put = (name, ref, svg, shapes = [], { bias = 0, ...rest } = {}) => R.put({ name, at: ref, bias, svg, shapes, piece: "machine", ...rest });
const rec = (shape) => R.solid(shape);

function box(name, [x0, y0, z0], [x1, y1, z1], style = {}, { r = 0.6, steps = 3, bevel = 0, extra = "", inner = "", bias = 0, ground = false, cls } = {}) {
  const plan = { x: x0, y: y0, w: x1 - x0, d: y1 - y0, r };
  const shape = rec(A.slab(plan, z0, z1 - z0, { name, ground }, steps));
  const solid = S(k.slabOf(plan, z0, z1 - z0, P, steps, bevel), { tone: "mid", ...style, inner });
  put(name, [(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2], (cls ? `<g class="${cls}">${solid}</g>` : solid) + extra, [shape], { bias });
  return shape;
}
function turned(name, F, profile, style = {}, { extra = "", inner = "", bias = 0, smooth, steps, owner, cls } = {}) {
  const opts = { ...(smooth !== undefined ? { smooth } : {}), ...(steps ? { steps } : {}) };
  const paths = G.solidOf(profile, F, P, opts);
  const mid = (profile[0][0] + profile[profile.length - 1][0]) / 2;
  const shape = rec(A.solid(F, profile, { name, owner, radius: smooth && smooth.radius ? smooth.radius : null }));
  const svg = S(paths, { tone: "mid", ...style, inner }) + extra;
  put(name, G.add3(F.o, G.mul3(F.a, mid)), cls ? `<g class="${cls}">${svg}</g>` : svg, [shape], { bias });
  return shape;
}
const disc = (name, F, s0, s1, r, style = {}, options = {}) => turned(name, F, [[s0, r], [s1, r]], style, options);
function prism(name, F, poly, s0, s1, style = {}, { extra = "", bias = 0, cls } = {}) {
  const shape = rec(A.prism(F, poly, s0, s1, { name }));
  const cx = poly.reduce((a, p) => a + p[0], 0) / poly.length;
  const cy = poly.reduce((a, p) => a + p[1], 0) / poly.length;
  const centre = G.add3(G.add3(G.add3(F.o, G.mul3(F.a, (s0 + s1) / 2)), G.mul3(F.u, cx)), G.mul3(F.v, cy));
  const svg = S(G.prismOf(F, poly, s0, s1, P), { tone: "mid", ...style }) + extra;
  put(name, centre, cls ? `<g class="${cls}">${svg}</g>` : svg, [shape], { bias });
  return shape;
}
/** A dome lamp lens, a quarter circle turned about the axis. */
const domeProfile = (r) => Array.from({ length: 9 }, (_, i) => {
  const t = (i / 8) * (Math.PI / 2);
  return i > 0 && i < 8 ? [r * Math.sin(t), r * Math.cos(t), 1] : [r * Math.sin(t), r * Math.cos(t)];
});

function cable(name, points, r, { tone = "mid", bend = 4, shells = [true, true], maxLength = 14, touch } = {}) {
  const route = G.fillet(points, Math.max(bend, r * 2.6), 10, { P, tube: r });
  const total = G.pathLength(route);
  const SHELL = Math.max(2, r * 2.6);
  const gaps = [...(shells[0] ? [[0, SHELL]] : []), ...(shells[1] ? [[total - SHELL, total]] : [])];
  R.route(name, route, r, { gaps, limp: true, touch, rims: shells.map((on) => (on ? r * 1.8 : r)), piece: "machine" });
  const pieces = tubePieces(route, r, P, { maxLength, spacing: Math.max(0.6, Math.min(1.6, r)), gaps });
  pieces.forEach((piece, index) =>
    put(`${name}:${index}`, piece.mid, tubeSvg(piece, { tone }), [A.tube(piece.points, piece.radii)], { bias: 0.05, route: name, chunk: index, attrs: ` data-route="${name}" data-chunk="${index}"` }),
  );
  [0, 1].forEach((index) => {
    if (!shells[index]) return;
    const end = index ? route[route.length - 1] : route[0];
    const tangent = G.tangentAlong(route, index ? total : 0);
    const F = G.frameAlong(end, tangent);
    const [s0, s1] = index ? [-SHELL, 0] : [0, SHELL];
    const shape = rec(A.disc(F, s0, s1, r * 1.8, { name: `${name}.shell${index}`, owner: name }));
    put(`${name}.shell${index}`, G.add3(end, G.mul3(tangent, (s0 + s1) / 2)), S(G.disc(s0, s1, r * 1.8, F, P, { steps: 24 }), { tone: "mid" }), [shape], { bias: 0.15 });
  });
  return { route, pieces: pieces.length };
}

// ---------------------------------------------------------------- shapes
const regular = (n, r, rot = -Math.PI / 2) => Array.from({ length: n }, (_, i) => [r * Math.cos(rot + (i * 2 * Math.PI) / n), r * Math.sin(rot + (i * 2 * Math.PI) / n)]);
const SHAPES = {
  circle: (r) => regular(40, r * 0.92),
  square: (r) => regular(4, r * 1.08, Math.PI / 4),
  diamond: (r) => regular(4, r * 1.1, 0).map(([x, y]) => [x * 0.8, y]),
  triangle: (r) => regular(3, r * 1.18, Math.PI / 2).map(([x, y]) => [x, y + r * 0.2]),
  hexagon: (r) => regular(6, r * 1.02, 0),
  pentagon: (r) => regular(5, r * 1.04, Math.PI / 2),
  star: (r) => Array.from({ length: 10 }, (_, i) => {
    const a = Math.PI / 2 + (i * Math.PI) / 5;
    const rr = i % 2 ? r * 0.5 : r * 1.16;
    return [rr * Math.cos(a), rr * Math.sin(a)];
  }),
  plus: (r) => {
    const a = r * 1.02;
    const t = r * 0.4;
    return [[-t, -a], [t, -a], [t, -t], [a, -t], [a, t], [t, t], [t, a], [-t, a], [-t, t], [-a, t], [-a, -t], [-t, -t]];
  },
  half: (r) => Array.from({ length: 21 }, (_, i) => {
    const a = (i / 20) * Math.PI;
    return [r * 1.1 * Math.cos(a), r * 0.45 - r * 1.1 * Math.sin(a)];
  }),
  oval: (r) => Array.from({ length: 36 }, (_, i) => {
    const a = (i / 36) * 2 * Math.PI;
    return [r * 1.16 * Math.cos(a), r * 0.62 * Math.sin(a)];
  }),
  kite: (r) => [[0, -r * 1.2], [r * 0.78, -r * 0.2], [0, r * 1.2], [-r * 0.78, -r * 0.2]],
  trapezoid: (r) => [[-r * 0.62, -r * 0.82], [r * 0.62, -r * 0.82], [r * 1.12, r * 0.82], [-r * 1.12, r * 0.82]],
};
const CONVEX = new Set(["circle", "square", "diamond", "triangle", "hexagon", "pentagon", "half", "oval", "kite", "trapezoid"]);
const ringOf = (shape, r, [cx, cy] = [0, 0]) => SHAPES[shape](r).map(([x, y]) => [cx + x, cy + y]);

// ================================================================ BENCH
const bench = [];
bench.push(`<path class="iso-halo" d="${k.haloOf(BASE, -BASE_H - FOOT_H, BASE_H, P)}"/>`);
for (const [x, y] of byDepth(k.corners(BASE, 24))) {
  bench.push(S(k.cylinder(x, y, 7.4, -BASE_H - FOOT_H, 1.6, P, 28), { tone: "lo" }));
  bench.push(S(k.cylinder(x, y, 5.6, -BASE_H - FOOT_H + 1.6, FOOT_H - 1.6, P, 28), { tone: "mid" }));
}
bench.push(S(k.slabOf(BASE, -BASE_H, BASE_H, P, 8, 1.6), { tone: "mid", inner: Ln(k.sideSeam(BASE, -4, P, 8), { tone: "faint" }) }));
bench.push(Ln(k.planOutline(k.insetPlan(BASE, 5), 0, P), { tone: "lo" }));
const baseScrews = k.corners(BASE, 10);
bench.push(Ln(baseScrews.map(([x, y]) => k.ring(x, y, 2.2, 0, P, 16)).join(""), { tone: "lo" }));
bench.push(Dots(baseScrews.map(([x, y]) => at([x, y, 0])), { size: 0.5 }));
rec(A.slab(BASE, -BASE_H, BASE_H, { name: "stand.base", ground: true }, 8));

// A ruler along the front edge, the width of the board.
const STRIP = { x: BOARD.x, y: BASE.y + BASE.d - 15, w: BOARD.w - 40, d: 6, r: 1 };
bench.push(S(k.slabOf(STRIP, 0, 0.6, P, 3), { tone: "lo", crease: "none" }));
const ticks = k.topTicks(STRIP.x + 4, STRIP.x + STRIP.w - 4, 4, 5, STRIP.y, 0.6, [1.8, 3.4], P);
bench.push(Ln(ticks.minor, { tone: "lo" }), Ln(ticks.major, { tone: "mid" }));
bench.push(Dots([at([STRIP.x + 2, STRIP.y + 3, 0.6]), at([STRIP.x + STRIP.w - 2, STRIP.y + 3, 0.6])], { size: 0.45 }));

// The label plate, the one engraved label.
const LABEL = { x: BASE.x + BASE.w - 62, y: BASE.y + BASE.d - 28, w: 48, d: 17, r: 1.4 };
bench.push(S(k.slabOf(LABEL, 0, 0.8, P, 3), { tone: "lo", crease: "none" }));
bench.push(Ln(k.planOutline(k.insetPlan(LABEL, 1.6), 0.8, P, 3), { tone: "faint" }));
bench.push(k.faceTextSvg(k.topMatrix([LABEL.x + 5, LABEL.y + 7], 0.8, P, "x"), "WORD WIZ", { size: 4.2, tone: "mid" }));
bench.push(Ln([28, 20].map((w, i) => k.lineOnTop([LABEL.x + 5, LABEL.y + 10.6 + i * 2.8], [LABEL.x + 5 + w, LABEL.y + 10.6 + i * 2.8], 0.8, P)).join(""), { tone: "lo", free: true }));
bench.push(Dots([at([LABEL.x + LABEL.w - 3, LABEL.y + 3, 0.8]), at([LABEL.x + LABEL.w - 3, LABEL.y + LABEL.d - 3, 0.8])], { size: 0.45 }));

// The head's rail and its stops.
box("rail", [RAIL_X[0], RAIL_Y - 2.6, 0], [RAIL_X[1], RAIL_Y + 2.6, 3], { tone: "mid" }, { r: 1, bevel: 0.4, extra: Dots([RAIL_X[0] + 8, (RAIL_X[0] + RAIL_X[1]) / 2, RAIL_X[1] - 8].map((x) => at([x, RAIL_Y, 3])), { size: 0.4 }) });
for (const x of [RAIL_X[0] - 6, RAIL_X[1]]) {
  box("rail.stop", [x, RAIL_Y - 7, 0], [x + 6, RAIL_Y + 7, 9], { tone: "mid" }, { r: 1.2, bevel: 0.5, extra: Dots([at([x + 3, RAIL_Y - 4, 9]), at([x + 3, RAIL_Y + 4, 9])], { size: 0.45 }) });
}
// The junction box where the tablet's cable lands, beside the rail's end.
const JBOX = { x: RAIL_X[0] - 6 - 16, y: RAIL_Y - 8, w: 16, d: 16, r: 2 };
box("jbox", [JBOX.x, JBOX.y, 0], [JBOX.x + JBOX.w, JBOX.y + JBOX.d, 16], { tone: "mid" }, {
  r: JBOX.r,
  bevel: 0.5,
  inner: Ln(k.sideSeam(JBOX, 13, P, 3), { tone: "faint" }),
  extra: Dots([at([JBOX.x + 3, JBOX.y + 3, 16]), at([JBOX.x + JBOX.w - 3, JBOX.y + JBOX.d - 3, 16])], { size: 0.45 }),
});
const LED = [JBOX.x + JBOX.w - 4, JBOX.y + JBOX.d + 0.2, 12];
put("jbox.led", LED, `<g class="ss-led" data-led="jbox">${Dots([at(G.add3(LED, [0, 0.05, 0]))], { size: 1, tone: "hi" })}</g>`, [rec(A.ball(LED, 0.5, { name: "jbox.led" }))], { bias: 0.3 });
// The socket on the stand's back and the cable to the junction box.
const SOCKET = [-140, STAND.y, 3.6];
rec(A.slab(STAND, 0, STAND_H, { name: "tablet.stand" }, 6));
disc("tablet.socket", G.frameOf(SOCKET, [0, -1, 0], [1, 0, 0], [0, 0, 1]), 0, 1.6, 2.8, { tone: "mid" });
const PLUG = [JBOX.x + 6, JBOX.y + JBOX.d, 7];
const LINK = cable("socket", [G.add3(SOCKET, [0, -1.6, 0]), [SOCKET[0], 6, SOCKET[2]], [SOCKET[0], -4, 1.6], [SOCKET[0], -28, 1.6], [PLUG[0], -34, 1.6], [PLUG[0], -38, PLUG[2]], [PLUG[0], PLUG[1] + 1.6, PLUG[2]]], 1.6, { tone: "mid", bend: 4, shells: [false, true], touch: ["stand.base"] });
disc("jbox.socket", G.frameOf(PLUG, [0, 1, 0], [1, 0, 0], [0, 0, 1]), 0, 1.6, 2.8, { tone: "mid" });

/** Record, without drawing, the parts a layer stands on, so the audit can follow each part to the bench. */
function standOn(...shapes) {
  for (const shape of shapes) rec(shape);
}
const BENCH = () => A.slab(BASE, -BASE_H, BASE_H, { name: "stand.base", ground: true }, 8);
const RAIL = () => A.slab({ x: RAIL_X[0], y: RAIL_Y - 2.6, w: RAIL_X[1] - RAIL_X[0], d: 5.2, r: 1 }, 0, 3, { name: "stand.rail" }, 3);

// ================================================================ COLUMN (slides with the head)
R = COLUMN;
standOn(BENCH(), RAIL());
box("column.carriage", [-14, RAIL_Y - 8, 3], [14, RAIL_Y + 8, 7.4], { tone: "mid" }, { r: 1.6, bevel: 0.5, extra: Dots([[-11, RAIL_Y - 5], [11, RAIL_Y - 5], [-11, RAIL_Y + 5], [11, RAIL_Y + 5]].map(([x, y]) => at([x, y, 7.4])), { size: 0.45 }) });
const CF = Z_FRAME([0, RAIL_Y, 0]);
disc("column.collar", CF, 7.4, 10.4, 8, { tone: "mid" });
disc("column", CF, 10.4, 66, 5.4, { tone: "mid" }, { inner: Ln([30, 50].map((z) => G.arcOf(CF, z, 5.4, P)).join(""), { tone: "faint" }) });

// ================================================================ HEAD (walks along the board)
R = HEADR;
standOn(BENCH(), RAIL(), A.slab({ x: -14, y: RAIL_Y - 8, w: 28, d: 16, r: 1.6 }, 3, 4.4, { name: "stand.carriage" }, 3), A.disc(Z_FRAME([0, RAIL_Y, 0]), 7.4, 66, 5.4, { name: "stand.column" }));
const SF = G.frameOf([0, 0, HEAD_Z[0]], [0, 0, -1], [1, 0, 0], [0, -1, 0]);
turned("spout", SF, [[0, 10], [2.6, 10], [3.4, 9.2, 1], [6.2, 8.6, 1], [10, 8.4], [10, 9.4], [HEAD_Z[0] - SPOUT_TIP, 9.4]], { tone: "mid" }, { inner: Ln(G.arcOf(SF, 12, 9.4, P), { tone: "faint" }) });
box("arm", [-5, RAIL_Y + 7.4, 72], [5, HEAD.y, 80], { tone: "mid" }, { r: 1, bevel: 0.4, extra: Dots([at([0, RAIL_Y + 11, 80]), at([0, HEAD.y - 4, 80])], { size: 0.45 }) });
box("arm.collar", [-7.6, RAIL_Y - 7.6, 66], [7.6, RAIL_Y + 7.6, 82], { tone: "mid" }, { r: 3, steps: 4, bevel: 0.5, extra: Dots([at([0, RAIL_Y, 82])], { size: 0.6 }) });
{
  const extra = [
    Dots([[HEAD.x + 4, HEAD_Z[1] - 4], [HEAD.x + HEAD.w - 4, HEAD_Z[1] - 4], [HEAD.x + 4, HEAD_Z[0] + 4], [HEAD.x + HEAD.w - 4, HEAD_Z[0] + 4]].map(([x, z]) => at([x, FACE_Y, z])), { size: 0.5 }),
    Ln([0, 1, 2, 3].map((i) => {
      const y0 = HEAD.y + 8 + i * 7.4;
      return path3([[HEAD.x + HEAD.w, y0, 56], [HEAD.x + HEAD.w, y0 + 3.4, 56], [HEAD.x + HEAD.w, y0 + 3.4, 76], [HEAD.x + HEAD.w, y0, 76]], true);
    }).join(""), { tone: "lo" }),
  ].join("");
  box("head", [HEAD.x, HEAD.y, HEAD_Z[0]], [HEAD.x + HEAD.w, HEAD.y + HEAD.d, HEAD_Z[1]], { tone: "mid" }, { r: HEAD.r, steps: 6, bevel: 0.8, inner: Ln(k.sideSeam(HEAD, HEAD_Z[1] - 5, P, 6), { tone: "faint" }), extra, cls: "ss-yellow" });
}
// The ear, a grille in a bezel ring on the front face.
const EAR = [-11, FACE_Y, 66];
const EARF = Y_FRAME(EAR);
{
  const r = 12.6;
  const grille = [];
  for (let row = -7; row <= 7; row++) for (let col = -8; col <= 8; col++) {
    const x = col * 1.8 + (row % 2 ? 0.9 : 0);
    const z = row * 1.56;
    if (Math.hypot(x, z) < r - 1.6) grille.push(at([EAR[0] + x, FACE_Y + 0.05, EAR[2] + z]));
  }
  const svg = `<path class="iso-shade" data-shade="1" d="${G.circleOf(EARF, 0.02, r, P, 72)}"/>` + `<g class="ss-grille" data-part="grille">${Dots(grille, { size: 0.75, tone: "mid" })}</g>`;
  put("ear.grille", G.add3(EAR, [0, 0.1, 0]), svg, [rec(A.disc(EARF, 0, 0.1, r, { name: "ear.grille" }))], { bias: 0.2 });
  put("ear.bezel", G.add3(EAR, [0, 1.2, 0]), S(G.ringBand(0, 2.4, r, r + 3, EARF, P), { tone: "mid" }), [rec(A.ring(EARF, 0, 2.4, r, r + 3, { name: "ear.bezel" }))], { bias: 0.3 });
}
// The noise meter, a window with a scale and a needle in the plane of the face.
const METER = { u: [6, 25], z: [70, 81] };
const meterNeedle = {};
{
  const m = planeMatrix([METER.u[0], FACE_Y + 0.05, METER.z[1]], [1, 0, 0], [0, 0, -1]);
  const w = METER.u[1] - METER.u[0];
  const h = METER.z[1] - METER.z[0];
  const cx = w / 2;
  const cy = h - 1.4;
  const R0 = 8;
  const point = (deg, r) => [f2(cx + Math.sin((deg * Math.PI) / 180) * r), f2(cy - Math.cos((deg * Math.PI) / 180) * r)];
  const scale = Array.from({ length: 11 }, (_, i) => {
    const deg = -55 + i * 11;
    const [x0, y0] = point(deg, i % 5 ? R0 - 0.9 : R0 - 1.8);
    const [x1, y1] = point(deg, R0);
    return `M${x0} ${y0}L${x1} ${y1}`;
  }).join("");
  const [ax, ay] = point(-55, R0);
  const [bx, by] = point(55, R0);
  const arc = `M${ax} ${ay}A${R0} ${R0} 0 0 1 ${bx} ${by}`;
  Object.assign(meterNeedle, { cx, cy });
  const svg = `<g transform="${m}"><rect class="ss-window" width="${w}" height="${h}" rx="1"/><path class="ss-scale" d="${arc}${scale}"/><g data-part="needle"><path class="ss-needle" d="M${cx} ${cy}L${cx} ${f2(cy - R0 + 0.6)}"/></g><circle class="ss-hub" cx="${cx}" cy="${cy}" r="0.8"/></g>`;
  put("meter", [(METER.u[0] + METER.u[1]) / 2, FACE_Y + 0.1, 75], svg, [rec(A.box([METER.u[0], FACE_Y, METER.z[0]], [METER.u[1], FACE_Y + 0.05, METER.z[1]], { name: "meter" }))], { bias: 0.2 });
}
{
  // Noise-reduction knob, knurled, its pointer at the quiet-room setting.
  const KF = Y_FRAME([16, FACE_Y, 57]);
  const ribs = G.ribsOf(KF, 0.9, 3.8, 4.8, 30, P, { fade: [0.1, 0.55], seams: true });
  const face = [16, FACE_Y + 3.85, 57];
  disc("knob.collar", KF, 0, 0.9, 6, { tone: "mid" });
  disc("knob", KF, 0.9, 3.8, 4.8, { tone: "hi" }, { extra: k.fadedSvg(ribs, { tone: "lo" }) + Ln(path3([face, G.add3(face, [-2.6, 0, 2.4])]), { tone: "hi", free: "end" }), bias: 0.2 });
}
// The listening lamp on the lid, and the hat.
const LAMP = [20, 12, HEAD_Z[1]];
disc("lamp.bezel", Z_FRAME(LAMP), 0, 1, 3.8, { tone: "mid" });
turned("lamp", Z_FRAME(G.add3(LAMP, [0, 0, 1])), domeProfile(2.8), { tone: "hi" }, { cls: "ss-lamp" });
const HATF = Z_FRAME(HAT_AT);
const HAT_BEND = 29;
const HAT_H = 44;
const cone = (s) => 13.6 * Math.pow(Math.max(0, 1 - (s - 1.8) / (HAT_H - 1.8)), 0.9);
const coneSlope = (s) => (-13.6 * 0.9 * Math.pow(Math.max(1e-4, 1 - (s - 1.8) / (HAT_H - 1.8)), -0.1)) / (HAT_H - 1.8);
{
  // Brim, a band round the crown, the crown up to a soft knuckle, and the tip that flops over.
  const brim = G.disc(0, 1.8, 21, HATF, P);
  const band = G.solidOf([[1.8, cone(1.8) + 0.6], [7, cone(7) + 0.6]], HATF, P);
  const KNUCKLE_S = HAT_BEND + 1.2;
  const crownEnd = HAT_BEND;
  const ballR = Math.hypot(cone(crownEnd), KNUCKLE_S - crownEnd);
  const crown = Array.from({ length: 14 }, (_, i) => {
    const s = 7 + ((crownEnd - 7) * i) / 13;
    return i > 0 && i < 13 ? [s, cone(s), 1] : [s, cone(s)];
  });
  const crownPaths = G.solidOf(crown, HATF, P, { smooth: { slope: coneSlope, radius: cone } });
  const knuckleAt = G.pointOf(HATF, KNUCKLE_S, 0, 0);
  const knuckle = G.sphereOf(knuckleAt, ballR, P, { steps: 32 });
  const tipDir = G.unit3([-0.9, 0.2, 0.5]);
  const tipR0 = ballR * 0.9;
  const tipStart = Math.sqrt(ballR * ballR - tipR0 * tipR0);
  const TIPF = G.frameAlong(knuckleAt, tipDir);
  const tipLen = 15;
  const tipR = (s) => tipR0 * Math.pow(Math.max(0, 1 - (s - tipStart) / tipLen), 0.85);
  const tipSlope = (s) => (-tipR0 * 0.85 * Math.pow(Math.max(1e-4, 1 - (s - tipStart) / tipLen), -0.15)) / tipLen;
  const tipKnots = Array.from({ length: 12 }, (_, i) => {
    const s = tipStart + (tipLen * i) / 11;
    return i === 11 ? [s, 0] : i === 0 ? [s, tipR(s)] : [s, tipR(s), 1];
  });
  const tip = G.lathe([[tipStart, 0], ...tipKnots], TIPF, P, { smooth: { slope: tipSlope, radius: tipR } });
  const stars = [[12, -0.35, 2], [21, 0.45, 1.7]].map(([s, a, r]) => {
    const c = at(G.pointOf(HATF, s, cone(s) * 0.98, G.angleToward(HATF, V) + a));
    const pts = Array.from({ length: 8 }, (_, i) => {
      const t = (i * Math.PI) / 4;
      const rr = i % 2 ? r * 0.36 : r;
      return [c[0] + rr * Math.sin(t), c[1] - rr * Math.cos(t)];
    });
    return k.pathOf(pts, true);
  }).join("");
  const svg = `<g class="ss-purple ss-brim">${S(brim, { tone: "hi" })}</g><g class="ss-purple ss-band">${S(band, { tone: "hi" })}</g><g class="ss-purple">${S(crownPaths, { tone: "hi" })}</g><g class="ss-purple">${S(knuckle, { tone: "hi" })}</g><g class="ss-purple">${S(tip, { tone: "hi" })}</g><path class="ss-star" d="${stars}"/>`;
  put("hat", G.add3(HAT_AT, [0, 0, 14]), `<g data-part="hat">${svg}</g>`, [
    rec(A.disc(HATF, 0, 1.8, 21, { name: "hat.brim", owner: "hat" })),
    rec(A.solid(HATF, [[1.8, cone(1.8) + 0.6], [7, cone(7) + 0.6]], { name: "hat.band", owner: "hat" })),
    rec(A.solid(HATF, crown.map(([s, r]) => [s, r]), { name: "hat.crown", owner: "hat", radius: cone })),
    rec(A.ball(knuckleAt, ballR, { name: "hat.knuckle", owner: "hat" })),
    rec(A.lathe(TIPF, [[tipStart, 0], ...tipKnots.map(([s, r]) => [s, r]), [tipStart + tipLen, 0]], { name: "hat.tip", owner: "hat", radius: tipR })),
  ], { bias: 1 });
}

// ================================================================ TABLET (front corner)
R = TABLET;
standOn(BENCH());
box("tablet.stand", [STAND.x, STAND.y, 0], [STAND.x + STAND.w, STAND.y + STAND.d, STAND_H], { tone: "mid" }, {
  r: STAND.r,
  steps: 6,
  bevel: 0.8,
  inner: Ln(k.sideSeam(STAND, 2.4, P, 6), { tone: "faint" }),
  extra: Dots([[STAND.x + 4, STAND.y + 4], [STAND.x + STAND.w - 4, STAND.y + 4], [STAND.x + 4, STAND.y + STAND.d - 4], [STAND.x + STAND.w - 4, STAND.y + STAND.d - 4]].map(([x, y]) => at([x, y, STAND_H])), { size: 0.45 }),
});
box("tablet.ledge", [T_B[0] - 30, T_B[1], STAND_H], [T_B[0] + 30, T_B[1] + 3.6, STAND_H + 5], { tone: "mid" }, { r: 1, bevel: 0.4 });
const TF = G.frameOf(T_B, T_N, [1, 0, 0], T_UP);
const tabletPoly = k.roundedPlan({ x: -T_W / 2, y: 0, w: T_W, d: T_H, r: 4 }, 6);
{
  // A strut from the stand's back to the tablet's back, with a hinge pin at the top.
  const top = G.add3(G.add3(T_B, G.mul3(T_UP, 30)), G.mul3(T_N, -T_D));
  const foot = [T_B[0], STAND.y + 4, STAND_H];
  const dir = G.unit3(G.sub3(top, foot));
  const STF = G.frameOf(foot, dir, [1, 0, 0], G.unit3(G.cross3(dir, [1, 0, 0])));
  prism("tablet.strut", STF, [[-6, -1.2], [6, -1.2], [6, 1.2], [-6, 1.2]], 0, G.len3(G.sub3(top, foot)) - 3.6, { tone: "lo" });
  disc("tablet.hinge", G.frameOf(G.add3(top, G.mul3(T_N, -2)), [1, 0, 0], [0, 1, 0], [0, 0, 1]), -8, 8, 2, { tone: "mid" });
}
prism("tablet", TF, tabletPoly, -T_D, 0, { tone: "mid" });
const screenO = G.add3(G.add3(T_B, G.mul3(T_UP, T_H - 3.6)), G.add3(G.mul3(T_N, 0.04), [-T_W / 2 + 3.6, 0, 0]));
const SCREEN = { w: T_W - 7.2, h: T_H - 7.2, matrix: planeMatrix(screenO, [1, 0, 0], G.mul3(T_UP, -1)) };
{
  // The screen in its own plane, with the sentence as word chips, a spoken line and the mic button.
  const chipW = [18, 17, 16];
  const gap = 3;
  let x = (SCREEN.w - chipW.reduce((a, b) => a + b, 0) - gap * 2) / 2;
  const chips = WORDS.map((word, i) => {
    const out = `<g data-chip="${i}" class="ss-chip"><rect x="${f2(x)}" y="6.4" width="${chipW[i]}" height="10" rx="3"/><text x="${f2(x + chipW[i] / 2)}" y="13.6" text-anchor="middle">${word.text}</text></g>`;
    x += chipW[i] + gap;
    return out;
  }).join("");
  const mx = SCREEN.w / 2;
  const my = 29.4;
  const mic = `<g class="ss-mic" data-part="mic"><circle class="ss-mic-ring" cx="${mx}" cy="${my}" r="5.4"/><circle class="ss-mic-dot" cx="${mx}" cy="${my}" r="3.6"/><path class="ss-mic-glyph" d="M${mx - 0.8} ${my - 2}v1.9a0.8 0.8 0 0 0 1.6 0v-1.9a0.8 0.8 0 0 0 -1.6 0ZM${mx - 1.7} ${my - 0.3}a1.7 1.7 0 0 0 3.4 0M${mx} ${my + 1.4}v0.8"/></g>`;
  const say = `<text class="ss-say" data-part="say" x="${mx}" y="21.6" text-anchor="middle"></text>`;
  const screen = `<g transform="${SCREEN.matrix}"><rect class="ss-screen" width="${f2(SCREEN.w)}" height="${f2(SCREEN.h)}" rx="2"/>${chips}${say}${mic}</g>`;
  const camDot = at(G.add3(G.add3(T_B, G.mul3(T_UP, T_H - 1.8)), G.mul3(T_N, 0.05)));
  put("tablet.screen", G.add3(T_B, G.add3(G.mul3(T_UP, T_H / 2), G.mul3(T_N, 0.1))), screen + Dots([camDot], { size: 0.5, tone: "lo" }), [rec(A.prism(TF, [[-T_W / 2 + 3.6, 3.6], [T_W / 2 - 3.6, 3.6], [T_W / 2 - 3.6, T_H - 3.6], [-T_W / 2 + 3.6, T_H - 3.6]], 0, 0.05, { name: "tablet.screen" }))], { bias: 0.5 });
}
// The record button on the stand.
const REC = [STAND.x + STAND.w - 11, STAND.y + STAND.d - 9];
disc("rec.bezel", Z_FRAME([...REC, STAND_H]), 0, 1, 4.8, { tone: "mid" });
disc("rec.cap", Z_FRAME([...REC, STAND_H]), 1, 2.8, 3.6, { tone: "hi" }, { cls: "ss-purple ss-rec" });
// The horn, with a boss, a neck and a flared bell.
disc("horn.boss", Z_FRAME(HORN_BOSS), 0, 2.4, 4.2, { tone: "mid" });
const HF = G.frameAlong(HORN_T, HORN_A);
{
  // A ball joint on the boss, and a straight neck from the ball to the bell.
  const ball = rec(A.ball(HORN_BALL, 3, { name: "horn.ball" }));
  put("horn.ball", HORN_BALL, S(G.sphereOf(HORN_BALL, 3, P, { steps: 32 }), { tone: "mid" }), [ball], { bias: 0.1 });
  const neck = [G.add3(HORN_BALL, G.mul3(HORN_A, Math.sqrt(9 - 1.7 * 1.7))), G.add3(HORN_T, G.mul3(HORN_A, -1.2))];
  R.route("horn.neck", neck, 1.7, { piece: "machine" });
  tubePieces(neck, 1.7, P, { maxLength: 30 }).forEach((piece, index) => put(`horn.neck:${index}`, piece.mid, tubeSvg(piece, { tone: "mid" }), [A.tube(piece.points, piece.radii)], { bias: 0.05, route: "horn.neck", chunk: index }));
}
disc("horn.collar", HF, -1.2, 1.4, 2.9, { tone: "mid" });
{
  const knots = Array.from({ length: 25 }, (_, i) => {
    const s = 1.4 + ((HORN_L - 1.4) * i) / 24;
    return i > 0 && i < 24 ? [s, horn(s), 1] : [s, horn(s)];
  });
  const paths = G.lathe(knots, HF, P, { smooth: { slope: hornSlope, radius: horn }, rims: "first" });
  const mouth = G.circleOf(HF, HORN_L, horn(HORN_L) - 0.6, P, 96);
  const lip = G.circleOf(HF, HORN_L, horn(HORN_L), P, 96);
  const inside = G.arcOf(HF, HORN_L - 8, horn(HORN_L - 8), P, { inward: true, slope: hornSlope(HORN_L - 8) });
  const svg = S(paths, { tone: "hi" }) + `<path class="ss-void" d="${mouth}"/>` + Ln(inside, { tone: "faint" }) + Ln(lip, { tone: "hi" });
  put("horn.bell", G.add3(HORN_T, G.mul3(HORN_A, HORN_L * 0.6)), svg, [rec(A.lathe(HF, [[1.4, 0], ...knots.map(([s, r]) => [s, r]), [HORN_L, 0]], { name: "horn.bell", radius: horn }))]);
}

// ================================================================ BOARD (stands still)
const board = [];
const C = (svg) => board.push(svg);
const CS = (paths, style) => C(S(paths, style));
for (const [x, y] of byDepth(k.corners(BOARD, 14))) {
  CS(k.slabOf({ x: x - 6, y: y - 6, w: 12, d: 12, r: 2 }, 0, BOARD_Z[0], P, 4, 0.4), { tone: "lo" });
}
CS(k.slabOf(BOARD, BOARD_Z[0], BOARD_Z[1] - BOARD_Z[0], P, 6, 1), { tone: "mid", inner: Ln(k.sideSeam(BOARD, 11, P, 6), { tone: "faint" }) });
C(Dots([[BOARD.x + 4, BOARD.y + 4], [BOARD.x + BOARD.w - 4, BOARD.y + 4], [BOARD.x + 4, BOARD.y + BOARD.d - 4], [BOARD.x + BOARD.w - 4, BOARD.y + BOARD.d - 4]].map(([x, y]) => at([x, y, TOP])), { size: 0.45 }));

// Flags behind each word box. Each has a mast, a ball and a pennant that pops up on a clearly wrong word.
const flagX = wordBoxes.map((b) => b.x0 + 3);
wordBoxes.forEach((b, i) => {
  const x = flagX[i];
  CS(k.cylinder(x, FLAG_Y, 1.8, TOP, 1, P, 20), { tone: "mid" });
  CS(k.cylinder(x, FLAG_Y, 0.75, TOP + 1, 19.2, P, 16), { tone: "mid", crease: "none" });
  C(S(G.sphereOf([x, FLAG_Y, TOP + 21.4], 1.4, P, { steps: 24 }), { tone: "mid" }));
  const FF = G.frameOf([x, FLAG_Y, 0], [0, 1, 0], [1, 0, 0], [0, 0, 1]);
  const pennant = G.prismOf(FF, [[0.75, TOP + 12.4], [14, TOP + 16.2], [0.75, TOP + 20]], -0.45, 0.45, P);
  C(`<g data-flag="${i}" class="ss-flag" style="display:none"><g data-move>${S(pennant, { tone: "hi" })}</g></g>`);
});

// Word boxes, drawn as back walls, then each cell with its hole, its blocks and the divider to its right, then front walls.
const blockDefs = [];
const clipDefs = [];
function holeSvg(i, x, shape) {
  const ring = ringOf(shape, BLOCK_R + HOLE_PAD, [x, 0]);
  const pts = ring.map(([px, py]) => at([px, py, TOP]));
  const n = ring.length;
  const signed = ring.reduce((a, [x0, y0], j) => {
    const [x1, y1] = ring[(j + 1) % n];
    return a + x0 * y1 - x1 * y0;
  }, 0);
  const walls = [];
  for (let j = 0; j < n; j++) {
    const a = ring[j];
    const b = ring[(j + 1) % n];
    const dx = b[0] - a[0];
    const dy = b[1] - a[1];
    const inward = signed > 0 ? [-dy, dx] : [dy, -dx];
    const len = Math.hypot(...inward);
    const nrm = [inward[0] / len, inward[1] / len, 0];
    if (G.dot3(nrm, V) <= 0) continue;
    walls.push({ tone: G.toneOf(nrm, P), d: path3([[a[0], a[1], TOP], [b[0], b[1], TOP], [b[0], b[1], TOP - HOLE_DEPTH], [a[0], a[1], TOP - HOLE_DEPTH]], true) });
  }
  const outline = k.pathOf(pts, true);
  clipDefs.push(`<clipPath id="ss-hole-${i}"><path d="${outline}"/></clipPath>`);
  // A block sinking into the hole shows only above the hole's near rim.
  const hull = G.hullOf(pts);
  const left = hull.reduce((m, p) => (p[0] < m[0] ? p : m));
  const right = hull.reduce((m, p) => (p[0] > m[0] ? p : m));
  const lower = hull.filter((p) => p[1] >= left[1] + ((p[0] - left[0]) / (right[0] - left[0] || 1)) * (right[1] - left[1]) - 1e-6).sort((a, b) => a[0] - b[0]);
  clipDefs.push(`<clipPath id="ss-sink-${i}"><path d="${k.pathOf([...lower, [right[0], -400], [left[0], -400]], true)}"/></clipPath>`);
  return `<g data-hole="${i}" class="ss-hole"><path class="ss-hole-floor" d="${outline}"/><g clip-path="url(#ss-hole-${i})">${walls.map((w) => `<path class="iso-shade" data-shade="${Math.min(3, w.tone)}" d="${w.d}"/>`).join("")}</g><path class="ss-hole-rim" d="${outline}"/></g>`;
}
function blockSvg(shape) {
  return S(k.extrude(ringOf(shape, BLOCK_R), 0, BLOCK_H, P, { convex: CONVEX.has(shape), bevel: 0.3 }), { tone: "hi" });
}
// Every block a reading can drop in each box.
const variants = BOXES.map((box, i) => [...new Set([box.ipa, ...READINGS.map((reading) => reading.heard[i]).filter(Boolean)])]);

wordBoxes.forEach((b) => CS(k.slabOf({ x: b.x0, y: FRAME_Y[0], w: b.x1 - b.x0, d: WALL, r: 0.3 }, TOP, RIM, P, 2), { tone: "mid" }));
let cell = 0;
wordBoxes.forEach((b) => {
  CS(k.slabOf({ x: b.x0, y: FRAME_Y[0] + WALL, w: WALL, d: CELL, r: 0.2 }, TOP, RIM, P, 2), { tone: "mid" });
  b.cells.forEach((x, j) => {
    const i = cell++;
    C(holeSvg(i, x, SHAPE_OF[BOXES[i].ipa]));
    for (const ipa of variants[i]) {
      const shape = SHAPE_OF[ipa];
      C(`<g data-block="${i}" data-ipa="${ipa}" style="display:none"><g data-move>${blockSvg(shape)}</g></g>`);
      blockDefs.push({ hole: i, ipa, shape });
    }
    const right = j < b.cells.length - 1 ? x + CELL / 2 : b.x1 - WALL;
    CS(k.slabOf({ x: right, y: FRAME_Y[0] + WALL, w: WALL, d: CELL, r: 0.2 }, TOP, RIM, P, 2), { tone: "mid" });
  });
});
wordBoxes.forEach((b) => CS(k.slabOf({ x: b.x0, y: FRAME_Y[1] - WALL, w: b.x1 - b.x0, d: WALL, r: 0.3 }, TOP, RIM, P, 2), { tone: "mid" }));
// Score lamps on the front strip, one per word, lit in the word's colour band.
wordBoxes.forEach((b, i) => {
  const c = [(b.x0 + b.x1) / 2, 18.4, TOP];
  CS(k.cylinder(c[0], c[1], 3.8, TOP, 0.9, P, 28), { tone: "mid" });
  C(`<g data-lamp="${i}" class="ss-wordlamp">${S(G.solidOf(domeProfile(2.8), Z_FRAME(G.add3(c, [0, 0, 0.9])), P), { tone: "hi" })}</g>`);
});
// Drawer fronts on the board's face, one per word, with a pull and a card holder.
wordBoxes.forEach((b) => {
  const y = BOARD.y + BOARD.d;
  const x0 = b.x0 + 1;
  const x1 = b.x1 - 1;
  CS(k.slabOf({ x: x0, y, w: x1 - x0, d: 0.8, r: 0.3 }, BOARD_Z[0] + 2, 10, P, 2, 0.3), { tone: "mid" });
  C(Ln(path3([[x0 + 3, y + 0.82, 18.4], [x0 + 14, y + 0.82, 18.4], [x0 + 14, y + 0.82, 13], [x0 + 3, y + 0.82, 13]], true), { tone: "lo" }));
  const PF = Y_FRAME([(x0 + x1) / 2 + 6, y + 0.8, 15]);
  C(S(G.disc(0, 1.4, 1.2, PF, P, { steps: 20 }), { tone: "mid" }));
  C(S(G.disc(1.4, 2.6, 2.4, PF, P, { steps: 24 }), { tone: "hi" }));
});

// ---------------------------------------------------------------- order and assemble
for (const Rx of [BACK, COLUMN, HEADR, TABLET]) {
  A.settle(Rx, P);
  Rx.items.sort((a, b) => a.key - b.key);
}
const group = (Rx) => Rx.items.map((item) => `<g class="it" data-name="${item.name}"${item.attrs ?? ""}>${item.svg}</g>`).join("");

// Sound rings: the voice going into the tablet's mic, and the horn's reply.
const hornRings = `<g data-part="horn-rings">${Array.from({ length: 4 }, (_, i) => `<path class="ss-ring" data-ring="${i}" d="${G.circleOf(HF, HORN_L + 3 + i * 4.6, horn(HORN_L) + 1.4 + i * 2.6, P, 72)}"/>`).join("")}</g>`;
const MIC_AT = G.add3(G.add3(T_B, G.mul3(T_UP, T_H + 1)), [-T_W / 2 + 12, 0, 0]);
const voiceRings = `<g data-part="voice-rings">${Array.from({ length: 3 }, (_, i) => `<path class="ss-ring" data-ring="${i}" d="${G.circleOf(G.frameAlong(MIC_AT, T_UP), 0.6 + i * 1.2, 3 + i * 3.4, P, 48)}"/>`).join("")}</g>`;

const headAt = (x) => k.translateAlong(P, [x, 0, 0]);
const body = [
  `<defs>${clipDefs.join("")}</defs>`,
  ...bench,
  `<g class="ss-back">${group(BACK)}</g>`,
  `<g data-part="column" transform="${headAt(PARK)}">${group(COLUMN)}</g>`,
  `<g data-part="board">${board.join("")}</g>`,
  `<g data-part="head" transform="${headAt(PARK)}"><g data-part="bob">${group(HEADR)}</g></g>`,
  `<g class="ss-tablet">${group(TABLET)}</g>`,
  voiceRings,
  hornRings,
];

const LABEL_TEXT =
  "A sound-sorting machine on a bench. In the front corner a tablet on a stand records a child reading “The dog ran.”, with a horn beside it that speaks the feedback. A cable carries the recording to a rail at the back, where a listening head wearing the Word Wiz hat walks along a board. The board has one row of shaped holes per word, one hole for each sound the word needs. Over each hole the head drops a block shaped like the sound it heard: matching blocks drop in, wrong ones stick on top, and a flag pops up behind a word with three wrong sounds.";
const svg = k.figureSvg({ width: W, height: H, label: LABEL_TEXT, body, className: "ss-svg" });

// ---------------------------------------------------------------- data for the live code
const o = k.iso([0, 0, 0], P);
const axis = (v) => k.iso(v, P).map((c, i) => f2(c - o[i]));
const hatPivot = at(HAT_AT).map(f2);
const DATA = {
  basis: { x: axis([1, 0, 0]), y: axis([0, 1, 0]), z: axis([0, 0, 1]) },
  park: PARK,
  stops: STOPS.map(f2),
  top: TOP,
  blockH: BLOCK_H,
  spoutTip: SPOUT_TIP,
  holeDepth: HOLE_DEPTH,
  hatPivot,
  needle: meterNeedle,
  cable: { name: "socket", chunks: LINK.pieces },
  blocks: blockDefs,
};

// ---------------------------------------------------------------- write
const CSS = readFileSync(join(HERE, "sound-sorter.css"), "utf8");
mkdirSync(OUT, { recursive: true });
writeFileSync(join(OUT, "art.json"), JSON.stringify({ svg, data: DATA }));
const plate = k.plateHtml({
  fig: "Fig 1",
  title: "The sound sorter",
  hint: "Tap for the next reading",
  readout: "ready",
  keys: [
    { mark: "lit", label: "The sound being checked" },
    { mark: "raised", label: "One box per sound in each word" },
  ],
  caption: "",
  body: `<div class="iso-stage ss-stage" tabindex="0" role="group" aria-label="The sound sorter. Press space or tap for the next reading.">${svg}</div>`,
});
// The page runs the same live code as the React component, bundled with esbuild.
const live = esbuild
  .buildSync({ entryPoints: [join(FRONTEND, "src", "components", "landing", "soundSorter", "live.ts")], bundle: true, format: "esm", write: false, target: "es2022" })
  .outputFiles[0].text.replace(/^export \{[^}]*\};?\s*$/m, "");
for (const theme of ["light", "dark"]) {
  const script = `${live}\nmountSoundSorter(document.querySelector(".ss-stage"), ${JSON.stringify(DATA)}, { readout: document.querySelector("[data-readout]") });`;
  const page = k.pageHtml({ title: "Sound sorter", theme, body: `<style>${CSS}</style>${plate}`, script, width: 900 });
  writeFileSync(join(OUT, theme === "light" ? "sound-sorter-light.html" : "sound-sorter.html"), page);
}
// The landing page's copy: the art and data as a module, and the kit's styles with the sorter's own.
const SRC = join(FRONTEND, "src", "components", "landing", "soundSorter");
writeFileSync(
  join(SRC, "art.generated.ts"),
  `// Generated by scripts/anatomy/sound-sorter/build.mjs. Edit that script and rebuild; don't edit this file.
import type { SorterData } from "./live";

export const SORTER_SVG = ${JSON.stringify(svg)};

export const SORTER_DATA: SorterData = ${JSON.stringify(DATA)};
`,
);
writeFileSync(join(SRC, "sorter.generated.css"), `/* Generated by scripts/anatomy/sound-sorter/build.mjs from the anatomy kit's iso.css and sound-sorter.css. */
${readFileSync(join(HERE, "..", "kit", "iso.css"), "utf8")}
${CSS}`);
console.log("wrote", `${(svg.length / 1024).toFixed(0)} KB svg`, `${[BACK, COLUMN, HEADR, TABLET].reduce((n, Rx) => n + Rx.items.length, 0)} items`, `${board.length} board pieces`, `scale ${KS.toFixed(3)}`);

for (const [name, Rx] of [["bench", BACK], ["column", COLUMN], ["head", HEADR], ["tablet", TABLET]]) {
  if (process.argv.includes("--audit")) console.log(`\n== ${name}`);
  A.auditOrExit(Rx, P, {});
}
