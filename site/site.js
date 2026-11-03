// Docs site: light/dark theme toggle and client-side search over search-index.json.
(function () {
  var root = document.documentElement;

  // ─── theme ────────────────────────────────────────────────────────────
  var toggle = document.getElementById("theme-toggle");
  var prefersDark = window.matchMedia("(prefers-color-scheme: dark)");

  function currentTheme() {
    return root.dataset.theme || (prefersDark.matches ? "dark" : "light");
  }

  function syncToggle() {
    var dark = currentTheme() === "dark";
    toggle.textContent = dark ? "☀" : "☾";
    toggle.setAttribute("aria-label", dark ? "Switch to light theme" : "Switch to dark theme");
    toggle.setAttribute("aria-pressed", String(dark));
  }

  if (toggle) {
    syncToggle();
    prefersDark.addEventListener("change", syncToggle);
    toggle.addEventListener("click", function () {
      var next = currentTheme() === "dark" ? "light" : "dark";
      root.dataset.theme = next;
      try {
        localStorage.setItem("theme", next);
      } catch (e) {}
      syncToggle();
    });
  }

  // ─── search ───────────────────────────────────────────────────────────
  var input = document.getElementById("site-search");
  var results = document.getElementById("search-results");
  if (!input || !results) return;

  var index = null;
  var loading = null;

  function loadIndex() {
    if (index) return Promise.resolve(index);
    if (!loading) {
      loading = fetch("search-index.json")
        .then(function (r) { return r.json(); })
        .then(function (data) { index = data; return data; })
        .catch(function () { loading = null; return []; });
    }
    return loading;
  }

  function snippet(text, term) {
    var i = text.toLowerCase().indexOf(term);
    if (i < 0) return text.slice(0, 120);
    var start = Math.max(0, i - 50);
    return (start > 0 ? "…" : "") + text.slice(start, i + 90) + "…";
  }

  function search(query) {
    var terms = query.toLowerCase().split(/\s+/).filter(Boolean);
    return index
      .map(function (page) {
        var title = page.title.toLowerCase();
        var text = page.text.toLowerCase();
        var score = 0;
        for (var t = 0; t < terms.length; t++) {
          var inTitle = title.indexOf(terms[t]) >= 0;
          var hits = text.split(terms[t]).length - 1;
          if (!inTitle && !hits) return null;
          score += (inTitle ? 10 : 0) + hits;
        }
        return { page: page, score: score, snippet: snippet(page.text, terms[0]) };
      })
      .filter(Boolean)
      .sort(function (a, b) { return b.score - a.score; })
      .slice(0, 8);
  }

  function render(matches) {
    results.textContent = "";
    if (!matches.length) {
      var empty = document.createElement("li");
      empty.className = "search-empty";
      empty.textContent = "No results";
      results.appendChild(empty);
    }
    matches.forEach(function (m) {
      var li = document.createElement("li");
      var a = document.createElement("a");
      a.href = m.page.url;
      var strong = document.createElement("strong");
      strong.textContent = m.page.title;
      var span = document.createElement("span");
      span.textContent = m.snippet;
      a.appendChild(strong);
      a.appendChild(span);
      li.appendChild(a);
      results.appendChild(li);
    });
    results.hidden = false;
  }

  input.addEventListener("focus", loadIndex);
  input.addEventListener("input", function () {
    var query = input.value.trim();
    if (!query) {
      results.hidden = true;
      return;
    }
    loadIndex().then(function () {
      if (input.value.trim() === query) render(search(query));
    });
  });
  input.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      input.value = "";
      results.hidden = true;
    } else if (e.key === "Enter") {
      var first = results.querySelector("a");
      if (first) window.location.href = first.href;
    }
  });
  document.addEventListener("click", function (e) {
    if (!e.target.closest || !e.target.closest(".search")) results.hidden = true;
  });
})();
