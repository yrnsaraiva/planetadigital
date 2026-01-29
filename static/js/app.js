/* -------------------------
   Helpers
------------------------- */
const qs = (s, el = document) => el.querySelector(s);
const qsa = (s, el = document) => [...el.querySelectorAll(s)];

export function getConfig() {
  const el = qs("#site-config");
  if (!el) return {};
  try { return JSON.parse(el.textContent || "{}"); }
  catch { return {}; }
}

export function money(n, cur) {
  if (typeof n !== "number") return "";
  const cfg = getConfig();
  const currency = cur || cfg.currency || "MZN";
  return `${n.toLocaleString("pt-PT")} ${currency}`;
}

export function setYear() {
  const y = qs("#year");
  if (y) y.textContent = new Date().getFullYear();
}

export function hydrateGlobals() {
  const cfg = getConfig();

  const brand = qs("[data-brand]");
  if (brand && cfg.brand) brand.textContent = cfg.brand;

  const tag = qs("[data-tagline]");
  if (tag && cfg.tagline) tag.textContent = cfg.tagline;

  // pickup em inputs readonly
  qsa('[data-pickup]').forEach(el => {
    if (cfg.pickup) el.textContent = cfg.pickup;
  });
}

/* -------------------------
   Reveal on scroll
------------------------- */
export function initReveal() {
  const els = qsa(".reveal:not(.wired)");
  if (!els.length) return;

  const obs = new IntersectionObserver((entries) => {
    for (const e of entries) if (e.isIntersecting) e.target.classList.add("is-in");
  }, { threshold: 0.12 });

  els.forEach(el => {
    el.classList.add("wired");
    obs.observe(el);
  });
}

/* -------------------------
   Typing loop: PLANETA
   (aplica em #type-planeta)
------------------------- */
export function initTypingPlaneta() {
    const el = document.getElementById("type-planeta");
    if (!el) return;

    const text = "PLANETA";
    const typeSpeed = 120;   // escrever
    const eraseSpeed = 80;   // apagar
    const holdAfterType = 2700;
    const holdAfterErase = 600;

    let i = 0;
    let isTyping = true;

    el.classList.add("typing-caret");
    el.textContent = "";

    function loop() {
        if (isTyping) {
            if (i < text.length) {
                el.textContent += text.charAt(i);
                i++;
                setTimeout(loop, typeSpeed);
            } else {
                // terminou de escrever
                setTimeout(() => {
                    isTyping = false;
                    loop();
                }, holdAfterType);
            }
        } else {
            if (i > 3) {
                el.textContent = text.substring(0, i - 1);
                i--;
                setTimeout(loop, eraseSpeed);
            } else {
                // terminou de apagar
                setTimeout(() => {
                    isTyping = true;
                    loop();
                }, holdAfterErase);
            }
        }
    }

    // delay inicial para impacto
    setTimeout(loop, 500);
}

/* -------------------------
   Product gallery thumbs
   Markup esperado:
   - img principal: #mainImg
   - botões thumbs: [data-thumb="..."]
------------------------- */
export function initProductThumbs() {
  const main = qs("#mainImg");
  const thumbs = qsa("[data-thumb]");
  if (!main || !thumbs.length) return;

  thumbs.forEach(btn => {
    btn.addEventListener("click", () => {
      const src = btn.getAttribute("data-thumb");
      if (src) main.src = src;

      thumbs.forEach(b => b.classList.remove("ring-2", "ring-white/20"));
      btn.classList.add("ring-2", "ring-white/20");
    });
  });
}

export function initNewsletterPopup() {
    const KEY = "planeta_newsletter_state_v1";

    const overlay = document.getElementById("nlOverlay");
    const modal = document.getElementById("nlModal");
    const closeBtn = document.getElementById("nlClose");
    const laterBtn = document.getElementById("nlLater");
    const form = document.getElementById("nlForm");
    const email = document.getElementById("nlEmail");

    if (!overlay || !modal || !closeBtn || !form || !email) {
        console.warn("[PLANETA] Newsletter markup incomplete on this page.");
        return;
    }

    const open = () => {
        overlay.classList.remove("hidden");
        modal.classList.remove("hidden");
        document.body.style.overflow = "hidden";
        setTimeout(() => email.focus(), 50);
    };

    const close = (dismiss = true) => {
        overlay.classList.add("hidden");
        modal.classList.add("hidden");
        document.body.style.overflow = "";

        if (dismiss) {
            let st = {};
            try {
                st = JSON.parse(localStorage.getItem(KEY) || "{}");
            } catch {
            }
            localStorage.setItem(KEY, JSON.stringify({...st, dismissedAt: Date.now()}));
        }
    };

    // expõe manual trigger
    window.__PLANETA_NEWSLETTER__ = {
        open: (force = false) => open(force),
        close: () => close(true),
        reset: () => localStorage.removeItem(KEY),
    };

    // FECHAR: X + overlay + ESC + (opcional) Agora não
    closeBtn.addEventListener("click", () => close(true));
    overlay.addEventListener("click", () => close(true));
    window.addEventListener("keydown", (e) => {
        if (e.key === "Escape") close(true);
    });
    if (laterBtn) laterBtn.addEventListener("click", () => close(true));

    // SUBMIT (placeholder)
    form.addEventListener("submit", (e) => {
        e.preventDefault();
        const val = email.value.trim();
        if (!val) return;

        localStorage.setItem(KEY, JSON.stringify({subscribed: true, subscribedAt: Date.now(), email: val}));
        close(false);
        alert("Inscrição feita. Bem-vindo ao PLANETA.");
    });

    // triggers automáticos (mantém os teus se já tinhas)
    // Exemplo simples (tempo):
    setTimeout(() => open(), 9000);
}

export function wireFooterNewsletterToPopup() {
    const form = document.getElementById("footerNlForm");
    const input = document.getElementById("footerNlEmail");
    if (!form || !input) return;

    form.addEventListener("submit", (e) => {
        e.preventDefault();

        // abre o popup manualmente
        window.__PLANETA_NEWSLETTER__?.open(true);

        // preenche email no modal
        const modalEmail = document.getElementById("nlEmail");
        if (modalEmail) modalEmail.value = input.value.trim();
    });
}
