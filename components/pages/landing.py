from fasthtml.common import *


def landing_page() -> FT:
    return Html(
        _head(),
        Body(
            _page_loader(),
            _bg(),
            Canvas(id="particles"),
            _top_banner(),
            _navbar(),
            _hero(),
            _marquee(),
            _stats(),
            _features_bento(),
            _how_it_works(),
            _social_proof(),
            _cta(),
            _footer(),
            _scripts(),
        ),
    )


# ─── Head ────────────────────────────────────────────────────────────────────

def _head() -> FT:
    return Head(
        Meta(charset="UTF-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1"),
        Meta(name="theme-color", content="#7c3aed"),
        Meta(name="description", content="Teluka protects every marketplace deal in the Philippines with escrow, evidence verification, and AI scam detection."),
        Meta(name="apple-mobile-web-app-capable", content="yes"),
        Meta(name="apple-mobile-web-app-status-bar-style", content="black-translucent"),
        Title("Teluka — Stop Getting Scammed on Facebook Marketplace"),
        Link(rel="manifest", href="/static/manifest.json"),
        Link(rel="apple-touch-icon", href="/static/icons/icon-192.png"),
        Link(rel="preconnect", href="https://fonts.googleapis.com"),
        Link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=""),
        Link(href="https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,400;0,14..32,500;0,14..32,600;0,14..32,700;0,14..32,800;0,14..32,900;1,14..32,400&display=swap", rel="stylesheet"),
        Link(rel="stylesheet", href="/static/css/app.css"),
        Link(rel="stylesheet", href="/static/css/landing.css"),
        # Anti-FOUC: apply saved theme before first paint
        Script("""(function(){var t=localStorage.getItem('teluka-theme')||(window.matchMedia('(prefers-color-scheme:light)').matches?'light':'dark');document.documentElement.setAttribute('data-theme',t);})();"""),
    )


# ─── Top 3D announcement banner ──────────────────────────────────────────────

def _top_banner() -> FT:
    ticks = (
        "🔒 Escrow-protected  ·  📸 EXIF live photo  ·  🤖 AI scam detection  ·  "
        "⚡ GCash & Maya  ·  🚚 Lalamove tracking  ·  🪪 KYC verified  ·  "
        "🇵🇭 Built for the Philippines  ·  "
    )
    return Div(cls="top-banner", id="top-banner")(
        # Layered 3D depth strips
        Div(cls="tb-depth")(
            Div(cls="tb-depth-layer tbl-back"),
            Div(cls="tb-depth-layer tbl-mid"),
            Div(cls="tb-depth-layer tbl-front"),
        ),
        # Glowing border line at the bottom
        Div(cls="tb-edge"),
        # Content row
        Div(cls="tb-content")(
            Div(cls="tb-badge")(
                Div(cls="tb-badge-glow"),
                Span("🇵🇭"),
                Span("TELUKA IS LIVE", cls="tb-badge-text"),
            ),
            Div(cls="tb-divider"),
            Div(cls="tb-ticker")(
                Div(cls="tb-ticker-track")(
                    *[Span(ticks, cls="tb-tick") for _ in range(4)],
                ),
            ),
            Div(cls="tb-divider"),
            A("Get Protected →", href="/login", cls="tb-pill"),
        ),
    )


# ─── Page loader ─────────────────────────────────────────────────────────────

def _page_loader() -> FT:
    return Div(id="page-loader")(
        Div(cls="loader-glow"),
        Div(cls="loader-glow-2"),
        Div(cls="loader-logo-wrap")(
            Div(cls="loader-spin-ring"),
            Div(cls="loader-logo")("T"),
        ),
        Div(cls="loader-brand-text")("Teluka"),
        Div(cls="loader-dots")(
            Div(cls="loader-dot"),
            Div(cls="loader-dot"),
            Div(cls="loader-dot"),
        ),
        Div(cls="loader-bar-track")(
            Div(cls="loader-bar-fill"),
        ),
        Script("""
(function(){
  function hide(){
    var l=document.getElementById('page-loader');
    if(l){l.classList.add('hidden');setTimeout(function(){l.remove();},520);}
  }
  if(document.readyState==='complete'){hide();}
  else{window.addEventListener('load',hide);}
})();
        """),
    )


