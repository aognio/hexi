(function () {
  var root = document.documentElement;
  var toggle = document.getElementById("theme-toggle");
  var menuToggle = document.getElementById("menu-toggle");
  var sidebar = document.getElementById("sidebar");

  function setTheme(next) {
    root.setAttribute("data-theme", next);
    localStorage.setItem("hexi-docs-theme", next);
  }

  if (toggle) {
    toggle.addEventListener("click", function () {
      var current = root.getAttribute("data-theme") || "light";
      setTheme(current === "light" ? "dark" : "light");
    });
  }

  if (menuToggle && sidebar) {
    menuToggle.addEventListener("click", function () {
      var isOpen = sidebar.classList.toggle("open");
      menuToggle.setAttribute("aria-expanded", String(isOpen));
    });
  }

  document.querySelectorAll("pre > code").forEach(function (code) {
    var pre = code.parentElement;
    if (!pre || pre.parentElement && pre.parentElement.classList.contains("code-wrap")) {
      return;
    }

    var wrap = document.createElement("div");
    wrap.className = "code-wrap";
    pre.parentNode.insertBefore(wrap, pre);
    wrap.appendChild(pre);

    var button = document.createElement("button");
    button.className = "copy-button";
    button.type = "button";
    button.textContent = "Copy";
    button.addEventListener("click", function () {
      navigator.clipboard.writeText(code.innerText).then(function () {
        button.textContent = "Copied";
        window.setTimeout(function () {
          button.textContent = "Copy";
        }, 1200);
      });
    });
    wrap.appendChild(button);
  });

  var searchInput = document.getElementById("search-input");
  document.addEventListener("keydown", function (event) {
    if (event.key === "/" && searchInput && document.activeElement !== searchInput) {
      event.preventDefault();
      searchInput.focus();
    }
  });
})();
