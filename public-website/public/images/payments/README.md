# Payment operator logos

These are third-party trademarks, shown only to tell customers which payment
methods Kalai Safaris accepts. They are the operators' own published artwork,
trimmed of transparent padding and resized to 96px tall. Nothing else was changed.

| File | Mark | Owner | Source (downloaded 2026-11-03) |
| --- | --- | --- | --- |
| `ecocash.webp` | EcoCash wordmark, full colour | Econet Wireless Zimbabwe / EcoCash Holdings | https://www.econet.co.zw/wp-content/uploads/2025/06/Ecocash-Logo.png |
| `omari-white.webp` | Omari wordmark, reversed (white) | Old Mutual Zimbabwe (Omari) | https://www.omari.co.zw/images/logowhite.webp |

Neither operator publishes a vector file or a public brand guide. When the
operators send merchant artwork (ideally SVG), replace these files with it.

## Usage rules (until the operators send their own)

- Don't recolour, stretch, crop, outline or add effects to the artwork.
- EcoCash sits on white (`#FFFFFF`): a white chip on dark surfaces, or directly
  on a white or near-white surface. Omari's white wordmark always sits on Omari
  green (`#1A9C68`, sampled from the official full-colour logo).
- Keep clear space of at least half the logo height on every side (the badge
  padding in `src/components/MobileMoneyLogo.tsx` handles this).
- Target logo height is 14 to 16px. In narrow containers it may scale down,
  but it must never be distorted.
- Use the marks only next to the payment option they stand for. Don't use
  them as decoration or to suggest a partnership or endorsement.

Use them through `<MobileMoneyLogo />`, not as raw `<img>` tags, so these rules
stay in one place.