# ─── Aurora background ───────────────────────────────────────────────────────

def _bg() -> FT:
    return Div(cls="landing-bg")(
        Div(cls="aurora-orb orb-1"),
        Div(cls="aurora-orb orb-2"),
        Div(cls="aurora-orb orb-3"),
        Div(cls="aurora-orb orb-4"),
    )


# ─── Navbar ──────────────────────────────────────────────────────────────────

def _navbar() -> FT:
    return Nav(cls="lnav", id="lnav")(
        A("Teluka", href="/", cls="lnav-brand"),
        Div(cls="lnav-links")(
            A("Features", href="#features"),
            A("How it works", href="#how"),
            A("Reviews", href="#reviews"),
            A("Sign In →", href="/login", cls="btn-shimmer", style="padding:10px 22px;font-size:0.88rem"),
            Button(
                NotStr('<svg class="icon-sun" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg><svg class="icon-moon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'),
                id="theme-toggle",
                cls="theme-toggle",
                title="Toggle light / dark",
                onclick="toggleTheme()",
            ),
        ),
    )


# ─── Hero ─────────────────────────────────────────────────────────────────────

def _hero() -> FT:
    return Section(
        Div(cls="hero-left")(
            Div(cls="hero-pill")(
                Div(cls="hero-pill-dot")("🇵🇭"),
                Span("Made for the Philippines"),
            ),
            H1(cls="hero-h1")(
                Span("Stop Getting"),
                Br(),
                Span("Scammed", cls="line-strike"),
                Span(" on"),
                Br(),
                Span("Marketplace.", cls="word-swap"),
            ),
            P(
                "Teluka wraps every buy-and-sell deal in escrow, "
                "live photo verification, and AI-powered scam detection. "
                "Your money moves only when you say it does.",
                cls="hero-desc",
            ),
            Div(cls="hero-actions")(
                A(
                    _icon_shield(), " Get Protected — It's Free",
                    href="/login", cls="btn-shimmer",
                ),
                A(
                    _icon_play(), " See How It Works",
                    href="#how", cls="btn-outline-hero",
                ),
            ),
            Div(cls="hero-proof")(
                Div(cls="proof-avatars")(
                    Div("JR", cls="proof-avatar pa-1"),
                    Div("ML", cls="proof-avatar pa-2"),
                    Div("KD", cls="proof-avatar pa-3"),
                    Div("AS", cls="proof-avatar pa-4"),
                ),
                P(cls="proof-text")(
                    Strong("2,400+ Filipinos"),
                    " already selling without fear",
                ),
            ),
        ),
        Div(cls="hero-right")(
            _phone_mockup(),
        ),
        cls="hero-l",
    )


def _phone_mockup() -> FT:
    return Div(cls="mockup-scene", id="mockup")(
        Div(cls="phone-frame")(
            Div(cls="phone-notch"),
            Div(cls="phone-screen")(
                Div(cls="mock-app-bar")(
                    Div("Teluka", cls="mock-logo"),
                    Div(cls="mock-avatar"),
                ),
                Div(cls="mock-tx")(
                    Div("Active Transaction", cls="mock-tx-label"),
                    Div("iPhone 14 Pro Max", cls="mock-tx-name"),
                    Div("₱45,000", cls="mock-tx-amt"),
                    Div(cls="mock-tx-status")(
                        Div(cls="status-dot"),
                        Span("Funds Held in Escrow"),
                    ),
                ),
                Div(cls="mock-steps")(
                    Div(cls="mock-step-dot done")("✓"),
                    Div(cls="mock-step-line done")(Div(cls="mock-step-line-fill")),
                    Div(cls="mock-step-dot done")("✓"),
                    Div(cls="mock-step-line done")(Div(cls="mock-step-line-fill")),
                    Div(cls="mock-step-dot active")("3"),
                    Div(cls="mock-step-line todo"),
                    Div(cls="mock-step-dot todo")("4"),
                    Div(cls="mock-step-line todo"),
                    Div(cls="mock-step-dot todo")("5"),
                ),
                _mini_detail_card("📦", "Delivery", "Lalamove • In Transit", "#06b6d4"),
                _mini_detail_card("📸", "Evidence", "3/3 photos verified", "#10b981"),
            ),
        ),
        # Floating badges
        Div(cls="phone-badge pb-1")(Div(cls="phone-badge-dot dot-green"), "EXIF Verified ✓"),
        Div(cls="phone-badge pb-2")(Div(cls="phone-badge-dot dot-violet"), "Escrow Active 🔒"),
        Div(cls="phone-badge pb-3")(Div(cls="phone-badge-dot dot-cyan"), "Scam Score: Low"),
        Div(cls="phone-shadow"),
    )


