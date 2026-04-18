from fasthtml.common import *


def page_shell(*content, title: str = "Teluka") -> FT:
    """Outer shell: meta, styles, and body wrapper."""
    return Html(
        Head(
            Meta(charset="UTF-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1"),
            Title(title),
            Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css"),
        ),
        Body(
            Main(*content, cls="container"),
        ),
    )


def navbar() -> FT:
    return Nav(
        Ul(Li(Strong("Teluka"))),
        Ul(
            Li(A("Transactions", href="/transactions")),
            Li(A("Profile", href="/profile")),
        ),
        cls="container-fluid",
    )


def transaction_card(tx_id: str, item: str, amount_centavos: int, status: str) -> FT:
    amount_php = f"₱{amount_centavos / 100:,.2f}"
    badge_cls = {
        "pending": "secondary",
        "escrowed": "primary",
        "completed": "contrast",
        "disputed": "warning",
        "refunded": "",
    }.get(status, "secondary")
    return Card(
        Header(Strong(item)),
        P(f"Amount: {amount_php}"),
        P(Small(f"Status: "), Mark(status, cls=badge_cls)),
        Footer(
            A("View", href=f"/transactions/{tx_id}", role="button", cls="outline"),
        ),
    )


def status_badge(status: str) -> FT:
    colors = {
        "pending": "#999",
        "escrowed": "#0070f3",
        "evidence_submitted": "#f5a623",
        "in_transit": "#7b61ff",
        "delivered": "#17c964",
        "completed": "#17c964",
        "disputed": "#f31260",
        "cancelled": "#999",
        "refunded": "#f5a623",
    }
    color = colors.get(status, "#999")
    return Span(
        status.replace("_", " ").title(),
        style=f"background:{color};color:#fff;padding:2px 10px;border-radius:12px;font-size:0.8em;",
    )


def risk_badge(risk_score: float) -> FT:
    if risk_score < 30:
        label, color = "Low Risk", "#17c964"
    elif risk_score < 60:
        label, color = "Medium Risk", "#f5a623"
    else:
        label, color = "High Risk", "#f31260"
    return Span(
        f"{label} ({risk_score:.0f})",
        style=f"background:{color};color:#fff;padding:2px 10px;border-radius:12px;font-size:0.8em;",
    )


def escrow_flow_steps(current_status: str) -> FT:
    steps = [
        ("pending", "Payment"),
        ("escrowed", "Funds Held"),
        ("evidence_submitted", "Evidence"),
        ("in_transit", "Shipping"),
        ("delivered", "Delivered"),
        ("unboxing_uploaded", "Unboxing"),
        ("completed", "Released"),
    ]
    items = []
    reached = False
    for slug, label in steps:
        if slug == current_status:
            reached = True
        cls = "done" if not reached else ("active" if slug == current_status else "")
        items.append(Li(label, cls=cls))
    return Ol(*items, cls="escrow-steps")
