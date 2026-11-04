# Payment brand logos

These are third-party trademarks, shown only to tell customers which payment
methods Kalai Safaris accepts. They are the operators' own published artwork,
with the raster files trimmed of transparent padding and resized to 96px tall.
The ZimSwitch SVG is byte-for-byte as published. Nothing else was changed.

| File | Mark | Owner | Source (downloaded 2026-11-03) |
| --- | --- | --- | --- |
| `ecocash.webp` | EcoCash wordmark, full colour | Econet Wireless Zimbabwe / EcoCash Holdings | https://www.econet.co.zw/wp-content/uploads/2025/06/Ecocash-Logo.png |
| `omari-white.webp` | Omari wordmark, reversed (white) | Old Mutual Zimbabwe (Omari) | https://www.omari.co.zw/images/logowhite.webp |
| `zimswitch.svg` | ZimSwitch logo, yellow badge (vector, unmodified) | Zimswitch Technologies | https://zimswitch.co.zw/wp-content/themes/zimswitch/assets/images/logo.svg |
| `visa.webp` | Visa brandmark, Visa Blue (downloaded 2026-11-04; artwork already edge-to-edge, so only resized) | Visa Inc. | https://usa.visa.com/dam/VCOM/global/about-visa/images/visa-brandmark-blue-1960x622.png |

Only ZimSwitch publishes a vector file, and none of the three publishes a public brand guide. When the
operators send merchant artwork (ideally SVG), replace these files with it.

**Mastercard:** not added yet. Mastercard's sites refuse automated downloads, so
the footer and card picker still show an icon-font placeholder. Drop the official
artwork (ideally the SVG symbol from Mastercard's brand centre) in here as
`mastercard.svg`, add it to `MARKS` and `PAYMENT_LOGO_ORDER` in
`src/components/PaymentLogo.tsx`, and remove the placeholder `FaCcMastercard`.

**Order:** EcoCash, Omari, ZimSwitch, then InnBucks (once live), then Visa and
Mastercard — set once in `PAYMENT_LOGO_ORDER`.

## Usage rules (until the operators send their own)

- Don't recolour, stretch, crop, outline or add effects to the artwork.
- EcoCash and Visa sit on white (`#FFFFFF`): a white chip on dark surfaces, or directly
  on a white or near-white surface. Omari's white wordmark always sits on Omari
  green (`#1A9C68`, sampled from the official full-colour logo).
- ZimSwitch's artwork carries its own yellow plate, so it gets no extra backing.
- Keep clear space of at least half the logo height on every side (the badge
  padding in `src/components/PaymentLogo.tsx` handles this).
- Target logo height is 14 to 16px. In narrow containers it may scale down,
  but it must never be distorted.
- Use the marks only next to the payment option they stand for. Don't use
  them as decoration or to suggest a partnership or endorsement.

Use them through `<PaymentLogo />`, not as raw `<img>` tags, so these rules
stay in one place.