def _mini_detail_card(icon: str, label: str, value: str, color: str) -> FT:
    return Div(
        style=(
            f"display:flex;align-items:center;gap:10px;padding:10px 14px;"
            f"background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.07);"
            f"border-radius:12px;margin-bottom:10px;"
        )
    )(
        Div(icon, style=f"font-size:1rem;width:30px;text-align:center"),
        Div(
            Div(label, style="font-size:0.6rem;color:rgba(255,255,255,0.35);text-transform:uppercase;letter-spacing:0.06em"),
            Div(value, style=f"font-size:0.78rem;font-weight:700;color:{color}"),
        ),
    )


# ─── Marquee ──────────────────────────────────────────────────────────────────

def _marquee() -> FT:
    items = [
        ("md-violet", "GCash & Maya Payments"),
        ("md-green",  "Escrow Protection"),
        ("md-cyan",   "EXIF Photo Verification"),
        ("md-pink",   "Unboxing Video Gate"),
        ("md-violet", "AI Scam Detection"),
        ("md-green",  "Lalamove Tracking"),
        ("md-cyan",   "Supabase Realtime"),
        ("md-pink",   "PayMongo Integration"),
        ("md-violet", "KYC Verified Users"),
        ("md-green",  "Zero Bait & Switch"),
    ]

    def item(dot_cls: str, text: str) -> FT:
        return Div(cls="marquee-item")(
            Div(cls=f"marquee-dot {dot_cls}"),
            Span(text),
            Span("·"),
        )

    # Duplicate for seamless loop
    all_items = [item(d, t) for d, t in items] * 2
    return Div(cls="marquee-wrap")(
        Div(cls="marquee-track")(*all_items),
    )


# ─── Stats ────────────────────────────────────────────────────────────────────

def _stats() -> FT:
    return Div(
        Div(cls="stats-bar reveal")(
            Div(cls="stat-cell")(
                Div("₱12M+", cls="stat-num", **{"data-count": "12000000", "data-prefix": "₱", "data-suffix": "+"}),
                Div("Protected in Escrow", cls="stat-desc"),
            ),
            Div(cls="stat-cell")(
                Div("847", cls="stat-num", **{"data-count": "847"}),
                Div("Scams Blocked", cls="stat-desc"),
            ),
            Div(cls="stat-cell")(
                Div("2,400+", cls="stat-num"),
                Div("Verified Users", cls="stat-desc"),
            ),
        ),
        style="padding:0 40px 80px; max-width:1180px; margin:0 auto",
    )


# ─── Features bento grid ──────────────────────────────────────────────────────

def _features_bento() -> FT:
    return Section(cls="lsection", id="features")(
        Div(cls="lsection-hd reveal")(
            Div("Why Teluka?", cls="lsection-eye"),
            H2("Every layer of protection", cls="lsection-title"),
            P(
                "We built the security stack Facebook Marketplace never had.",
                cls="lsection-sub",
            ),
        ),
        Div(cls="bento")(
            # Row 1: wide + regular
            _bento_escrow_flow(),    # span-8 wide
            _bento_risk(),           # span-4 regular
            # Row 2: regular × 3
            _bento_exif(),
            _bento_delivery(),
            _bento_unboxing(),
            # Row 3: full + regular
            _bento_payments(),       # span-8
            _bento_kyc(),            # span-4
        ),
    )


