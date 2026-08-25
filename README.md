# Order to Cash Automation

An Odoo addon implementing the Order-to-Cash proposal: Order Source tracking
on Sales Orders, a phone-first customer duplicate check, automatic overdue
tiering with follow-up activities, a payment-matching guardrail that never
guesses across customers, and two lightweight reporting dashboards.

This is a **demo / proof-of-concept build for a client walkthrough**, not a
final production package — see "Before you demo this" below.

## What's in here

| Area | What it does |
|---|---|
| `models/sale_order.py` | `x_order_source` field (Online Retail / Online Wholesale / Administration / Sales Team), auto-classified from the line's unit of measure |
| `models/res_partner.py` | Phone-first, name-second duplicate lookup helper |
| `wizards/customer_lookup_wizard.py` | The actual "Find / Verify Customer" popup, opened from a button on the Sales Order |
| `models/account_move.py` | `x_overdue_tier` computed field + daily cron that creates follow-up activities (Due Soon → Overdue 15+) |
| `models/account_payment.py` | Payment-matching guardrail: auto-reconciles only on a single clear match, otherwise flags `x_needs_match_review` for a human |
| `models/o2c_dashboard.py` | Two SQL-view reporting models (Sales by Channel, Receivables Aging) feeding native pivot/graph/list views |
| `demo/demo_data.xml` | 3 sample products + 4 sample customers (one is a deliberate near-duplicate, for demoing the lookup wizard) |

## Version target

Built against **Odoo 19.0** (current stable as of writing) using the modern
view syntax: `<list>` instead of `<tree>`, `invisible="expr"` instead of
`attrs`/`states`, and `ir.cron` without the deprecated `numbercall`/`doall`
fields. This syntax has been standard since Odoo 18 and should carry
forward to Odoo 20 without changes.

**If the client's server turns out to actually be running Odoo 20 beta**
(pre-release, expected ~September–October 2026): the syntax above should
still apply, but pre-release builds can have API changes that haven't
settled yet. Confirm the exact version first — see the "beta version"
question already in the proposal doc — and re-test after their production
version goes stable.

## Honest limitations — read this before the client demo

**This code has not been run against a live Odoo instance.** I don't have
one available in the environment that generated it. Every file has been:

- Python syntax-checked (`py_compile`) — all pass.
- XML well-formedness checked — all pass.
- Written against field names and APIs I'm confident are correct for
  Odoo 19 (`account_type`, `payment_state`, `amount_residual`,
  `activity_schedule`, `account.move.line.reconcile()`, etc.).

What I can't guarantee without a real install:

1. **The three `inherit_id` view references** (`sale.view_order_form`,
   `account.view_account_payment_form`, `account.view_move_form`) —
   these are long-standing, commonly-referenced IDs, but if any one of
   them doesn't match your instance, that specific view fails to install
   with a clear "element not found" error. Fix: open the relevant form in
   **Developer Mode → bug icon → Edit View: Form**, note the real
   `inherit_id`/structure, and adjust the corresponding file in `views/`.
   The rest of the module installs independently of this.
2. **The Carton/Units UoM heuristic** (`CARTON_UOM_KEYWORDS` in
   `models/sale_order.py`) is a name-matching heuristic, not a real UoM
   category check, because the actual carton-to-unit ratio hasn't been
   confirmed by the client yet (see Question H in the proposal). Demo
   products ship with the standard "Units" UoM only — add the real
   Carton UoM once you have the ratio, and the automation picks it up
   automatically, no code change needed.
3. **Payment reconciliation** (`account.payment._o2c_reconcile`) uses
   Odoo's standard `account.move.line.reconcile()` method — this is the
   same mechanism the built-in bank reconciliation widget uses, but it
   should be tested against a couple of real invoices/payments before
   you rely on it live.

## Install (on a test database first)

```bash
# from your Odoo addons path
git clone <your-repo-url> order_to_cash_automation
# restart Odoo with --update=order_to_cash_automation, or:
```

1. Copy this folder into your Odoo `addons` path.
2. Restart the Odoo service (or `--dev=all` if you're iterating).
3. Apps → Update Apps List → search "Order to Cash Automation" → Install.
4. To load the demo data (recommended before a client walkthrough):
   install on a database created with the **Demo Data** checkbox ticked,
   or run `-i order_to_cash_automation --without-demo=False`.

## Manual test checklist (do this before showing the client)

- [ ] Create a Sales Order for "Little Stars Baby Shop" with a couple of
      demo products → confirm **Order Source** shows "Online Retail".
- [ ] Click **Find / Verify Customer** on a new Sales Order, search phone
      `0333 445 5667` → confirm both "Ayesha Malik" and "Ayesha M." show
      up as matches (this is the duplicate-check demo moment).
- [ ] Confirm a Sales Order → create the Invoice → confirm **Due Date**
      populates from the customer's payment terms.
- [ ] Set an invoice's due date to yesterday (Developer Mode field edit)
      → run the **O2C: Recompute Overdue Tiers** cron manually (Settings →
      Technical → Scheduled Actions) → confirm the invoice shows
      "Overdue 1-7 Days" and an activity appears on the invoice.
- [ ] Register a payment against an invoice for the exact outstanding
      amount → click **Auto-Match Invoice** → confirm it reconciles and
      `x_needs_match_review` stays off.
- [ ] Create two open invoices for the same customer with different
      amounts, then register a payment that doesn't match either exactly
      → confirm it lands in **Payments Needing Review** instead of
      guessing.
- [ ] Open **Order to Cash → Dashboards → Sales by Channel** and
      **Receivables Aging** → confirm both pivot/graph views render.

## Pushing to your own GitHub

This folder is not yet a git repository (no credentials were available in
the environment that built it). To push it:

```bash
cd order_to_cash_automation
git init
git add .
git commit -m "Initial commit: Order to Cash Automation module"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

Then deploy from your own machine per the proposal's Phase 1 plan.
