"""CLI du générateur.

    python -m generator sample --date 2026-04-07        statistiques d'une journée
    python -m generator traps --start 2026-08-01 --end 2026-10-20 [--out generator/traps.json]
"""
import argparse
import json
import sys
from collections import defaultdict
from datetime import date, timedelta

from generator.orders import expected_orders, generate_day


def sample(day: date) -> None:
    lines, traps = generate_day(day)
    paid = [l for l in lines if l["status"] == "paid"]
    revenue = sum(l["total_amount"] for l in paid)
    by_seller = defaultdict(float)
    for l in paid:
        by_seller[l["seller_id"]] += l["total_amount"]
    top = sorted(by_seller.values(), reverse=True)
    top20 = sum(top[: max(1, len(top) // 5)]) / revenue
    print(f"Date              : {day} (attendu ~{expected_orders(day):.0f} commandes, événement : {traps['event']})")
    print(f"Commandes / lignes: {len({l['order_id'] for l in lines})} / {len(lines)}")
    print(f"CA (paid)         : {revenue:,.2f} €  | panier moyen : {revenue / len({l['order_id'] for l in paid}):.2f} €")
    print(f"Vendeurs actifs   : {len(by_seller)}  | part du CA des 20 % premiers : {top20:.0%}")
    print(f"Pièges            : {len(traps['suspicious_prices'])} prix suspects, "
          f"{len(traps['null_customer'])} customer_id null, {len(traps['future_created_at'])} dates futures, "
          f"{len(traps['duplicated_order_ids'])} commandes dupliquées")
    print("Exemple de ligne  :", json.dumps(lines[0], ensure_ascii=False))


def traps(start: date, end: date, out: str) -> None:
    result = []
    d = start
    while d <= end:
        result.append(generate_day(d)[1])
        d += timedelta(days=1)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"{len(result)} jours écrits dans {out}")


def main() -> int:
    parser = argparse.ArgumentParser(prog="generator")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("sample", help="Statistiques d'une journée générée")
    p.add_argument("--date", type=date.fromisoformat, required=True)
    p = sub.add_parser("traps", help="Exporte les lignes piégées sur une période")
    p.add_argument("--start", type=date.fromisoformat, required=True)
    p.add_argument("--end", type=date.fromisoformat, required=True)
    p.add_argument("--out", default="generator/traps.json")
    args = parser.parse_args()

    if args.command == "sample":
        sample(args.date)
    else:
        traps(args.start, args.end, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