def _bento_escrow_flow() -> FT:
    return Div(cls="bento-cell bento-w reveal", data_tilt="true")(
        Div(
            cls="bento-blob",
            style="width:300px;height:300px;background:radial-gradient(circle,rgba(124,58,237,0.15) 0%,transparent 70%);top:-80px;right:-40px",
        ),
        Div(cls="bento-icon bi-violet")("🔒"),
        H3("Escrow Protection", cls="bento-title"),
        P(
            "Funds are locked with PayMongo — never transferred directly. "
            "Money moves only when all 5 conditions are verified.",
            cls="bento-desc",
        ),
        Div(cls="bento-flow")(
            Div(cls="flow-node")(Div("₱", cls="flow-dot fd-done"), Div("Paid", cls="flow-label")),
            Div(cls="flow-line")(Div(cls="flow-line-fill")),
            Div(cls="flow-node")(Div("🔒", cls="flow-dot fd-active"), Div("Held", cls="flow-label")),
            Div(cls="flow-line")(Div(cls="flow-line-fill")),
            Div(cls="flow-node")(Div("📸", cls="flow-dot fd-done"), Div("Evidence", cls="flow-label")),
            Div(cls="flow-line"),
            Div(cls="flow-node")(Div("🚚", cls="flow-dot fd-next"), Div("Delivery", cls="flow-label")),
            Div(cls="flow-line"),
            Div(cls="flow-node")(Div("✓", cls="flow-dot fd-next"), Div("Released", cls="flow-label")),
        ),
    )


def _bento_risk() -> FT:
    return Div(cls="bento-cell bento-c reveal reveal-delay-1", data_tilt="true")(
        Div(cls="bento-icon bi-pink")("🧠"),
        H3("AI Scam Detection", cls="bento-title"),
        P("Every transaction is scored against blacklisted numbers and fraud patterns before a single peso moves.", cls="bento-desc"),
        Div(cls="bento-big-stat")("0.3s"),
        P("avg. risk check time", style="font-size:0.75rem;color:rgba(255,255,255,0.3);margin-top:4px"),
    )


def _bento_exif() -> FT:
    return Div(cls="bento-cell bento-c reveal reveal-delay-1", data_tilt="true")(
        Div(cls="bento-icon bi-cyan")("📸"),
        H3("Live Photo Verification", cls="bento-title"),
        P("EXIF metadata is checked against the transaction timestamp. Photos older than 24h are automatically rejected.", cls="bento-desc"),
    )


def _bento_delivery() -> FT:
    return Div(cls="bento-cell bento-c reveal reveal-delay-2", data_tilt="true")(
        Div(cls="bento-icon bi-blue")("🚚"),
        H3("Delivery Tracking", cls="bento-title"),
        P("Lalamove & Grab integration. Funds stay locked until the courier confirms DELIVERED status.", cls="bento-desc"),
    )


def _bento_unboxing() -> FT:
    return Div(cls="bento-cell bento-c reveal reveal-delay-3", data_tilt="true")(
        Div(cls="bento-icon bi-amber")("🎥"),
        H3("Unboxing Gate", cls="bento-title"),
        P("Buyers must upload an unboxing video before payment is released. The final defense against bait-and-switch.", cls="bento-desc"),
    )


