/* PokéQuant static demo: reads window.POKEQUANT (data/results.js) and renders the six steps. */
(function () {
  "use strict";

  var D = window.POKEQUANT;
  var $ = function (id) { return document.getElementById(id); };
  var SVGNS = "http://www.w3.org/2000/svg";
  var state = { set: null, scenario: "central", budget: 36 };
  var LABEL = { gross: "Gross (reference)", central: "Central", adverse: "Adverse (prudent)" };
  var SCEN_HINT = {
    gross: "No fees, no shipping, no haircut: a theoretical reference, never the main result.",
    central: "Main result: TCGplayer seller fees, 1 USD shipping per card, 15 % liquidity haircut.",
    adverse: "Prudent case: booster 1 USD above retail, tracked shipping, 30 % haircut."
  };
  var VERDICT = { "decisive: A": "A better", "decisive: B": "B better", undetermined: "Undetermined", tie: "Tie" };

  if (!D) {
    $("banner-text").textContent = "The data file could not be loaded.";
    return;
  }

  // ---------- helpers ----------
  function el(tag, attrs, text) {
    var e = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    if (text !== undefined) e.textContent = text;
    return e;
  }
  function svg(tag, attrs, text) {
    var e = document.createElementNS(SVGNS, tag);
    if (attrs) Object.keys(attrs).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    if (text !== undefined) e.textContent = text;
    return e;
  }
  function usd(x, d) {
    if (x === null || x === undefined || isNaN(x)) return "n/a";
    var digits = d === undefined ? (Math.abs(x) >= 100 ? 0 : 2) : d;
    return (x < 0 ? "−" : "") + Math.abs(x).toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });
  }
  function pct(x) { return (100 * x).toFixed(1) + " %"; }
  function fmt(metric, x) { return metric === "p_loss" || metric === "p_gain" ? pct(x) : usd(x); }
  function scen(name) { return D.scenarios.filter(function (s) { return s.name === name; })[0]; }
  function setName(id) { return D.sets.filter(function (s) { return s.id === id; })[0].name; }
  function row(set, label, scenario, metric) {
    return D.rows.filter(function (r) {
      return r.set === set && r.label === label && r.scenario === scenario && r.metric === metric;
    })[0];
  }
  function picker(container, options, current, onPick) {
    container.innerHTML = "";
    options.forEach(function (o) {
      var b = el("button", { type: "button", role: "radio", "aria-checked": String(o.value === current) }, o.label);
      b.addEventListener("click", function () { onPick(o.value); });
      b.addEventListener("keydown", function (ev) {
        var i = options.indexOf(o);
        if (ev.key === "ArrowRight" || ev.key === "ArrowDown") { onPick(options[(i + 1) % options.length].value); ev.preventDefault(); focusChecked(container); }
        if (ev.key === "ArrowLeft" || ev.key === "ArrowUp") { onPick(options[(i - 1 + options.length) % options.length].value); ev.preventDefault(); focusChecked(container); }
      });
      b.tabIndex = o.value === current ? 0 : -1;
      container.appendChild(b);
    });
  }
  function focusChecked(container) {
    var b = container.querySelector('[aria-checked="true"]');
    if (b) b.focus();
  }
  var tip = $("tooltip");
  function showTip(ev, html) {
    tip.innerHTML = html;
    tip.hidden = false;
    var x = Math.min(ev.clientX + 14, window.innerWidth - tip.offsetWidth - 8);
    var y = Math.max(8, ev.clientY - tip.offsetHeight - 12);
    tip.style.left = x + "px";
    tip.style.top = y + "px";
  }
  function hideTip() { tip.hidden = true; }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  // ---------- banner & provenance ----------
  var M = D.meta;
  $("banner-text").textContent =
    "Experimental research results, not financial advice. Card values use the " + M.price_type +
    " in " + M.currency + " on " + M.price_date + "; card condition " + M.condition +
    ". Every number depends on these prices and on the cost assumptions of step 2. " +
    "Intervals are 95 % intervals over pull-rate uncertainty.";
  var prov = $("provenance");
  prov.classList.add("wide");
  [
    ["Run", M.run_id + " (seed " + M.seed + ", " + M.epistemic_draws + " pull-rate draws × " + M.aleatory_runs.toLocaleString("en-US") + " simulated runs)"],
    ["Config", M.config + " (pre-registered, tag prereg-v2)"],
    ["Results checksum", "sha256 " + M.results_sha256.slice(0, 16) + "…"],
    ["Price date and type", M.price_date + " · " + M.price_type + " · " + M.currency]
  ].concat(M.attribution.map(function (a) { return ["Source", a]; })).forEach(function (p) {
    var d = el("div"); d.appendChild(el("dt", null, p[0])); d.appendChild(el("dd", null, p[1])); prov.appendChild(d);
  });

  // ---------- step 1 & 2 ----------
  state.set = D.sets[0].id;
  function renderPickers() {
    picker($("set-picker"), D.sets.map(function (s) { return { value: s.id, label: s.name }; }), state.set, function (v) { state.set = v; render(); });
    picker($("scenario-picker"), D.scenarios.map(function (s) { return { value: s.name, label: LABEL[s.name] || s.name }; }), state.scenario, function (v) { state.scenario = v; resetCalc(); render(); });
    picker($("budget-picker"), D.budgets.map(function (n) { return { value: n, label: n + (n === 1 ? " booster" : " boosters") }; }), state.budget, function (v) { state.budget = v; render(); });
    $("set-hint").textContent = setName(state.set) + " (" + state.set + "), English booster packs.";
    var s = scen(state.scenario);
    var p = $("scenario-params");
    p.innerHTML = "";
    [
      ["Booster price", usd(s.booster_cost) + " USD"],
      ["Seller fee rate", pct(s.marketplace_fee_rate + s.payment_fee_rate)],
      ["Fixed fee per sale", usd(s.selling_fixed_fee) + " USD"],
      ["Shipping per card sold", usd(s.shipping_per_sale) + " USD"],
      ["Shipping per card bought", usd(s.buyer_shipping) + " USD"],
      ["Liquidity haircut", pct(s.liquidity_haircut)]
    ].forEach(function (kv) {
      var d = el("div"); d.appendChild(el("dt", null, kv[0])); d.appendChild(el("dd", null, kv[1])); p.appendChild(d);
    });
    $("scenario-hint").textContent = SCEN_HINT[s.name] || s.description;
  }

  // ---------- step 3: break-even ----------
  function tile(label, value, sub) {
    var t = el("div", { class: "tile" });
    t.appendChild(el("div", { class: "label" }, label));
    t.appendChild(el("div", { class: "value" }, value));
    t.appendChild(el("div", { class: "sub" }, sub));
    return t;
  }
  function renderTiles() {
    var be = D.break_even[state.set][state.scenario];
    var s = scen(state.scenario);
    var box = $("be-tiles");
    box.innerHTML = "";
    box.appendChild(tile("Break-even booster price", usd(be.mean) + " USD", "95 % interval " + usd(be.low) + " to " + usd(be.high)));
    box.appendChild(tile("Booster price assumed", usd(s.booster_cost) + " USD", "Scenario: " + (LABEL[s.name] || s.name)));
    var gap = s.booster_cost - be.mean;
    box.appendChild(tile(gap >= 0 ? "Expected loss per booster opened" : "Expected gain per booster opened", usd(Math.abs(gap)) + " USD",
      be.high < s.booster_cost ? "Opening loses on average: the whole interval is below the price" : "The interval reaches the booster price"));
  }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function gridValue(g, field, k, f) {
    var K = g.keep, F = g.fixed, Z = g[field];
    k = Math.min(Math.max(k, K[0]), K[K.length - 1]);
    f = Math.min(Math.max(f, F[0]), F[F.length - 1]);
    var i = Math.min(K.length - 2, Math.floor((k - K[0]) / (K[1] - K[0])));
    var j = Math.min(F.length - 2, Math.floor((f - F[0]) / (F[1] - F[0])));
    var tk = (k - K[i]) / (K[i + 1] - K[i]), tf = (f - F[j]) / (F[j + 1] - F[j]);
    return lerp(lerp(Z[i][j], Z[i][j + 1], tf), lerp(Z[i + 1][j], Z[i + 1][j + 1], tf), tk);
  }
  function resetCalc() {
    var s = scen(state.scenario);
    $("in-booster").value = s.booster_cost.toFixed(2);
    $("in-fee").value = (100 * (s.marketplace_fee_rate + s.payment_fee_rate)).toFixed(2);
    $("in-haircut").value = Math.round(100 * s.liquidity_haircut);
    $("in-fixed").value = s.fixed.toFixed(2);
  }
  function num(id, lo, hi) {
    var v = parseFloat($(id).value);
    if (isNaN(v)) return null;
    return Math.min(Math.max(v, lo), hi);
  }
  function renderCalc() {
    var b = num("in-booster", 0, 20), fee = num("in-fee", 0, 30), h = num("in-haircut", 0, 50), f = num("in-fixed", 0, 6);
    var out = $("calc-result");
    if (b === null || fee === null || h === null || f === null) { out.textContent = "Enter a number in every field."; return; }
    var k = (1 - h / 100) * (1 - fee / 100);
    var g = D.break_even_grid[state.set];
    var m = gridValue(g, "mean", k, f), lo = gridValue(g, "low", k, f), hi = gridValue(g, "high", k, f);
    out.innerHTML = "";
    out.appendChild(document.createTextNode("Break-even booster price: " + usd(m) + " USD (95 % interval " + usd(lo) + " to " + usd(hi) + "). "));
    var v;
    if (hi < b) v = el("span", { class: "verdict-bad" }, "At " + usd(b) + " USD a booster, opening loses about " + usd(b - m) + " USD per booster on average.");
    else if (lo > b) v = el("span", { class: "verdict-good" }, "At " + usd(b) + " USD a booster, opening gains on average (before risk).");
    else v = el("span", null, "At " + usd(b) + " USD a booster, the sign of the average profit is undetermined.");
    out.appendChild(v);
    drawBreakEven(g, k, f, b);
  }

  function axisTicks(lo, hi, n) {
    var span = hi - lo, step = Math.pow(10, Math.floor(Math.log10(span / n)));
    [1, 2, 2.5, 5, 10].some(function (m) { if (span / (step * m) <= n) { step *= m; return true; } return false; });
    var t = [], v = Math.ceil(lo / step) * step;
    for (; v <= hi + 1e-9; v += step) t.push(+v.toFixed(6));
    return t;
  }

  function drawBreakEven(g, k, f, booster) {
    var W = Math.max(320, $("be-chart").clientWidth || 900), H = W < 560 ? 260 : 320, L = 52, R = 12, T = 14, B = 42;
    var F = g.fixed;
    var pts = F.map(function (x) { return { x: x, m: gridValue(g, "mean", k, x), lo: gridValue(g, "low", k, x), hi: gridValue(g, "high", k, x) }; });
    var ymax = Math.max(booster, pts[0].hi) * 1.08;
    var xs = function (x) { return L + (x - F[0]) / (F[F.length - 1] - F[0]) * (W - L - R); };
    var ys = function (y) { return T + (1 - y / ymax) * (H - T - B); };
    var s = svg("svg", { viewBox: "0 0 " + W + " " + H, role: "img", "aria-label": "Break-even booster price against the fixed cost per card sold" });
    axisTicks(0, ymax, 5).forEach(function (t) {
      s.appendChild(svg("line", { class: "gridline", x1: L, x2: W - R, y1: ys(t), y2: ys(t) }));
      s.appendChild(svg("text", { x: L - 8, y: ys(t) + 4, "text-anchor": "end" }, usd(t)));
    });
    axisTicks(F[0], F[F.length - 1], W < 560 ? 4 : 8).forEach(function (t) {
      s.appendChild(svg("text", { x: xs(t), y: H - B + 18, "text-anchor": "middle" }, usd(t)));
    });
    s.appendChild(svg("line", { class: "axis", x1: L, x2: W - R, y1: ys(0), y2: ys(0) }));
    s.appendChild(svg("text", { x: (L + W - R) / 2, y: H - 4, "text-anchor": "middle" }, "Fixed cost per card sold (USD)"));
    var band = pts.map(function (p) { return xs(p.x) + "," + ys(p.hi); }).concat(pts.slice().reverse().map(function (p) { return xs(p.x) + "," + ys(p.lo); }));
    s.appendChild(svg("polygon", { class: "band-a", points: band.join(" ") }));
    s.appendChild(svg("polyline", { class: "line-a", points: pts.map(function (p) { return xs(p.x) + "," + ys(p.m); }).join(" ") }));
    s.appendChild(svg("line", { class: "line-ref", x1: L, x2: W - R, y1: ys(booster), y2: ys(booster) }));
    s.appendChild(svg("text", { class: "label-ref", x: W - R, y: ys(booster) - 6, "text-anchor": "end" }, "Booster price " + usd(booster)));
    var my = gridValue(g, "mean", k, f);
    s.appendChild(svg("circle", { class: "dot-a ring", cx: xs(Math.min(Math.max(f, F[0]), F[F.length - 1])), cy: ys(my), r: 6 }));
    var cross = svg("line", { class: "crosshair", y1: T, y2: H - B, x1: -10, x2: -10 });
    s.appendChild(cross);
    var hit = svg("rect", { x: L, y: T, width: W - L - R, height: H - T - B, fill: "transparent" });
    hit.addEventListener("mousemove", function (ev) {
      var r = s.getBoundingClientRect();
      var x = (ev.clientX - r.left) / r.width * W;
      var fx = F[0] + (x - L) / (W - L - R) * (F[F.length - 1] - F[0]);
      var i = Math.round((fx - F[0]) / (F[1] - F[0]));
      i = Math.max(0, Math.min(F.length - 1, i));
      var p = pts[i];
      cross.setAttribute("x1", xs(p.x)); cross.setAttribute("x2", xs(p.x));
      showTip(ev, "Fixed cost " + usd(p.x) + " USD<br><b>Break-even " + usd(p.m) + "</b> [" + usd(p.lo) + ", " + usd(p.hi) + "]");
    });
    hit.addEventListener("mouseleave", function () { cross.setAttribute("x1", -10); cross.setAttribute("x2", -10); hideTip(); });
    s.appendChild(hit);
    var box = $("be-chart"); box.innerHTML = ""; box.appendChild(s);
    $("be-caption").textContent = "Break-even booster price as the fixed cost per card sold changes · " + setName(state.set);
    var lg = $("be-legend"); lg.innerHTML = "";
    var a = el("span"); a.appendChild(el("i", { class: "sw-a" })); a.appendChild(document.createTextNode("Break-even price, 95 % band")); lg.appendChild(a);
    var c = el("span"); c.appendChild(el("i", { class: "sw-ref" })); c.appendChild(document.createTextNode("Booster price")); lg.appendChild(c);
    $("be-source").textContent = "Fee rate and haircut as entered. Prices: " + M.price_type + ", " + M.price_date + ". Grid computed from the " + M.epistemic_draws + " pull-rate draws of run " + M.run_id + ".";
  }

  // ---------- step 4: E1 ----------
  function cell(r, metric) {
    var td = el("td");
    td.appendChild(document.createTextNode(fmt(metric, r.a_mean)));
    td.appendChild(el("br"));
    td.appendChild(el("span", { class: "ci" }, "[" + fmt(metric, r.a_low) + ", " + fmt(metric, r.a_high) + "]"));
    return td;
  }
  function badge(verdict) {
    var cls = verdict === "decisive: B" ? "badge b" : verdict === "decisive: A" ? "badge a" : "badge";
    return el("span", { class: cls }, VERDICT[verdict] || verdict);
  }
  function renderE1() {
    var label = "n=" + state.budget;
    var s = scen(state.scenario);
    var t = $("e1-table"); t.innerHTML = "";
    var cap = el("caption", { class: "hint" }, setName(state.set) + " · " + (LABEL[s.name] || s.name) + " · budget " + usd(state.budget * s.booster_cost) + " USD (" + state.budget + " × " + usd(s.booster_cost) + ")");
    t.appendChild(cap);
    var head = el("tr");
    ["Metric", "A: open (mean over draws, 95 % interval)", "B: buy", "Share of draws A better", "Verdict"].forEach(function (h) { head.appendChild(el("th", { scope: "col" }, h)); });
    var thead = el("thead"); thead.appendChild(head); t.appendChild(thead);
    var body = el("tbody");
    [["mean", "Mean profit Π (USD)"], ["median", "Median profit Π (USD)"], ["p_loss", "Probability of a loss"], ["cvar05", "CVaR 5 %: mean loss in the worst 5 % (USD)"]].forEach(function (m) {
      var r = row(state.set, label, state.scenario, m[0]);
      if (!r) return;
      var tr = el("tr");
      tr.appendChild(el("th", { scope: "row" }, m[1]));
      tr.appendChild(cell(r, m[0]));
      tr.appendChild(el("td", null, fmt(m[0], r.b)));
      tr.appendChild(el("td", null, pct(r.share_a_better)));
      var v = el("td"); v.appendChild(badge(r.verdict)); tr.appendChild(v);
      body.appendChild(tr);
    });
    t.appendChild(body);
    drawE1();
  }
  function drawE1() {
    var budgets = D.budgets, W = Math.max(320, $("e1-chart").clientWidth || 900), H = W < 560 ? 260 : 300, L = 60, R = 12, T = 14, B = 42;
    var data = budgets.map(function (n) { return { n: n, a: row(state.set, "n=" + n, state.scenario, "mean"), b: row(state.set, "n=" + n, state.scenario, "mean").b }; });
    var vals = []; data.forEach(function (d) { vals.push(d.a.a_low, d.a.a_high, d.b, 0); });
    var ymin = Math.min.apply(null, vals), ymax = Math.max.apply(null, vals);
    var pad = (ymax - ymin) * 0.08 || 1; ymin -= pad; ymax += pad;
    var band = (W - L - R) / budgets.length;
    var xs = function (i, off) { return L + band * (i + 0.5) + off; };
    var ys = function (y) { return T + (ymax - y) / (ymax - ymin) * (H - T - B); };
    var s = svg("svg", { viewBox: "0 0 " + W + " " + H, role: "img", "aria-label": "Mean net profit of opening and buying by budget" });
    var ticks = axisTicks(ymin, ymax, 5), dec = ticks.length > 1 && ticks[1] - ticks[0] < 1 ? 2 : 0;
    ticks.forEach(function (t) {
      s.appendChild(svg("line", { class: "gridline", x1: L, x2: W - R, y1: ys(t), y2: ys(t) }));
      s.appendChild(svg("text", { x: L - 8, y: ys(t) + 4, "text-anchor": "end" }, usd(t, dec)));
    });
    s.appendChild(svg("line", { class: "axis zero", x1: L, x2: W - R, y1: ys(0), y2: ys(0) }));
    data.forEach(function (d, i) {
      s.appendChild(svg("text", { x: xs(i, 0), y: H - B + 18, "text-anchor": "middle" }, W < 560 ? "n = " + d.n : d.n + (d.n === 1 ? " booster" : " boosters")));
      var xa = xs(i, -14), xb = xs(i, 14);
      s.appendChild(svg("line", { class: "whisker-a", x1: xa, x2: xa, y1: ys(d.a.a_low), y2: ys(d.a.a_high) }));
      var ca = svg("circle", { class: "dot-a ring", cx: xa, cy: ys(d.a.a_mean), r: 6 });
      var cb = svg("circle", { class: "dot-b ring", cx: xb, cy: ys(d.b), r: 6 });
      [[ca, "A: open " + d.n, d.a.a_mean, "[" + usd(d.a.a_low) + ", " + usd(d.a.a_high) + "]"], [cb, "B: buy, same budget", d.b, "fixed once prices are known"]].forEach(function (o) {
        var hit = svg("circle", { cx: o[0].getAttribute("cx"), cy: o[0].getAttribute("cy"), r: 16, fill: "transparent" });
        hit.addEventListener("mousemove", function (ev) { showTip(ev, esc(o[1]) + "<br><b>Mean Π " + usd(o[2]) + " USD</b><br>" + esc(o[3])); });
        hit.addEventListener("mouseleave", hideTip);
        s.appendChild(o[0]); s.appendChild(hit);
      });
    });
    s.appendChild(svg("text", { x: L, y: H - 4 }, "Budget (USD = boosters × booster price)"));
    var box = $("e1-chart"); box.innerHTML = ""; box.appendChild(s);
    $("e1-caption").textContent = "Mean net profit by budget · " + setName(state.set) + " · " + (LABEL[state.scenario] || state.scenario);
    var lg = $("e1-legend"); lg.innerHTML = "";
    var a = el("span"); a.appendChild(el("i", { class: "dot sw-a" })); a.appendChild(document.createTextNode("A: open boosters (95 % interval)")); lg.appendChild(a);
    var b = el("span"); b.appendChild(el("i", { class: "dot sw-b" })); b.appendChild(document.createTextNode("B: buy single cards")); lg.appendChild(b);
    $("e1-source").textContent = "Π in USD, " + M.price_type + " on " + M.price_date + ". Mean over " + M.epistemic_draws + " pull-rate draws, " + M.aleatory_runs.toLocaleString("en-US") + " simulated runs each.";
  }

  // ---------- step 5: E2 ----------
  function renderE2() {
    var t = $("e2-table"); t.innerHTML = "";
    t.appendChild(el("caption", { class: "hint" }, setName(state.set) + " · " + (LABEL[state.scenario] || state.scenario)));
    var head = el("tr");
    ["Target", "Boosters per hit", "Cap n_max", "P(opening cheaper)", "Mean Π (USD)", "Median Π (USD)", "CVaR 5 % (USD)", "Verdict (mean)"].forEach(function (h) { head.appendChild(el("th", { scope: "col" }, h)); });
    var thead = el("thead"); thead.appendChild(head); t.appendChild(thead);
    var body = el("tbody");
    D.e2.filter(function (e) { return e.set === state.set; }).forEach(function (e) {
      var tr = el("tr");
      var name = e.label === "top_price" ? "Most expensive card (" + e.rarity + ")" : "Most expensive Special Illustration Rare";
      tr.appendChild(el("th", { scope: "row" }, name));
      var pp = el("td"); pp.appendChild(document.createTextNode("1 in " + Math.round(e.packs_per_hit.mean).toLocaleString("en-US")));
      pp.appendChild(el("br")); pp.appendChild(el("span", { class: "ci" }, "[" + Math.round(e.packs_per_hit.low).toLocaleString("en-US") + ", " + Math.round(e.packs_per_hit.high).toLocaleString("en-US") + "]"));
      tr.appendChild(pp);
      tr.appendChild(el("td", null, e.n_max.toLocaleString("en-US")));
      ["p_gain", "mean", "median", "cvar05"].forEach(function (m) { tr.appendChild(cell(row(state.set, e.label, state.scenario, m), m)); });
      var v = el("td"); v.appendChild(badge(row(state.set, e.label, state.scenario, "mean").verdict)); tr.appendChild(v);
      body.appendChild(tr);
    });
    t.appendChild(body);
  }

  // ---------- step 6: hypotheses & export ----------
  var HYP = {
    H1: "Mean and risk can rank the strategies differently.",
    H2: "Pull-rate uncertainty can change a verdict.",
    H3: "Fees and liquidity costs reduce the advantage of opening.",
    H4: "The winner differs between sets or price dates."
  };
  function renderHyp() {
    var box = $("hyp"); box.innerHTML = "";
    Object.keys(D.hypotheses).sort().forEach(function (h) {
      var d = el("div", { class: "hyp" });
      var p = el("p"); p.appendChild(el("span", { class: "st" }, h + ": " + D.hypotheses[h].status + ". "));
      p.appendChild(document.createTextNode(HYP[h] || ""));
      d.appendChild(p);
      var ev = el("details", { class: "hint" });
      ev.appendChild(el("summary", null, "Evidence (" + D.hypotheses[h].evidence.length + ")"));
      var ul = el("ul");
      D.hypotheses[h].evidence.forEach(function (x) { ul.appendChild(el("li", null, x)); });
      ev.appendChild(ul);
      d.appendChild(ev);
      box.appendChild(d);
    });
  }
  $("dl-csv").addEventListener("click", function () {
    var cols = ["set", "estimand", "label", "scenario", "metric", "a_mean", "a_low", "a_high", "a_mc_se", "b", "share_a_better", "verdict"];
    var lines = [cols.join(",")].concat(D.rows.map(function (r) { return cols.map(function (c) { return r[c]; }).join(","); }));
    var url = URL.createObjectURL(new Blob([lines.join("\n") + "\n"], { type: "text/csv" }));
    var a = el("a", { href: url, download: "pokequant-" + M.run_id + "-comparisons.csv" });
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  });

  ["in-booster", "in-fee", "in-haircut", "in-fixed"].forEach(function (id) { $(id).addEventListener("input", renderCalc); });

  function render() {
    renderPickers();
    renderTiles();
    renderCalc();
    renderE1();
    renderE2();
  }
  resetCalc();
  renderHyp();
  render();
  var resizeTimer = null;
  window.addEventListener("resize", function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () { renderCalc(); drawE1(); }, 150);
  });
})();
