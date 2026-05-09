# Fonts

We don't currently ship local font files. Verkstad type loads from Google Fonts:

```css
@import url("https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500&display=swap");
```

## Substitution flag

Söhne (Klim Type Foundry) is the canonical Verkstad type. It is a paid license and is not redistributable, so this system substitutes **Geist** (similar grotesque, modern, free under SIL OFL) until the licensed Söhne `.woff2` files are dropped here.

When that happens:

1. Drop `Söhne-Buch.woff2`, `Söhne-Kräftig.woff2`, `Söhne-Halbfett.woff2`, `SöhneMono-Buch.woff2` into this folder.
2. Replace the `@import` in `colors_and_type.css` with `@font-face` blocks pointing at those files.
3. Update `--font-display`, `--font-body`, `--font-mono` to lead with `"Söhne"`.