def _bento_payments() -> FT:
    return Div(cls="bento-cell bento-w reveal", data_tilt="true")(
        Div(
            cls="bento-blob",
            style="width:250px;height:250px;background:radial-gradient(circle,rgba(6,182,212,0.12) 0%,transparent 70%);bottom:-40px;right:20px",
        ),
        Div(cls="bento-icon bi-green")("⚡"),
        H3("Instant GCash & Maya", cls="bento-title"),
        P(
            "The wallets 9 out of 10 Filipinos already use. No bank account needed — "
            "pay and get paid in centavos with zero friction.",
            cls="bento-desc",
        ),
        Div(style="display:flex;gap:12px;margin-top:20px;position:relative;z-index:1")(
            _wallet_chip("GCash", "#0061AF"),
            _wallet_chip("Maya", "#00C800"),
            _wallet_chip("PayMongo", "#7c3aed"),
        ),
    )


def _bento_kyc() -> FT:
    return Div(cls="bento-cell bento-c reveal reveal-delay-1", data_tilt="true")(
        Div(cls="bento-icon bi-violet")("🪪"),
        H3("KYC Verification", cls="bento-title"),
        P("GCash and Maya-verified numbers get higher trust scores. Unverified sellers face stricter evidence requirements.", cls="bento-desc"),
    )


def _wallet_chip(name: str, color: str) -> FT:
    return Div(
        name,
        style=(
            f"display:inline-flex;align-items:center;padding:6px 14px;"
            f"background:{color}22;border:1px solid {color}44;"
            f"border-radius:999px;font-size:0.78rem;font-weight:700;color:{color};"
        ),
    )


# ─── How it works ─────────────────────────────────────────────────────────────

def _how_it_works() -> FT:
    steps = [
        ("Initiate", "Create a Transaction",
         "Buyer locks in the item description and price. All terms are set — no last-minute changes possible."),
        ("Escrow", "Pay into Escrow",
         "Buyer pays via GCash or Maya. Funds are held by PayMongo, not the seller, until every condition is met."),
        ("Verify", "Seller Submits Live Evidence",
         "Seller uploads real-time photos. Teluka reads EXIF metadata and rejects anything older than 24 hours."),
        ("Track", "Automated Delivery Tracking",
         "A Lalamove or Grab rider handles logistics. The app polls the courier API until DELIVERED is confirmed."),
        ("Release", "Unbox & Release Payment",
         "Buyer records an unboxing video, confirms the item, and releases payment. Seller gets paid instantly."),
    ]
    step_items = [
        Div(cls=f"tl-item reveal reveal-delay-{i+1}")(
            Div(str(i + 1), cls="tl-num"),
            Div(cls="tl-content")(
                Span(tag, cls="tl-tag"),
                H4(title, cls="tl-title"),
                P(desc, cls="tl-desc"),
            ),
        )
        for i, (tag, title, desc) in enumerate(steps)
    ]
    return Section(cls="lsection", id="how")(
        Div(cls="lsection-hd reveal")(
            Div("The Process", cls="lsection-eye"),
            H2("Five steps. Zero scams.", cls="lsection-title"),
            P("Every deal follows the same iron-clad flow.", cls="lsection-sub"),
        ),
        Div(cls="timeline")(*step_items),
    )


# ─── Social proof ─────────────────────────────────────────────────────────────

def _social_proof() -> FT:
    reviews = [
        ("JR", "pa-1", "Sold my RTX 4090 for ₱38,000. Buyer was in Davao, I was in Manila. Teluka held the funds, Lalamove picked it up, and I got paid the same day it was delivered. Zero stress.",
         "Jose R.", "Quezon City"),
        ("ML", "pa-2", "Tried to buy an iPhone and got scammed twice before. With Teluka the seller had to show LIVE photos. You can tell immediately if it's the real unit. Game changer talaga.",
         "Maria L.", "Cebu City"),
        ("KD", "pa-3", "As a seller I love that buyers can't do a refund scam. The escrow only releases after the unboxing video confirms the item. Now I actually feel safe shipping expensive items.",
         "Kevin D.", "Makati"),
        ("AS", "pa-4", "Yung scam detection blocked a buyer with 5 reports before they even messaged me. Hindi ko na kailangang magtaka kung legit ba yung tao.",
         "Ana S.", "Pasig"),
    ]
    cards = [
        Div(cls=f"review-card reveal reveal-delay-{i+1}")(
            Div("★★★★★", cls="review-stars"),
            P(f'"{text}"', cls="review-text"),
            Div(cls="review-author")(
                Div(initials, cls=f"review-ava {ava_cls}"),
                Div(
                    Div(name, cls="review-name"),
                    Div(loc, cls="review-loc"),
                ),
            ),
        )
        for i, (initials, ava_cls, text, name, loc) in enumerate(reviews)
    ]
    return Section(cls="lsection", id="reviews")(
        Div(cls="lsection-hd reveal")(
            Div("Real People. Real Deals.", cls="lsection-eye"),
            H2("Filipinos who stopped getting scammed", cls="lsection-title"),
        ),
        Div(cls="reviews-grid")(*cards),
    )


