# Payment brand logos

These are third-party trademarks, shown only to tell customers which payment
methods Kalai Safaris accepts. They are the operators' own published artwork,
with the raster files trimmed of transparent padding and resized to 96px tall.
The ZimSwitch SVG is byte-for-byte as published. Nothing else was changed.

| File | Mark | Owner | Source (downloaded 2026-11-03) |
| --- | --- | --- | --- |
| `ecocash.webp` | EcoCash wordmark, full colour | Econet Wireless Zimbabwe / EcoCash Holdings | https://www.econet.co.zw/wp-content/uploads/2025/06/Ecocash-Logo.png |
| `omari.webp` | Omari wordmark, full colour (supplied by Kalai Safaris, 2026-11-04; cut from the 2048px logo sheet: neutral background and the "A member of the Old Mutual group" line removed, wordmark unchanged) | Old Mutual Zimbabwe (Omari) | Client-supplied official artwork |
| `zimswitch.svg` | ZimSwitch logo, yellow badge (vector, unmodified) | Zimswitch Technologies | https://zimswitch.co.zw/wp-content/themes/zimswitch/assets/images/logo.svg |
| `mastercard.webp` | Mastercard symbol (supplied by Kalai Safaris, 2026-11-04; cut from its light-grey square, resized to 96px tall, colours unchanged) | Mastercard | Client-supplied official artwork |
| `visa.webp` | Visa brandmark, Visa Blue (downloaded 2026-11-04; artwork already edge-to-edge, so only resized) | Visa Inc. | https://usa.visa.com/dam/VCOM/global/about-visa/images/visa-brandmark-blue-1960x622.png |

Only ZimSwitch publishes a vector file, and none of the three publishes a public brand guide. When the
operators send merchant artwork (ideally SVG), replace these files with it.

**Order:** EcoCash, Omari, ZimSwitch, then InnBucks (once live), then Visa and
Mastercard — set once in `PAYMENT_LOGO_ORDER`.

## Usage rules (until the operators send their own)

- Don't recolour, stretch, crop, outline or add effects to the artwork.
- EcoCash, Omari, Visa and Mastercard sit on white (`#FFFFFF`): a white chip on dark
  surfaces, or directly on a white or near-white surface.
- ZimSwitch's artwork carries its own yellow plate, so it gets no extra backing.
- Keep clear space of at least half the logo height on every side (the badge
  padding in `src/components/PaymentLogo.tsx` handles this).
- Target logo height is 14 to 16px. In narrow containers it may scale down,
  but it must never be distorted.
- Use the marks only next to the payment option they stand for. Don't use
  them as decoration or to suggest a partnership or endorsement.

Use them through `<PaymentLogo />`, not as raw `<img>` tags, so these rules
stay in one place.
