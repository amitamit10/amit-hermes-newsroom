(() => {
  const body = document.body;
  const nav = document.querySelector("#primary-nav");
  const menuButton = document.querySelector(".menu-toggle");
  const closeMenu = () => {
    if (!nav || !menuButton) return;
    nav.classList.remove("is-open");
    menuButton.setAttribute("aria-expanded", "false");
    menuButton.setAttribute("aria-label", "Open navigation");
    nav.setAttribute("aria-hidden", window.matchMedia("(max-width: 760px)").matches ? "true" : "false");
  };

  if (nav && menuButton) {
    body.classList.add("has-menu-script");
    nav.setAttribute("aria-hidden", window.matchMedia("(max-width: 760px)").matches ? "true" : "false");
    menuButton.addEventListener("click", () => {
      const isOpen = menuButton.getAttribute("aria-expanded") === "true";
      nav.classList.toggle("is-open", !isOpen);
      menuButton.setAttribute("aria-expanded", String(!isOpen));
      menuButton.setAttribute("aria-label", isOpen ? "Open navigation" : "Close navigation");
      nav.setAttribute("aria-hidden", String(isOpen));
    });
    nav.querySelectorAll("a").forEach((link) => link.addEventListener("click", closeMenu));
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") closeMenu();
    });
    window.addEventListener("resize", () => {
      if (!window.matchMedia("(max-width: 760px)").matches) {
        nav.classList.remove("is-open");
        menuButton.setAttribute("aria-expanded", "false");
        menuButton.setAttribute("aria-label", "Open navigation");
        nav.setAttribute("aria-hidden", "false");
      } else if (menuButton.getAttribute("aria-expanded") !== "true") {
        nav.setAttribute("aria-hidden", "true");
      }
    }, { passive: true });
  }

  body.classList.add("interactive-ready");
  const readingProgress = document.querySelector("#reading-progress");
  const articleShell = document.querySelector(".article-shell");
  if (readingProgress && articleShell) {
    let progressFrame = 0;
    const updateProgress = () => {
      const start = articleShell.getBoundingClientRect().top + window.scrollY;
      const travel = Math.max(1, articleShell.scrollHeight - window.innerHeight);
      readingProgress.value = Math.min(100, Math.max(0, ((window.scrollY - start) / travel) * 100));
    };
    const queueProgress = () => {
      if (progressFrame) return;
      progressFrame = window.requestAnimationFrame(() => {
        progressFrame = 0;
        updateProgress();
      });
    };
    window.addEventListener("scroll", queueProgress, { passive: true });
    window.addEventListener("resize", queueProgress, { passive: true });
    updateProgress();
  }

  const tocLinks = Array.from(document.querySelectorAll(".article-toc a"));
  const tocSections = Array.from(document.querySelectorAll(".story-section[id]"));
  if (tocLinks.length && tocSections.length && "IntersectionObserver" in window) {
    const tocObserver = new IntersectionObserver((entries) => {
      const active = entries
        .filter((entry) => entry.isIntersecting)
        .sort((first, second) => Math.abs(first.boundingClientRect.top - 140) - Math.abs(second.boundingClientRect.top - 140))[0];
      if (!active) return;
      for (const link of tocLinks) {
        if (link.hash === `#${active.target.id}`) link.setAttribute("aria-current", "location");
        else link.removeAttribute("aria-current");
      }
    }, { rootMargin: "-12% 0px -72% 0px", threshold: 0 });
    tocSections.forEach((section) => tocObserver.observe(section));
  }
  tocLinks.forEach((link) => link.addEventListener("click", () => {
    if (window.matchMedia("(max-width: 760px)").matches) {
      const details = link.closest("details");
      if (details) details.open = false;
    }
  }));

  const sourceReferenceLinks = Array.from(document.querySelectorAll('.citation a[href^="#source-"]'));
  sourceReferenceLinks.forEach((link) => link.addEventListener("click", () => {
    const target = document.querySelector(link.hash);
    if (target) window.requestAnimationFrame(() => target.focus({ preventScroll: true }));
  }));

  document.querySelectorAll("[data-copy-link]").forEach((button) => {
    const feedback = document.getElementById(button.getAttribute("aria-describedby"));
    button.addEventListener("click", async () => {
      const pageUrl = window.location.href.split("#")[0];
      let fallbackField = button.parentElement.querySelector(".copy-link-fallback");
      if (feedback) feedback.textContent = "";
      try {
        if (navigator.clipboard?.writeText && window.isSecureContext) {
          await navigator.clipboard.writeText(pageUrl);
        } else {
          const field = document.createElement("textarea");
          field.value = pageUrl;
          field.setAttribute("readonly", "");
          field.style.position = "fixed";
          field.style.opacity = "0";
          document.body.append(field);
          field.select();
          const copied = document.execCommand("copy");
          field.remove();
          if (!copied) throw new Error("Clipboard unavailable");
        }
        fallbackField?.remove();
        if (feedback) feedback.textContent = "Story link copied.";
      } catch {
        if (!fallbackField) {
          fallbackField = document.createElement("input");
          fallbackField.className = "copy-link-fallback";
          fallbackField.type = "url";
          fallbackField.readOnly = true;
          fallbackField.setAttribute("aria-label", "Story link for manual copying");
          button.parentElement.append(fallbackField);
        }
        fallbackField.value = pageUrl;
        if (feedback) feedback.textContent = "Clipboard blocked. The link is selected below; press Ctrl+C to copy.";
        fallbackField.focus();
        fallbackField.select();
      }
    });
  });

  const visualDialog = document.querySelector("#visual-dialog");
  const visualDialogImage = visualDialog?.querySelector(".visual-dialog-image");
  const visualDialogCaption = visualDialog?.querySelector(".visual-dialog-caption");
  let visualDialogOpener = null;
  document.querySelectorAll(".visual-expand").forEach((button) => {
    button.addEventListener("click", () => {
      const figure = button.closest("figure");
      const image = figure?.querySelector(".visual-frame img");
      const caption = figure?.querySelector("figcaption");
      if (!visualDialog || !visualDialogImage || !image) return;
      visualDialogOpener = button;
      visualDialogImage.src = image.currentSrc || image.src;
      visualDialogImage.alt = image.alt;
      if (visualDialogCaption) {
        visualDialogCaption.replaceChildren(...Array.from(caption?.childNodes || [], (node) => node.cloneNode(true)));
      }
      visualDialog.showModal();
    });
  });
  visualDialog?.querySelector(".visual-dialog-close")?.addEventListener("click", () => visualDialog.close());
  visualDialog?.addEventListener("click", (event) => {
    if (event.target === visualDialog) visualDialog.close();
  });
  visualDialog?.addEventListener("close", () => {
    visualDialogImage?.removeAttribute("src");
    visualDialogCaption?.replaceChildren();
    const opener = visualDialogOpener;
    visualDialogOpener = null;
    if (opener?.isConnected) opener.focus();
  });

  const grid = document.querySelector("#archive-grid");
  const search = document.querySelector("#story-search");
  const status = document.querySelector("#results-status");
  const empty = document.querySelector("#empty-state");
  const resetButton = document.querySelector("#reset-filters");
  const categoryButtons = Array.from(document.querySelectorAll("[data-filter]"));
  const statusButtons = Array.from(document.querySelectorAll("[data-status-filter]"));
  if (!grid || !status || !empty) return;

  const cards = Array.from(grid.querySelectorAll(".story-card"));
  const params = new URLSearchParams(window.location.search);
  const validCategory = (value) => categoryButtons.some((button) => button.dataset.filter === value);
  const validStatus = (value) => statusButtons.some((button) => button.dataset.statusFilter === value);
  let activeCategory = validCategory(params.get("category")) ? params.get("category") : "all";
  let activeStatus = validStatus(params.get("status")) ? params.get("status") : "all";
  if (search) search.value = params.get("q") || "";

  const syncButtonGroup = (buttons, selectedValue, dataKey) => {
    buttons.forEach((button) => {
      const selected = button.dataset[dataKey] === selectedValue;
      button.classList.toggle("is-selected", selected);
      button.setAttribute("aria-pressed", String(selected));
    });
  };
  const syncArchiveUrl = () => {
    const url = new URL(window.location.href);
    const query = (search?.value || "").trim();
    if (query) url.searchParams.set("q", query);
    else url.searchParams.delete("q");
    if (activeCategory !== "all") url.searchParams.set("category", activeCategory);
    else url.searchParams.delete("category");
    if (activeStatus !== "all") url.searchParams.set("status", activeStatus);
    else url.searchParams.delete("status");
    window.history.replaceState(null, "", `${url.pathname}${url.search}${url.hash}`);
  };
  const updateArchive = () => {
    const query = (search?.value || "").trim().toLocaleLowerCase();
    let visible = 0;
    for (const card of cards) {
      const categoryMatches = activeCategory === "all" || card.dataset.category === activeCategory;
      const statusMatches = activeStatus === "all" || card.dataset.statusTone === activeStatus;
      const queryMatches = !query || (card.dataset.search || "").toLocaleLowerCase().includes(query);
      const show = categoryMatches && statusMatches && queryMatches;
      card.hidden = !show;
      if (show) visible += 1;
    }
    const filtered = Boolean(query) || activeCategory !== "all" || activeStatus !== "all";
    status.textContent = filtered
      ? `Showing ${visible} of ${cards.length} stories`
      : `Showing ${cards.length} stories`;
    empty.hidden = visible !== 0;
    if (resetButton) resetButton.hidden = !filtered;
    syncArchiveUrl();
  };

  categoryButtons.forEach((button) => {
    button.addEventListener("click", () => {
      activeCategory = button.dataset.filter || "all";
      syncButtonGroup(categoryButtons, activeCategory, "filter");
      updateArchive();
    });
  });
  statusButtons.forEach((button) => {
    button.addEventListener("click", () => {
      activeStatus = button.dataset.statusFilter || "all";
      syncButtonGroup(statusButtons, activeStatus, "statusFilter");
      updateArchive();
    });
  });
  search?.addEventListener("input", updateArchive);
  resetButton?.addEventListener("click", () => {
    activeCategory = "all";
    activeStatus = "all";
    if (search) search.value = "";
    syncButtonGroup(categoryButtons, activeCategory, "filter");
    syncButtonGroup(statusButtons, activeStatus, "statusFilter");
    updateArchive();
    search?.focus();
  });
  syncButtonGroup(categoryButtons, activeCategory, "filter");
  syncButtonGroup(statusButtons, activeStatus, "statusFilter");
  updateArchive();
})();