# ─── CTA ──────────────────────────────────────────────────────────────────────

def _cta() -> FT:
    return Section(cls="cta-section")(
        Div(cls="cta-bg"),
        Div(cls="cta-inner reveal")(
            H2(cls="cta-title")(
                "Your next deal is ",
                Span("protected.", cls="word-swap"),
            ),
            P(
                "Join thousands of Filipinos who've made scam-proof deals. "
                "Free to start — no credit card, no bank account needed.",
                cls="cta-sub",
            ),
            Div(cls="btn-cta-wrap")(
                Div(cls="btn-cta-ring"),
                A(
                    _icon_shield(), " Create Free Account",
                    href="/login", cls="btn-shimmer",
                    style="font-size:1.05rem;padding:18px 44px",
                ),
            ),
        ),
    )


# ─── Footer ───────────────────────────────────────────────────────────────────

def _footer() -> FT:
    return Footer(cls="lfooter")(
        Div(
            Div("Teluka", cls="lfooter-brand"),
            P("Protecting buyers and sellers across the Philippines.", cls="lfooter-copy"),
        ),
        Div(cls="lfooter-links")(
            A("Privacy", href="#"),
            A("Terms", href="#"),
            A("Support", href="#"),
        ),
    )


# ─── Inline SVG icons ─────────────────────────────────────────────────────────

def _icon_shield() -> FT:
    return NotStr('<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>')


def _icon_play() -> FT:
    return NotStr('<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8" fill="currentColor" stroke="none"/></svg>')


# ─── Scripts ──────────────────────────────────────────────────────────────────

