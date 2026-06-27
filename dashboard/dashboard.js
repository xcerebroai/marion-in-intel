/* Marion County IN Distress Intelligence — operator lead board logic.
   Client-side only. Fetches dashboard/data/dashboard.json.
   Ported from El Paso County dashboard (app.js v5). */
(function () {
  "use strict";

  // ── helpers ──
  function $(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function money(v) {
    var n = Number(v);
    return (v == null || v === "" || isNaN(n)) ? "—"
      : "$" + n.toLocaleString("en-US");
  }
  function parseDate(s) {
    if (!s) return null;
    var m = String(s).trim().match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (m) return new Date(+m[1], +m[2] - 1, +m[3]);
    var d = new Date(s);
    return isNaN(d.getTime()) ? null : d;
  }
  var TODAY = (function () {
    var d = new Date(); d.setHours(0, 0, 0, 0); return d;
  })();
  function daysAgo(d) {
    if (!d) return null;
    return Math.round((TODAY - d) / 86400000);
  }

  // ── state ──
  var records = [];
  var state = {
    search: "", filedWindow: "any", valMin: null, valMax: null,
    patterns: {}, owners: {},
    togNew: false, togAbsentee: false, togEnriched: false, togReview: false,
    sort: "urgency", preset: "all"
  };
  var PAGE = 60;
  var marked = loadMarked();
  var skipped = {};
  var filtered = [];
  var io = null;
  var sentinel = null;
  var shown = 0;

  function loadMarked() {
    try {
      var arr = JSON.parse(localStorage.getItem("marion_in_marked_v1") || "[]");
      var s = {}; arr.forEach(function (x) { s[x] = true; }); return s;
    } catch (e) { return {}; }
  }
  function saveMarked() {
    try { localStorage.setItem("marion_in_marked_v1", JSON.stringify(Object.keys(marked))); }
    catch (e) {}
  }

  // ── pattern config ──
  var PATTERN_META = {
    foreclosure: { label: "Foreclosure",                cls: "fcl" },
    estate:      { label: "Estate / Probate",           cls: "estate" },
    tax:         { label: "Tax Delinquent",             cls: "tax" },
    lien:        { label: "Lien",                       cls: "lien" },
    transfer:    { label: "Transfer / Ownership Change",cls: "xfer" },
    bankruptcy:  { label: "Bankruptcy",                 cls: "bk" }
  };

  // ── prep ──
  function prep(r) {
    var pats = r.display_patterns || [];
    r._isFcl     = pats.indexOf("foreclosure") >= 0;
    r._isEstate  = pats.indexOf("estate")      >= 0;
    r._isTax     = pats.indexOf("tax")         >= 0;
    r._isBk      = pats.indexOf("bankruptcy")  >= 0;
    r._isLien    = pats.indexOf("lien")        >= 0;
    r._isXfer    = pats.indexOf("transfer")    >= 0;
    r._isNew     = r.is_new === true;
    r._review    = r.display_lead_status === "REVIEW_REQUIRED";
    r._assessed  = Number(r.display_assessed_value) || 0;
    r._isAbsentee = (r.display_attributes || []).indexOf("absentee") >= 0;
    r._isEnriched = r.enrichment_status === "ENRICHED";
    r._filed     = parseDate(r.primary_event_date);
    r._tier      = urgencyTier(r);
    var mail     = [r.mailing_address, r.mailing_city, r.mailing_state, r.mailing_zip]
                     .filter(Boolean).join(", ");
    r._mailingFull = mail || null;
    r._blob = [
      r.display_owner, r.display_address, r._mailingFull,
      r.primary_parcel_id, pats.join(" "),
      (r.primary_source_urls || []).join(" ")
    ].filter(Boolean).join(" ").toLowerCase();
  }

  function urgencyTier(r) {
    if (r._review) return 99;
    if (r._isFcl)    return 1;
    if (r._isEstate) return 2;
    if (r._isTax)    return 3;
    if (r._isBk)     return 4;
    return 5;
  }

  // ── boot ──
  function boot(payload) {
    records = (payload.records || []);
    records.forEach(prep);

    $("topStats").innerHTML = topStatsHtml(payload);

    var bl = payload.build_label;
    if (bl && bl !== "FULL_BUILD") {
      var b = $("banner");
      b.hidden = false;
      b.textContent = "PARTIAL LEAD BOARD (" + bl + ") — " + (payload.build_label_reason || "");
    }

    buildPresets();
    buildPatternFilter();
    buildOwnerFilter();
    wireControls();
    setupObserver();
    render();
    document.documentElement.setAttribute("data-ready", "1");
  }

  function topStatsHtml(p) {
    var fcl     = records.filter(function (r) { return r._isFcl; }).length;
    var estate  = records.filter(function (r) { return r._isEstate; }).length;
    var newToday = p.new_lead_count || 0;
    function st(n, l, cls) {
      return '<div class="topstat ' + (cls||"") + '"><div class="n">' + n +
        '</div><div class="l">' + l + "</div></div>";
    }
    return st(records.length.toLocaleString(), "total leads") +
      st(newToday, "new today", "newtoday") +
      st(fcl, "foreclosures", "urgent") +
      st(estate, "estate leads", "estate");
  }

  // ── presets ──
  var PRESETS = [
    { id: "fcl",       label: "Foreclosures" },
    { id: "estate",    label: "Estate / Probate leads" },
    { id: "tax",       label: "Tax delinquent" },
    { id: "bk",        label: "Bankruptcy filings" },
    { id: "absentee",  label: "Absentee owners" },
    { id: "newtoday",  label: "New today" },
    { id: "all",       label: "Show all" }
  ];
  function buildPresets() {
    var box = $("presets");
    box.innerHTML = "";
    PRESETS.forEach(function (p) {
      var b = document.createElement("button");
      b.className = "preset"; b.textContent = p.label; b.dataset.id = p.id;
      b.addEventListener("click", function () { applyPreset(p.id); });
      box.appendChild(b);
    });
  }
  function markPresetActive(id) {
    state.preset = id;
    Array.prototype.forEach.call($("presets").children, function (b) {
      b.classList.toggle("active", b.dataset.id === id);
    });
  }

  function buildPatternFilter() {
    var counts = {};
    records.forEach(function (r) {
      (r.display_patterns || []).forEach(function (p) {
        counts[p] = (counts[p] || 0) + 1;
      });
    });
    var box = $("patternFilter"); box.innerHTML = "";
    Object.keys(counts).sort(function (a, b) { return counts[b] - counts[a]; })
      .forEach(function (t) {
        state.patterns[t] = true;
        var meta = PATTERN_META[t] || { label: t };
        var l = document.createElement("label");
        l.className = "chk";
        l.innerHTML = '<input type="checkbox" checked data-pat="' + esc(t) + '"> ' +
          esc(meta.label) + '<span class="cnt">' + counts[t] + "</span>";
        l.querySelector("input").addEventListener("change", function (e) {
          state.patterns[t] = e.target.checked; markPresetActive(""); render();
        });
        box.appendChild(l);
      });
  }

  function buildOwnerFilter() {
    var counts = {};
    records.forEach(function (r) {
      var o = r.owner_type || "UNKNOWN";
      counts[o] = (counts[o] || 0) + 1;
    });
    var box = $("ownerFilter"); box.innerHTML = "";
    Object.keys(counts).sort().forEach(function (o) {
      state.owners[o] = true;
      var l = document.createElement("label");
      l.className = "chk";
      l.innerHTML = '<input type="checkbox" checked data-own="' + esc(o) + '"> ' +
        esc(o) + '<span class="cnt">' + counts[o] + "</span>";
      l.querySelector("input").addEventListener("change", function (e) {
        state.owners[o] = e.target.checked; markPresetActive(""); render();
      });
      box.appendChild(l);
    });
  }

  function wireControls() {
    var deb;
    $("search").addEventListener("input", function (e) {
      clearTimeout(deb);
      deb = setTimeout(function () {
        state.search = e.target.value.trim().toLowerCase(); render();
      }, 250);
    });
    $("filedWindow").addEventListener("change", function (e) {
      state.filedWindow = e.target.value; markPresetActive(""); render();
    });
    $("valMin").addEventListener("input", function (e) {
      state.valMin = e.target.value === "" ? null : Number(e.target.value);
      markPresetActive(""); render();
    });
    $("valMax").addEventListener("input", function (e) {
      state.valMax = e.target.value === "" ? null : Number(e.target.value);
      markPresetActive(""); render();
    });
    $("togNew").addEventListener("change",      function (e) { state.togNew      = e.target.checked; markPresetActive(""); render(); });
    $("togAbsentee").addEventListener("change", function (e) { state.togAbsentee = e.target.checked; markPresetActive(""); render(); });
    $("togEnriched").addEventListener("change", function (e) { state.togEnriched = e.target.checked; markPresetActive(""); render(); });
    $("togReview").addEventListener("change",   function (e) { state.togReview   = e.target.checked; markPresetActive(""); render(); });
    $("sortMode").addEventListener("change",    function (e) { state.sort = e.target.value; render(); });
    $("resetBtn").addEventListener("click",     function ()  { applyPreset("all"); });
    $("exportFiltered").addEventListener("click", function () { exportCsv(filtered, "marion_in_filtered.csv"); });
    $("exportMarked").addEventListener("click",   function () {
      var rows = records.filter(function (r) { return marked[r.lead_id]; });
      if (!rows.length) { alert("No leads marked yet."); return; }
      exportCsv(rows, "marion_in_marked.csv");
    });
  }

  function applyPreset(id) {
    // reset all
    state.search = ""; $("search").value = "";
    state.filedWindow = "any"; $("filedWindow").value = "any";
    state.valMin = null; state.valMax = null;
    $("valMin").value = ""; $("valMax").value = "";
    state.togNew = false;      $("togNew").checked = false;
    state.togAbsentee = false; $("togAbsentee").checked = false;
    state.togEnriched = false; $("togEnriched").checked = false;
    state.togReview = false;   $("togReview").checked = false;
    setAllChecks("patternFilter", "pat", state.patterns, true);
    setAllChecks("ownerFilter",   "own", state.owners,   true);

    if      (id === "fcl")      { onlyChecks("patternFilter", "pat", state.patterns, ["foreclosure"]); }
    else if (id === "estate")   { onlyChecks("patternFilter", "pat", state.patterns, ["estate"]); }
    else if (id === "tax")      { onlyChecks("patternFilter", "pat", state.patterns, ["tax"]); }
    else if (id === "bk")       { onlyChecks("patternFilter", "pat", state.patterns, ["bankruptcy"]); }
    else if (id === "absentee") { state.togAbsentee = true; $("togAbsentee").checked = true; }
    else if (id === "newtoday") { state.togNew = true; $("togNew").checked = true; }

    markPresetActive(id);
    render();
  }

  function setAllChecks(boxId, attr, store, on) {
    $(boxId).querySelectorAll("input[type=checkbox]").forEach(function (c) {
      c.checked = on; store[c.dataset[attr]] = on;
    });
  }
  function onlyChecks(boxId, attr, store, keep) {
    $(boxId).querySelectorAll("input[type=checkbox]").forEach(function (c) {
      var on = keep.indexOf(c.dataset[attr]) >= 0;
      c.checked = on; store[c.dataset[attr]] = on;
    });
  }

  // ── filtering + sorting ──
  function applyFilters() {
    var allPat = Object.keys(state.patterns).every(function (k) { return state.patterns[k]; });
    var allOwn = Object.keys(state.owners).every(function (k) { return state.owners[k]; });
    var winDays = state.filedWindow === "any" ? null : Number(state.filedWindow);

    return records.filter(function (r) {
      if (skipped[r.lead_id]) return false;
      if (state.togReview   && !r._review)    return false;
      if (state.togNew      && !r._isNew)     return false;
      if (state.togAbsentee && !r._isAbsentee)return false;
      if (state.togEnriched && !r._isEnriched)return false;
      if (!allPat) {
        var hit = (r.display_patterns || []).some(function (p) { return state.patterns[p]; });
        if (!hit) return false;
      }
      if (!allOwn && !state.owners[r.owner_type || "UNKNOWN"]) return false;
      if (winDays != null) {
        var ago = daysAgo(r._filed);
        if (ago === null || ago < 0 || ago > winDays) return false;
      }
      if (state.valMin != null && r._assessed < state.valMin) return false;
      if (state.valMax != null && state.valMax > 0 && r._assessed > state.valMax) return false;
      if (state.search && r._blob.indexOf(state.search) < 0) return false;
      return true;
    });
  }

  function sortRows(rows) {
    var by = state.sort;
    return rows.slice().sort(function (a, b) {
      if (by === "recent") {
        var af = a._filed ? a._filed.getTime() : 0;
        var bf = b._filed ? b._filed.getTime() : 0;
        return bf - af;
      }
      if (by === "value") return b._assessed - a._assessed;
      if (by === "signals") return (b.stack_depth || 0) - (a.stack_depth || 0);
      // urgency default
      if (a._tier !== b._tier) return a._tier - b._tier;
      if ((b.stack_depth || 0) !== (a.stack_depth || 0))
        return (b.stack_depth || 0) - (a.stack_depth || 0);
      return b._assessed - a._assessed;
    });
  }

  // ── render ──
  function setupObserver() {
    sentinel = document.createElement("div");
    sentinel.className = "sentinel";
    io = new IntersectionObserver(function (entries) {
      if (entries[0].isIntersecting) renderMore();
    }, { root: $("leadList"), rootMargin: "400px" });
  }

  function render() {
    filtered = sortRows(applyFilters());
    shown = 0;
    var list = $("leadList");
    io.unobserve(sentinel);
    list.innerHTML = "";
    $("rowCount").textContent = filtered.length.toLocaleString() + " of " +
      records.length.toLocaleString() + " leads";
    $("markedCount").textContent = Object.keys(marked).length;
    updateFilterSummary();
    var empty = $("emptyMsg");
    if (!filtered.length) {
      empty.hidden = false;
      empty.innerHTML = "<b>No leads match the current filters.</b>Try clearing a filter or click Show all.";
      return;
    }
    empty.hidden = true;
    renderMore();
  }

  function renderMore() {
    var list = $("leadList");
    var end = Math.min(shown + PAGE, filtered.length);
    var frag = document.createDocumentFragment();
    for (var i = shown; i < end; i++) frag.appendChild(makeCard(filtered[i]));
    list.appendChild(frag);
    list.appendChild(sentinel);
    shown = end;
    if (shown < filtered.length) io.observe(sentinel);
    else io.unobserve(sentinel);
  }

  function chipsHtml(r) {
    return (r.display_patterns || []).map(function (p) {
      var meta = PATTERN_META[p] || { label: p, cls: "" };
      return '<span class="chip ' + meta.cls + '">' + esc(meta.label) + "</span>";
    }).join("");
  }

  function makeCard(r) {
    var el = document.createElement("div");
    var tierCls = r._review ? "review" : ("u-" + r._tier);
    el.className = "lead " + tierCls + (marked[r.lead_id] ? " marked" : "");
    el.dataset.id = r.lead_id;

    var addr = r.display_address
      ? '<div class="addr">' + esc(r.display_address) + "</div>"
      : '<div class="addr none">No property address on file</div>';

    var mail = (r._mailingFull && r._mailingFull !== r.display_address)
      ? '<div class="mail">Mailing: ' + esc(r._mailingFull) + "</div>"
      : "";

    var newPill = r._isNew ? '<span class="new-pill">NEW</span>' : "";
    var otype   = r.owner_type || "UNKNOWN";

    var av = r._assessed
      ? '<div class="assessed">' + money(r.display_assessed_value) +
        '<div class="ac">assessed</div></div>'
      : "";

    var badges = [];
    if (r._review)    badges.push('<span class="badge warn">REVIEW REQUIRED</span>');
    if (r._isAbsentee)badges.push('<span class="badge warn">Absentee</span>');
    if (r._isEnriched)badges.push('<span class="badge good">Enriched</span>');
    if ((r.stack_depth || 0) >= 2) badges.push('<span class="badge info">×' + r.stack_depth + ' signals</span>');

    el.innerHTML =
      '<div class="lead-main">' +
        '<div class="lead-id">' +
          '<div class="owner">' + esc(r.display_owner || "—") +
            '<span class="otype">' + esc(otype) + "</span>" +
            newPill +
          "</div>" +
          addr + mail +
          '<div class="chips">' + chipsHtml(r) + "</div>" +
        "</div>" +
        '<div class="lead-right">' + av +
          '<div class="badges">' + badges.join("") + "</div>" +
        "</div>" +
      "</div>" +
      '<div class="detail"></div>';

    el.addEventListener("click", function (ev) {
      if (ev.target.closest(".detail-actions")) return;
      toggleDetail(el, r);
    });
    return el;
  }

  // ── detail panel ──
  function toggleDetail(el, r) {
    if (el.classList.contains("open")) { el.classList.remove("open"); return; }
    var d = el.querySelector(".detail");
    if (!d.dataset.built) { d.innerHTML = detailHtml(r); d.dataset.built = "1"; wireDetail(el, d, r); }
    el.classList.add("open");
  }

  function detailHtml(r) {
    var rows = [];
    function add(k, v) { if (v != null && v !== "" && v !== "—") rows.push([k, v]); }
    add("Parcel ID",       esc(r.primary_parcel_id));
    add("Filed date",      esc(r.primary_event_date));
    add("First seen",      esc(r.first_seen_date));
    add("Patterns",        (r.display_patterns || []).join(", "));
    add("Deal paths",      (r.display_deal_paths || r.display_deal_path_details || [])
                             .map(function (d) { return typeof d === "string" ? d : d.path; }).join(", "));
    add("Attributes",      (r.display_attributes || []).join(", "));
    add("Enrichment",      r.enrichment_status);
    add("Property class",  esc(r.property_class));
    add("Year built",      esc(r.year_built));
    add("Assessed value",  money(r.display_assessed_value));
    add("Last sale price", money(r.display_last_sale_price));
    add("Last sale date",  esc(r.display_last_sale_date));
    add("Review flags",    (r.review_flags || []).join("; "));

    var grid = '<dl class="detail-grid">' +
      rows.map(function (kv) {
        return "<dt>" + kv[0] + "</dt><dd>" + kv[1] + "</dd>";
      }).join("") + "</dl>";

    var links = (r.primary_source_urls || []).map(function (u, i) {
      return '<a href="' + esc(u) + '" target="_blank" rel="noopener">Source record ' + (i + 1) + "</a>";
    }).join(" &nbsp;");
    if (links) grid += '<p style="margin:6px 0 8px">' + links + "</p>";

    var mk = marked[r.lead_id];
    return grid +
      '<div class="detail-actions">' +
        '<button class="btn act-mark">' + (mk ? "✓ Marked" : "Mark for review") + "</button>" +
        '<button class="btn act-skip">Skip (hide)</button>' +
        '<button class="btn act-export">Export this lead</button>' +
      "</div>";
  }

  function wireDetail(el, d, r) {
    var mb = d.querySelector(".act-mark");
    mb.onclick = function () {
      if (marked[r.lead_id]) delete marked[r.lead_id];
      else marked[r.lead_id] = true;
      saveMarked();
      el.classList.toggle("marked", !!marked[r.lead_id]);
      mb.textContent = marked[r.lead_id] ? "✓ Marked" : "Mark for review";
      $("markedCount").textContent = Object.keys(marked).length;
    };
    d.querySelector(".act-skip").onclick = function () {
      skipped[r.lead_id] = true; el.classList.remove("open"); render();
    };
    d.querySelector(".act-export").onclick = function () {
      exportCsv([r], "marion_lead_" + (r.lead_id || "row") + ".csv");
    };
  }

  // ── filter summary ──
  function updateFilterSummary() {
    var parts = [];
    var preset = PRESETS.filter(function (p) { return p.id === state.preset && p.id !== "all"; })[0];
    if (preset) parts.push("<b>" + esc(preset.label) + "</b>");
    if (state.search) parts.push('search "' + esc(state.search) + '"');
    if (state.filedWindow !== "any") parts.push("filed last " + state.filedWindow + " days");
    var patOff = Object.keys(state.patterns).filter(function (k) { return !state.patterns[k]; });
    if (patOff.length) {
      var on = Object.keys(state.patterns).filter(function (k) { return state.patterns[k]; });
      parts.push(on.map(function (p) { return (PATTERN_META[p] || {label:p}).label; }).join("/"));
    }
    if (state.valMin != null) parts.push("min " + money(state.valMin));
    if (state.valMax != null) parts.push("max " + money(state.valMax));
    if (state.togNew)      parts.push("new today");
    if (state.togAbsentee) parts.push("absentee");
    if (state.togEnriched) parts.push("enriched");
    if (state.togReview)   parts.push("review-required");
    $("filterSummary").innerHTML = parts.length
      ? "Showing: " + parts.join(" · ")
      : "Showing: <b>all leads</b> — sorted by urgency";
  }

  // ── CSV export ──
  var CSV_COLS = [
    "lead_id", "display_owner", "owner_type",
    "display_address", "mailing_address", "mailing_city", "mailing_state", "mailing_zip",
    "primary_parcel_id", "display_assessed_value", "display_last_sale_price",
    "display_last_sale_date", "property_class", "year_built",
    "enrichment_status", "display_lead_status", "primary_event_date",
    "first_seen_date", "is_new", "stack_depth"
  ];
  function exportCsv(rows, fname) {
    var head = CSV_COLS.concat(["display_patterns", "display_attributes", "display_deal_paths", "source_urls"]);
    var lines = [head.join(",")];
    rows.forEach(function (r) {
      var cells = CSV_COLS.map(function (c) { return q(r[c]); });
      cells.push(q((r.display_patterns || []).join("; ")));
      cells.push(q((r.display_attributes || []).join("; ")));
      cells.push(q((r.display_deal_paths || []).join("; ")));
      cells.push(q((r.primary_source_urls || []).join(" ")));
      lines.push(cells.join(","));
    });
    var blob = new Blob([lines.join("\n")], { type: "text/csv" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = fname;
    document.body.appendChild(a); a.click(); a.remove();
  }
  function q(v) {
    if (v == null) v = "";
    return '"' + String(v).replace(/"/g, '""') + '"';
  }

  // ── start ──
  function start() {
    var paths = ["./data/dashboard.json", "../data/dashboard.json"];
    var idx = 0;
    function tryNext() {
      if (idx >= paths.length) {
        $("banner").hidden = false;
        $("banner").textContent = "Could not load dashboard data. Is the data file present?";
        document.documentElement.setAttribute("data-ready", "1");
        return;
      }
      fetch(paths[idx++])
        .then(function (r) {
          if (!r.ok) throw new Error("HTTP " + r.status);
          return r.json();
        })
        .then(boot)
        .catch(tryNext);
    }
    tryNext();
  }

  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", start);
  else start();
})();
