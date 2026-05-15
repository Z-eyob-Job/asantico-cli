---
name: asantico-invoice-formatter
description: Use this skill whenever generating, validating, or modifying any Asantico invoice or estimate content, including PDF text, sample JSON line items, email copy referencing a document, line-item descriptions, payment terms, or validity statements. Trigger this skill any time a value or string in this project relates to invoice numbering, estimate numbering, currency formatting, property names, Seattle sales tax, or document footers. Use this skill BEFORE writing test fixtures with realistic line items, BEFORE generating any PDF, and BEFORE drafting any prose that will be embedded in an invoice or estimate or in correspondence about one.
---

# Asantico Invoice Formatter

## Purpose

A single source of truth for the formatting and content rules that govern every Asantico invoice and estimate. Apply these rules silently and consistently. If a rule conflicts with a request from the user, surface the conflict in plain language before proceeding.

## Hard rules

1. **Seattle sales tax is 10.55%** and applies per line item, labor included. Never apply the rate once at the subtotal level.
2. **Per-line tax math**: line_tax = line_total * Decimal("0.1055"). Use Decimal throughout. Round with ROUND_HALF_UP to two decimal places only at the final display step.
3. **Currency display**: $1,234.56. Always two decimal places, comma thousand separators, leading dollar sign. Never 1234.5, never USD 1234.56, never $1234.5.
4. **No em dashes anywhere**. The em dash (Unicode U+2014) is banned in all generated content: PDF text, code comments, docstrings, error messages, README copy, sample JSON, commit messages. Use commas, semicolons, parentheses, or periods.
5. **Document numbering**: invoices use INV-0001 format (four-digit zero-padded), estimates use EST-0001. Counters are stored per type in ~/.asantico/counters.json and increment after each successful generation.
6. **Filename pattern**: {type}_{property-slug}_{YYYY-MM-DD}.pdf. Slug rule: lowercase, replace any run of non-alphanumeric characters with a single hyphen, trim leading and trailing hyphens.

## Recipient block

All Sprint 1 documents bill to Avenue One Residential, Attn: Andrew Miller or Saniya Zaveri depending on the property.

Andrew receives Garden, The Meridian, Portal, Aprea View. Saniya receives Gilman's Fairway, Linden Avenue Condominiums, Canterbury Shores, Koda Condominiums, Clark Roadhouse. When in doubt, default to Andrew.

## Line item conventions

- Description: concise, action-led. Good: "Replace bathroom faucet, primary unit". Bad: "Replaced the bathroom faucet that was leaking which the tenant reported last week, primary unit upstairs."
- Unit values: only hr, each, or flat. Reject anything else with a validation error.
- Quantity: positive Decimal. Reject zero and negative values.
- Unit price: positive Decimal in USD.
- No marketing language: avoid "premium", "high quality", "professional grade". State what was done.

## Document footer copy

Invoice footer (use verbatim, edit only the net term if specified):

    Payment terms: Net 30. Make checks payable to Asantico, Seattle WA.
    Questions: contact Asantico directly.

Estimate footer (use verbatim):

    This estimate is valid for 30 days from the date issued. Pricing reflects work scope as described and may be revised if scope changes.

## Sample JSON shape for line items

When generating test fixtures or example files, follow this exact shape:

    {
      "line_items": [
        {
          "description": "Replace garbage disposal, unit 204",
          "quantity": 1,
          "unit": "each",
          "unit_price": 285.00
        },
        {
          "description": "Plumbing labor, kitchen",
          "quantity": 2.5,
          "unit": "hr",
          "unit_price": 95.00
        }
      ],
      "notes": "Optional free-text notes for the document footer."
    }

Use realistic Avenue One property names for fixtures: Garden, The Meridian, Portal, Aprea View, Gilman's Fairway, Linden Avenue Condominiums, Canterbury Shores, Koda Condominiums, Clark Roadhouse.

## Email and correspondence copy

When drafting any email or message that references a generated invoice or estimate:

- Keep it under 80 words.
- State the property, the scope, and that the document is attached.
- Do not include line-item pricing or totals in the email body.
- Address Andrew or Saniya per the routing rule above.
- No em dashes. No marketing language.

Example email body for an invoice on The Meridian:

    Hi Andrew,

    Invoice attached for work completed at The Meridian, scope per the
    attached PDF. Please let me know if anything needs adjustment.

    Thanks,
    Stark

## When this skill applies vs when it does not

Apply this skill for: PDF text, line item descriptions, sample JSON fixtures, document footers, filenames, currency formatting, email copy about an invoice or estimate, error messages that reference money or documents.

Do NOT apply this skill for: pytest fixtures unrelated to documents, README sections that describe the project at a high level rather than embedding document copy, Spec Kit slash commands (they have their own templates).

## Validation checklist before emitting any document content

- [ ] No em dashes in the output
- [ ] All currency values formatted as $1,234.56
- [ ] Tax math is per-line, not subtotal-level
- [ ] Document number follows INV-#### or EST-####
- [ ] Filename follows {type}_{slug}_{YYYY-MM-DD}.pdf
- [ ] Recipient routed correctly (Andrew vs Saniya)
- [ ] Footer matches invoice vs estimate variant exactly
- [ ] Line item units are hr, each, or flat
- [ ] No marketing adjectives in line item descriptions