def _scripts() -> FT:
    return Script("""
/* ── PWA ── */
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => navigator.serviceWorker.register('/static/sw.js'));
}

/* ── Theme toggle ── */
function toggleTheme() {
  const html = document.documentElement;
  const next = html.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
  html.setAttribute('data-theme', next);
  localStorage.setItem('teluka-theme', next);
  document.getElementById('theme-toggle').classList.toggle('is-light', next === 'light');
}
// Sync toggle button state on load
(function() {
  const t = document.documentElement.getAttribute('data-theme') || 'dark';
  const btn = document.getElementById('theme-toggle');
  if (btn && t === 'light') btn.classList.add('is-light');
})();

/* ── Navbar scroll + banner 3D fold-away + parallax ── */
const lnav  = document.getElementById('lnav');
const tBanner = document.getElementById('top-banner');
const BANNER_H = 48;

window.addEventListener('scroll', () => {
  const y = window.scrollY;

  /* navbar glass blur */
  lnav.classList.toggle('scrolled', y > BANNER_H + 10);

  /* ── banner 3D fold-away ── */
  if (tBanner) {
    const p = Math.min(y / BANNER_H, 1);           // 0 → 1 as banner exits
    const rotX   = p * -90;                         // folds back around X
    const scaleZ = 1 - p * 0.4;
    tBanner.style.transform =
      `perspective(300px) rotateX(${rotX}deg) scaleY(${scaleZ})`;
    tBanner.style.opacity   = String(Math.max(1 - p * 2, 0));
    tBanner.style.pointerEvents = p >= 1 ? 'none' : '';
    document.body.classList.toggle('banner-gone', p >= 1);
  }

  /* ── subtle hero parallax ── */
  const orbs = document.querySelectorAll('.aurora-orb');
  orbs.forEach((orb, i) => {
    const speed = [0.08, 0.14, 0.06, 0.12][i] || 0.1;
    orb.style.transform = `translateY(${y * speed}px)`;
  });

  /* ── scroll depth on hero headline ── */
  const heroLeft = document.querySelector('.hero-left');
  if (heroLeft) {
    const pct = Math.min(y / 600, 1);
    heroLeft.style.transform = `translateY(${pct * 60}px) scale(${1 - pct * 0.04})`;
    heroLeft.style.opacity   = String(1 - pct * 1.2);
  }
}, { passive: true });

/* ── Scroll reveal ── */
const revealEls = document.querySelectorAll('.reveal');
const observer = new IntersectionObserver((entries) => {
  entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); observer.unobserve(e.target); } });
}, { threshold: 0.12 });
revealEls.forEach(el => observer.observe(el));

/* ── 3D tilt on bento cells ── */
document.querySelectorAll('[data-tilt]').forEach(card => {
  card.addEventListener('mousemove', e => {
    const r = card.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width  - 0.5;
    const y = (e.clientY - r.top)  / r.height - 0.5;
    card.style.transform = `perspective(800px) rotateY(${x * 12}deg) rotateX(${-y * 12}deg) translateZ(8px)`;
    card.style.setProperty('--mx', `${(x + 0.5) * 100}%`);
    card.style.setProperty('--my', `${(y + 0.5) * 100}%`);
    card.classList.add('tilt-active');
  });
  card.addEventListener('mouseleave', () => {
    card.style.transform = 'perspective(800px) rotateY(0deg) rotateX(0deg) translateZ(0)';
    card.classList.remove('tilt-active');
  });
});

/* ── Phone mockup mouse parallax ── */
const mockup = document.getElementById('mockup');
if (mockup) {
  document.addEventListener('mousemove', e => {
    const cx = window.innerWidth  / 2;
    const cy = window.innerHeight / 2;
    const dx = (e.clientX - cx) / cx;
    const dy = (e.clientY - cy) / cy;
    mockup.style.animation = 'none';
    mockup.style.transform = `perspective(1200px) rotateY(${-8 + dx * 6}deg) rotateX(${2 - dy * 4}deg) translateY(${dy * -8}px)`;
  }, { passive: true });
}

/* ── Animated counters ── */
function animateCount(el) {
  const target = parseInt(el.dataset.count || '0', 10);
  const prefix = el.dataset.prefix || '';
  const suffix = el.dataset.suffix || '';
  const duration = 2000;
  const start = performance.now();
  function update(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const value = Math.floor(eased * target);
    el.textContent = prefix + value.toLocaleString() + suffix;
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}
const countObs = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting && e.target.dataset.count) {
      animateCount(e.target);
      countObs.unobserve(e.target);
    }
  });
}, { threshold: 0.5 });
document.querySelectorAll('[data-count]').forEach(el => countObs.observe(el));

/* ── Canvas particles ── */
(function() {
  const canvas = document.getElementById('particles');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let W, H, particles;

  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }

  function init() {
    resize();
    particles = Array.from({ length: 60 }, () => ({
      x: Math.random() * W, y: Math.random() * H,
      r: Math.random() * 1.5 + 0.5,
      vx: (Math.random() - 0.5) * 0.25,
      vy: (Math.random() - 0.5) * 0.25,
      a: Math.random(),
    }));
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    particles.forEach(p => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      const isDark = document.documentElement.getAttribute('data-theme') !== 'light';
      ctx.fillStyle = isDark
        ? `rgba(13,148,136,${p.a * 0.55})`
        : `rgba(13,148,136,${p.a * 0.25})`;
      ctx.fill();
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;
      if (p.y < 0) p.y = H; if (p.y > H) p.y = 0;
    });
    requestAnimationFrame(draw);
  }

  window.addEventListener('resize', () => { resize(); });
  init(); draw();
})();
""")
