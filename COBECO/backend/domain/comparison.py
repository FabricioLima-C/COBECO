from decimal import ROUND_HALF_UP, Decimal

from backend.domain.errors import BusinessError


def compare(items: list[dict], suppliers: list[dict], offers: list[dict]) -> dict:
    if not items:
        raise BusinessError("EMPTY_LIST", "Adicione pelo menos um produto.")
    lookup = {(o["supplier_id"], o["product_id"]): o for o in offers if o["active"]}
    rows = []
    for supplier in suppliers:
        available, missing = [], []
        total = Decimal("0")
        for item in items:
            offer = lookup.get((supplier["id"], item["product_id"]))
            if offer is None or offer["stock"] < item["quantity"]:
                missing.append(item["name"])
            else:
                available.append(item["name"])
                total += Decimal(str(offer["price"])) * item["quantity"]
        rows.append(
            {
                "supplier_id": supplier["id"],
                "supplier_name": supplier["name"],
                "available_items": available,
                "missing_items": missing,
                "coverage": round(len(available) / len(items) * 100, 2),
                "total": str(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)) if available else None,
                "partial": len(available) != len(items),
            }
        )
    rows.sort(key=lambda r: (r["total"] is None, Decimal(r["total"] or "0"), r["supplier_name"]))
    eligible = [r for r in rows if r["total"] is not None]
    best = []
    if eligible:
        coverage = max(r["coverage"] for r in eligible)
        eligible = [r for r in eligible if r["coverage"] == coverage]
        minimum = min(Decimal(r["total"]) for r in eligible)
        best = [r["supplier_id"] for r in eligible if Decimal(r["total"]) == minimum]
    return {"rows": rows, "best_supplier_ids": best, "tied": len(best) > 1}
