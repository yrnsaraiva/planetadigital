(() => {
  const qs = (s, el = document) => el.querySelector(s);
  const qsa = (s, el = document) => [...el.querySelectorAll(s)];

  // Elements (teu markup)
  const overlay = qs("#cartOverlay");
  const drawer  = qs("#cartDrawer");
  const closeBtn = qs("#cartClose");
  const itemsEl = qs("#cartItems");
  const totalEl = qs("#cartTotal");
  const badgeEl = qs("[data-cart-count]");

  const reserveBtn = qs("#reserveBtn");
  const reserveModal = qs("#reserveModal");
  const reserveClose = qs("#reserveClose");
  const reserveForm = qs("#reserveForm");

  const urls = window.__SHOP_CART_URLS__ || {};

  // ---------- CSRF ----------
  function getCSRFToken() {
    return qs("[name=csrfmiddlewaretoken]")?.value || "";
  }

  function isAjax() {
    return true;
  }

  async function post(url, data = {}) {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCSRFToken(),
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams(data).toString(),
    });

    let payload = null;
    try { payload = await res.json(); } catch (_) {}

    if (!res.ok) {
      const msg = payload?.error || `Erro (${res.status})`;
      throw new Error(msg);
    }
    return payload;
  }

  async function getJSON(url) {
    const res = await fetch(url, {
      headers: { "X-Requested-With": "XMLHttpRequest" },
    });
    const payload = await res.json();
    if (!res.ok || payload?.ok === false) throw new Error(payload?.error || "Erro ao carregar carrinho.");
    return payload;
  }

  // ---------- UI: open/close drawer ----------
  function openDrawer() {
    if (!overlay || !drawer) return;

    overlay.classList.remove("hidden");
    drawer.style.transform = "translateX(0)";
    drawer.setAttribute("aria-hidden", "false");
  }

  function closeDrawer() {
    if (!overlay || !drawer) return;

    overlay.classList.add("hidden");
    drawer.style.transform = "translateX(100%)";
    drawer.setAttribute("aria-hidden", "true");
  }

  // ---------- UI: reserve modal ----------
  function openReserveModal() {
    if (!reserveModal) return;
    reserveModal.classList.remove("hidden");
    reserveModal.setAttribute("aria-hidden", "false");
  }

  function closeReserveModal() {
    if (!reserveModal) return;
    reserveModal.classList.add("hidden");
    reserveModal.setAttribute("aria-hidden", "true");
  }

  // ---------- Render ----------
  function moneyMZN(v) {
    const n = Number(v || 0);
    return `${n.toLocaleString("pt-PT")} MZN`;
  }

  function setBadge(count) {
    if (badgeEl) badgeEl.textContent = String(count ?? 0);
  }

  function renderCart(data) {
    if (!itemsEl || !totalEl) return;

    setBadge(data.count || 0);
    totalEl.textContent = moneyMZN(data.total);

    if (!data.items || data.items.length === 0) {
      itemsEl.innerHTML = `<div class="text-sm text-white/60">O carrinho está vazio.</div>`;
      return;
    }

    itemsEl.innerHTML = data.items.map((it) => {
      const img = it.image
        ? `<img src="${it.image}" class="h-16 w-16 rounded-xl object-cover border border-white/10" alt="">`
        : `<div class="h-16 w-16 rounded-xl border border-white/10 bg-black/40"></div>`;

      return `
        <div class="rounded-2xl border border-white/10 bg-black/30 p-4" data-cart-row data-item-id="${it.id}">
          <div class="flex gap-3">
            ${img}

            <div class="flex-1">
              <div class="font-display uppercase text-lg leading-[0.9]">${it.product}</div>
              <div class="mt-2 font-monoish text-xs text-white/60">Variante: ${it.size || "—"}</div>

              <!-- Qtd controls (opcional) -->
              <div class="mt-2 flex items-center gap-2">
                <button type="button" class="h-8 w-8 rounded-full border border-white/15 hover:border-white/30 transition glass"
                        data-qty-minus>-</button>
                <input class="w-14 text-center rounded-full bg-black/40 border border-white/15 px-3 py-1.5 text-sm text-white/90 outline-none focus:border-white/30"
                       value="${it.qty}" inputmode="numeric" data-qty-input />
                <button type="button" class="h-8 w-8 rounded-full border border-white/15 hover:border-white/30 transition glass"
                        data-qty-plus>+</button>

                <div class="ml-auto font-monoish text-xs text-white/60">${moneyMZN(it.line)}</div>
              </div>
            </div>

            <button type="button" class="text-[10px] kicker text-white/60 hover:text-white link-u" data-remove>
              remover
            </button>
          </div>
        </div>
      `;
    }).join("");

    wireRowActions();
  }

  async function refreshCart() {
    if (!urls.modalData) return;
    const data = await getJSON(urls.modalData);
    renderCart(data);
  }

  // ---------- Row actions ----------
  function urlWithId(pattern, id) {
    // pattern exemplo: "/cart/item/0/remove/"
    return String(pattern).replace("/0/", `/${id}/`);
  }

  function wireRowActions() {
    qsa("[data-item-id]").forEach((row) => {
      const itemId = row.getAttribute("data-item-id");
      const removeBtn = qs("[data-remove]", row);
      const minusBtn = qs("[data-qty-minus]", row);
      const plusBtn = qs("[data-qty-plus]", row);
      const qtyInput = qs("[data-qty-input]", row);

      if (removeBtn) {
        removeBtn.addEventListener("click", async () => {
          try {
            const url = urlWithId(urls.removeItem, itemId);
            await post(url);
            await refreshCart();
          } catch (err) {
            alert(err.message || "Erro ao remover item.");
          }
        });
      }

      // Qty update (opcional)
      async function commitQty(qty) {
        qty = Math.max(1, Math.min(20, qty));
        try {
          const url = urlWithId(urls.setQty, itemId);
          await post(url, { quantity: String(qty) });
          await refreshCart();
        } catch (err) {
          alert(err.message || "Erro ao atualizar quantidade.");
        }
      }

      if (minusBtn && qtyInput) {
        minusBtn.addEventListener("click", () => {
          const v = parseInt(qtyInput.value || "1", 10);
          commitQty(v - 1);
        });
      }

      if (plusBtn && qtyInput) {
        plusBtn.addEventListener("click", () => {
          const v = parseInt(qtyInput.value || "1", 10);
          commitQty(v + 1);
        });
      }

      if (qtyInput) {
        qtyInput.addEventListener("change", () => {
          const v = parseInt(qtyInput.value || "1", 10);
          commitQty(Number.isFinite(v) ? v : 1);
        });
      }
    });
  }

  // ---------- Open triggers ----------
  // Qualquer botão/link com data-open-cart abre o drawer
  function wireOpenCartTriggers() {
    qsa("[data-open-cart]").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        e.preventDefault();
        openDrawer();
        try { await refreshCart(); } catch (_) {}
      });
    });
  }

  // ---------- Close triggers ----------
  function wireCloseCartTriggers() {
    if (overlay) overlay.addEventListener("click", closeDrawer);
    if (closeBtn) closeBtn.addEventListener("click", closeDrawer);
  }

  // ---------- Reserve modal wiring ----------
  function wireReserveModal() {
    if (reserveBtn) reserveBtn.addEventListener("click", () => {
      // aqui tens duas opções:
      // A) abrir modal de reserva (teu fluxo atual)
      openReserveModal();
      // B) se preferires ir direto ao checkout:
      // window.location.href = urls.checkout;
    });

    if (reserveClose) reserveClose.addEventListener("click", closeReserveModal);

    if (reserveModal) {
      reserveModal.addEventListener("click", (e) => {
        // clicar fora do painel fecha
        const panel = qs("#reservePanel");
        if (panel && !panel.contains(e.target) && e.target === reserveModal) closeReserveModal();
      });
    }

    if (reserveForm) {
      reserveForm.addEventListener("submit", (e) => {
        // Neste ponto, como o checkout “real” já existe no Django,
        // recomendo que este submit leve ao checkout, ou faça POST numa view tua.
        // Por agora, só previne HTML5 issues e deixa seguir o teu fluxo/handler.
        // Se quiseres, eu adapto para criar Order + redirect ao success aqui.
        // e.preventDefault();
      });
    }
  }

  // ---------- Add-to-cart AJAX integration ----------
  // Se houver um form com id="addToCartForm", intercepta e abre o drawer após adicionar
  function wireAddToCartAjax() {
    const form = qs("#addToCartForm");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
      e.preventDefault();

      try {
        const res = await fetch(form.action, {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": form.querySelector("[name=csrfmiddlewaretoken]")?.value || getCSRFToken(),
            "Content-Type": "application/x-www-form-urlencoded",
          },
          body: new URLSearchParams(new FormData(form)).toString(),
        });

        const data = await res.json();
        if (!res.ok || data?.ok === false) {
          alert(data?.error || "Falha ao adicionar ao carrinho.");
          return;
        }

        // atualiza badge imediatamente (e depois refresh p/ itens)
        if (data.cart_count != null) setBadge(data.cart_count);

        openDrawer();
        await refreshCart();
      } catch (err) {
        alert(err.message || "Erro ao adicionar ao carrinho.");
      }
    });
  }

  // ---------- Expose manual trigger ----------
  window.__PLANETA_CART__ = {
    open: async () => {
      openDrawer();
      await refreshCart();
    },
    close: closeDrawer,
    refresh: refreshCart,
  };

  // Init
  wireOpenCartTriggers();
  wireCloseCartTriggers();
  wireReserveModal();
  wireAddToCartAjax();

  // (opcional) carregar badge/total em background no load:
  // refreshCart().catch(()=>{});
})();
