from fasthtml.common import *


def landing_page() -> FT:
    return Html(
        _head(),
        Body(
            _page_loader(),
            Div(cls="scroll-progress", id="scroll-progress"),
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
            _pwa_install_banner(),
            Script(src="/static/js/app.js"),
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
        "🔒 Your money is held safe  ·  📸 Real photos required  ·  🤖 Scam alerts  ·  "
        "⚡ GCash & Maya  ·  ⚖️ We settle disputes fairly  ·  ✅ Verified sellers  ·  "
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
    _theme_btn = Button(
        NotStr('<svg class="icon-sun" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg><svg class="icon-moon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'),
        id="theme-toggle",
        cls="theme-toggle",
        title="Toggle light / dark",
        onclick="toggleTheme()",
    )
    return Div()(
        Nav(cls="lnav", id="lnav")(
            A("Teluka", href="/", cls="lnav-brand"),
            Div(cls="lnav-links")(
                A("Features", href="#features"),
                A("How it works", href="#how"),
                A("Reviews", href="#reviews"),
                A("Sign In →", href="/login", cls="btn-shimmer", style="padding:10px 22px;font-size:0.88rem"),
                _theme_btn,
            ),
            Div(cls="lnav-links", style="gap:8px;")(
                _theme_btn,
                Button(
                    Span(), Span(), Span(),
                    cls="nav-hamburger", id="nav-hamburger",
                    onclick="toggleMobileNav()",
                    aria_label="Open menu",
                ),
            ),
        ),
        # Mobile nav overlay
        Div(cls="mobile-nav", id="mobile-nav")(
            A("Features",     href="#features",   onclick="closeMobileNav()"),
            A("How it works", href="#how",        onclick="closeMobileNav()"),
            A("Reviews",      href="#reviews",    onclick="closeMobileNav()"),
            Div(cls="mobile-nav-divider"),
            A("Sign In →", href="/login", cls="mobile-nav-cta"),
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
                "Teluka holds your money safely until you're happy with what you received. "
                "The seller only gets paid after you confirm the item is exactly as described.",
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
                        Span("Money Held Safely 🔒"),
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
                _mini_detail_card("📸", "Photos", "3/3 real photos checked ✓", "#10b981"),
                _mini_detail_card("⏳", "Status", "Waiting for your review", "#06b6d4"),
            ),
        ),
        # Floating badges
        Div(cls="phone-badge pb-1")(Div(cls="phone-badge-dot dot-green"), "Photo Verified ✓"),
        Div(cls="phone-badge pb-2")(Div(cls="phone-badge-dot dot-violet"), "Money Held Safe 🔒"),
        Div(cls="phone-badge pb-3")(Div(cls="phone-badge-dot dot-cyan"), "Scam Risk: Low"),
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
        ("md-violet", "🔒", "Money Held Safe"),
        ("md-green",  "🛡️", "No Bait & Switch"),
        ("md-cyan",   "📸", "Real Photos Required"),
        ("md-pink",   "🎥", "Video Proof on Delivery"),
        ("md-violet", "🤖", "Scam Alerts"),
        ("md-green",  "⚖️", "Fair Dispute Resolution"),
        ("md-cyan",   "⚡", "Instant GCash & Maya"),
        ("md-pink",   "✅", "Verified Sellers Only"),
        ("md-violet", "🇵🇭", "Made for Filipinos"),
        ("md-green",  "🆓", "Free to Start"),
    ]

    def item(dot_cls: str, emoji: str, text: str) -> FT:
        return Div(cls="marquee-item")(
            Span(emoji, cls="marquee-emoji"),
            Span(text, cls="marquee-text"),
            Span(cls=f"marquee-sep"),
        )

    all_items = [item(d, e, t) for d, e, t in items] * 3
    return Div(cls="marquee-section")(
        Div(cls="marquee-label")("EVERYTHING YOU GET"),
        Div(cls="marquee-wrap")(
            Div(cls="marquee-track")(*all_items),
        ),
        Div(cls="marquee-wrap marquee-wrap-reverse")(
            Div(cls="marquee-track marquee-track-reverse")(
                *[item(d, e, t) for d, e, t in reversed(items)] * 3
            ),
        ),
    )


# ─── Stats ────────────────────────────────────────────────────────────────────

def _stats() -> FT:
    stats = [
        ("₱12M+",  "12000000", "₱", "+", "Kept Safe for Buyers", "🔐", "md-violet"),
        ("847",    "847",      "",  "",  "Scams Blocked",         "🛡️",  "md-pink"),
        ("2,400+", "2400",     "",  "+", "Happy Users",           "😊",  "md-green"),
    ]
    cells = []
    for num, count, prefix, suffix, label, icon, dot in stats:
        cells.append(
            Div(cls="stat-card reveal")(
                Div(cls=f"stat-icon-wrap {dot}")(Span(icon, cls="stat-icon")),
                Div(
                    cls="stat-num",
                    **{
                        "data-count":  count,
                        "data-prefix": prefix,
                        "data-suffix": suffix,
                    }
                )(num),
                Div(cls="stat-label")(label),
                Div(cls="stat-glow"),
            )
        )
    return Div(cls="stats-section")(
        Div(cls="stats-eyebrow scroll-fade")("BY THE NUMBERS"),
        Div(cls="stats-grid stagger-children")(*cells),
    )


# ─── Features bento grid ──────────────────────────────────────────────────────

def _features_bento() -> FT:
    return Section(cls="lsection", id="features")(
        Div(cls="lsection-hd reveal")(
            Div("Why Teluka?", cls="lsection-eye"),
            H2("We protect you at every step", cls="lsection-title"),
            P(
                "So you never have to worry about losing your money again.",
                cls="lsection-sub",
            ),
        ),
        Div(cls="bento")(
            # Row 1: wide + regular
            _bento_escrow_flow(),    # span-8 wide
            _bento_risk(),           # span-4 regular
            # Row 2: regular × 3
            _bento_exif(),
            _bento_dispute(),
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
        H3("Your money is safe until you're happy", cls="bento-title"),
        P(
            "When you pay, the money is held — not given to the seller. "
            "It only gets released after you confirm you got what you paid for.",
            cls="bento-desc",
        ),
        Div(cls="bento-flow")(
            Div(cls="flow-node")(Div("₱", cls="flow-dot fd-done"), Div("You Pay", cls="flow-label")),
            Div(cls="flow-line")(Div(cls="flow-line-fill")),
            Div(cls="flow-node")(Div("🔒", cls="flow-dot fd-active"), Div("Held", cls="flow-label")),
            Div(cls="flow-line")(Div(cls="flow-line-fill")),
            Div(cls="flow-node")(Div("📸", cls="flow-dot fd-done"), Div("Proof", cls="flow-label")),
            Div(cls="flow-line"),
            Div(cls="flow-node")(Div("⚖️", cls="flow-dot fd-next"), Div("Review", cls="flow-label")),
            Div(cls="flow-line"),
            Div(cls="flow-node")(Div("✓", cls="flow-dot fd-next"), Div("Released", cls="flow-label")),
        ),
    )


def _bento_risk() -> FT:
    return Div(cls="bento-cell bento-c reveal reveal-delay-1", data_tilt="true")(
        Div(cls="bento-icon bi-pink")("🧠"),
        H3("We spot scammers before they spot you", cls="bento-title"),
        P("Every deal is automatically checked against known scammers. If something looks suspicious, we warn you before any money moves.", cls="bento-desc"),
        Div(cls="bento-big-stat")("0.3s"),
        P("avg. check time per deal", style="font-size:0.75rem;color:rgba(255,255,255,0.3);margin-top:4px"),
    )


def _bento_exif() -> FT:
    return Div(cls="bento-cell bento-c reveal reveal-delay-1", data_tilt="true")(
        Div(cls="bento-icon bi-cyan")("📸"),
        H3("Proof the item is real — not a stock photo", cls="bento-title"),
        P("Sellers must upload a fresh photo of the actual item. If the photo was taken more than 24 hours ago, it's automatically rejected.", cls="bento-desc"),
    )


def _bento_dispute() -> FT:
    verdict_items = [
        ("Buyer wins",   "bi-pink",   "Evidence mismatch confirmed"),
        ("Seller wins",  "bi-green",  "Item matches listing"),
        ("Auto-release", "bi-violet", "No dispute in 48 h"),
    ]
    return Div(cls="bento-cell bento-c reveal reveal-delay-2", data_tilt="true")(
        Div(cls="bento-icon bi-blue")("⚖️"),
        H3("Something wrong? We settle it fairly", cls="bento-title"),
        P(
            "You have 48 hours to check what you received. "
            "Not what you expected? Tell us. We listen to both sides before any money moves.",
            cls="bento-desc",
        ),
        Div(cls="dispute-verdicts")(
            *[
                Div(cls=f"dispute-verdict-row")(
                    Div(cls=f"dispute-dot {dot_cls}"),
                    Div(cls="dispute-verdict-info")(
                        Div(verdict, cls="dispute-verdict-label"),
                        Div(desc, cls="dispute-verdict-sub"),
                    ),
                )
                for verdict, dot_cls, desc in verdict_items
            ]
        ),
    )


def _bento_unboxing() -> FT:
    return Div(cls="bento-cell bento-c reveal reveal-delay-3", data_tilt="true")(
        Div(cls="bento-icon bi-amber")("🎥"),
        H3("Record opening it — just to be sure", cls="bento-title"),
        P("Before payment is released, you simply record a short video of yourself opening the package. This one step stops bait-and-switch scams completely.", cls="bento-desc"),
    )


def _bento_payments() -> FT:
    return Div(cls="bento-cell bento-w reveal", data_tilt="true")(
        Div(
            cls="bento-blob",
            style="width:250px;height:250px;background:radial-gradient(circle,rgba(6,182,212,0.12) 0%,transparent 70%);bottom:-40px;right:20px",
        ),
        Div(cls="bento-icon bi-green")("⚡"),
        H3("Pay with GCash or Maya — you already have them", cls="bento-title"),
        P(
            "No need to set up anything new. Use the wallet you already have. "
            "Sellers get paid instantly once the deal is confirmed — no bank account needed.",
            cls="bento-desc",
        ),
        Div(style="display:flex;gap:12px;margin-top:20px;position:relative;z-index:1")(
            _wallet_chip("GCash", "#0061AF"),
            _wallet_chip("Maya", "#00C800"),
            _wallet_chip("Instant Payout", "#7c3aed"),
        ),
    )


def _bento_kyc() -> FT:
    return Div(cls="bento-cell bento-c reveal reveal-delay-1", data_tilt="true")(
        Div(cls="bento-icon bi-violet")("🪪"),
        H3("Only deal with people you can trust", cls="bento-title"),
        P("Sellers verified through GCash or Maya earn a higher trust rating. The more deals completed without issues, the stronger the reputation.", cls="bento-desc"),
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
        ("Agree", "Set the deal terms",
         "Buyer and seller agree on the item and price inside Teluka. Everything is written down — no he-said-she-said."),
        ("Pay", "Buyer pays — money is held, not sent",
         "The buyer pays via GCash or Maya. The money goes into a safe hold — the seller doesn't receive it yet."),
        ("Proof", "Seller shows the real item",
         "The seller sends a fresh photo of the actual item, taken right now. Old or recycled photos are automatically rejected."),
        ("Check", "Buyer has 48 hours to review",
         "Once the seller sends proof, the buyer has 48 hours to inspect everything. Not happy? Raise a dispute and Teluka will look into it."),
        ("Done", "Confirm and the seller gets paid",
         "Buyer opens the package on video, confirms it's correct, and releases the payment. The seller gets paid right away."),
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
            Div("How It Works", cls="lsection-eye"),
            H2("Simple, safe, step by step.", cls="lsection-title"),
            P("Every deal follows the same clear process — no surprises, no stress.", cls="lsection-sub"),
        ),
        Div(cls="timeline")(*step_items),
    )


# ─── Social proof ─────────────────────────────────────────────────────────────

def _social_proof() -> FT:
    reviews = [
        ("JR", "pa-1", "Sold my RTX 4090 for ₱38,000. Buyer was in Davao, I was in Manila. Teluka held the funds, the buyer had 48 hours to check everything, and I got paid the moment he confirmed. Zero stress.",
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


# ─── PWA Install Banner ───────────────────────────────────────────────────────

def _pwa_install_banner() -> FT:
    return Div(cls="pwa-banner", id="pwa-banner", aria_hidden="true")(
        # Glow ring behind the icon
        Div(cls="pwa-banner-glow"),
        # Left: icon + text
        Div(cls="pwa-banner-left")(
            Div(cls="pwa-banner-icon")(
                Div(cls="pwa-icon-ring"),
                Span("T", cls="pwa-icon-letter"),
            ),
            Div(cls="pwa-banner-copy")(
                Div(cls="pwa-banner-title")(
                    Span("Add Teluka", cls="pwa-title-main"),
                    Span(" to Home Screen", cls="pwa-title-sub"),
                ),
                Div(cls="pwa-banner-desc")(
                    Span(cls="pwa-desc-dot"), "Instant access  ·  Works offline  ·  No App Store needed",
                ),
            ),
        ),
        # Right: actions
        Div(cls="pwa-banner-actions")(
            Button("Later", cls="pwa-btn-dismiss", id="pwa-dismiss", type="button"),
            Button(cls="pwa-btn-install", id="pwa-install", type="button")(
                Div(cls="pwa-btn-shimmer"),
                NotStr('<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>'),
                Span("Install App"),
            ),
        ),
        # Close ×
        Button(cls="pwa-banner-close", id="pwa-close", type="button", aria_label="Dismiss")(
            NotStr('<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>'),
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
/* ── PWA service worker ── */
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => navigator.serviceWorker.register('/static/sw.js'));
}

/* ── PWA install banner ── */
(function () {
  const DISMISSED_KEY = 'teluka-pwa-dismissed';
  const banner  = document.getElementById('pwa-banner');
  const btnInstall  = document.getElementById('pwa-install');
  const btnDismiss  = document.getElementById('pwa-dismiss');
  const btnClose    = document.getElementById('pwa-close');
  let deferredPrompt = null;

  function showBanner() {
    if (!banner || sessionStorage.getItem(DISMISSED_KEY)) return;
    banner.classList.add('pwa-banner--visible');
    banner.removeAttribute('aria-hidden');
  }

  function hideBanner() {
    if (!banner) return;
    banner.classList.remove('pwa-banner--visible');
    banner.setAttribute('aria-hidden', 'true');
    sessionStorage.setItem(DISMISSED_KEY, '1');
  }

  /* Intercept the browser's native prompt */
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    /* Show after 3 s — give the page time to load */
    setTimeout(showBanner, 3000);
  });

  /* Already installed → never show */
  window.addEventListener('appinstalled', () => {
    hideBanner();
    deferredPrompt = null;
  });

  if (btnInstall) {
    btnInstall.addEventListener('click', async () => {
      if (!deferredPrompt) return;
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      deferredPrompt = null;
      hideBanner();
    });
  }

  if (btnDismiss) btnDismiss.addEventListener('click', hideBanner);
  if (btnClose)   btnClose.addEventListener('click', hideBanner);
})();

/* ── Mobile nav ── */
function toggleMobileNav() {
  const nav = document.getElementById('mobile-nav');
  const btn = document.getElementById('nav-hamburger');
  const open = nav.classList.toggle('open');
  btn.classList.toggle('open', open);
  document.body.style.overflow = open ? 'hidden' : '';
}
function closeMobileNav() {
  const nav = document.getElementById('mobile-nav');
  const btn = document.getElementById('nav-hamburger');
  nav.classList.remove('open');
  btn.classList.remove('open');
  document.body.style.overflow = '';
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

/* ── Scroll progress bar ── */
const scrollProgress = document.getElementById('scroll-progress');
function updateScrollProgress() {
  const scrollTop = window.scrollY;
  const docHeight = document.documentElement.scrollHeight - window.innerHeight;
  const pct = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
  if (scrollProgress) scrollProgress.style.width = pct + '%';
}

/* ── Navbar + banner + parallax on scroll ── */
const lnav    = document.getElementById('lnav');
const tBanner = document.getElementById('top-banner');
const BANNER_H = 48;

window.addEventListener('scroll', () => {
  const y = window.scrollY;

  /* scroll progress */
  updateScrollProgress();

  /* navbar glass */
  lnav.classList.toggle('scrolled', y > BANNER_H + 10);

  /* banner 3D fold-away */
  if (tBanner) {
    const p = Math.min(y / BANNER_H, 1);
    tBanner.style.transform = `perspective(300px) rotateX(${p * -90}deg) scaleY(${1 - p * 0.4})`;
    tBanner.style.opacity   = String(Math.max(1 - p * 2, 0));
    tBanner.style.pointerEvents = p >= 1 ? 'none' : '';
    document.body.classList.toggle('banner-gone', p >= 1);
  }

  /* aurora orb parallax */
  const orbs = document.querySelectorAll('.aurora-orb');
  orbs.forEach((orb, i) => {
    const speed = [0.08, 0.14, 0.06, 0.12][i] || 0.1;
    orb.style.transform = `translateY(${y * speed}px)`;
  });

  /* hero headline depth */
  const heroLeft = document.querySelector('.hero-left');
  if (heroLeft) {
    const pct = Math.min(y / 600, 1);
    heroLeft.style.transform = `translateY(${pct * 60}px) scale(${1 - pct * 0.04})`;
    heroLeft.style.opacity   = String(1 - pct * 1.2);
  }

  /* stat cards subtle parallax */
  const statCards = document.querySelectorAll('.stat-card');
  statCards.forEach((card, i) => {
    const rect  = card.getBoundingClientRect();
    const mid   = rect.top + rect.height / 2 - window.innerHeight / 2;
    const shift = mid * 0.04 * (i % 2 === 0 ? 1 : -1);
    if (!card.matches(':hover')) {
      card.style.transform = `translateY(${shift}px)`;
    }
  });

}, { passive: true });

/* ── Scroll reveal (legacy .reveal + new scroll-* classes) ── */
const revealObs = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.classList.add('visible', 'in-view');
      revealObs.unobserve(e.target);
    }
  });
}, { threshold: 0.1, rootMargin: '0px 0px -60px 0px' });

document.querySelectorAll('.reveal, .scroll-fade, .scroll-zoom, .scroll-left, .scroll-right')
  .forEach(el => revealObs.observe(el));

/* ── Stagger children of .stagger-children ── */
document.querySelectorAll('.stagger-children').forEach(parent => {
  Array.from(parent.children).forEach((child, i) => {
    child.style.transitionDelay = (i * 0.08) + 's';
  });
});

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
