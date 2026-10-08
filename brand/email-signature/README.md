# Email signature

- `signature.html`: the signature, between the `SIGNATURE START` and `SIGNATURE END` comments.
- `visergy-logo.png`: the logo it shows, 300 px wide and displayed at 150 px, so it stays sharp
  on high-resolution screens. Exported from `../logo.svg`. Most mail apps don't show SVG.

## 1. Host the logo

Email signatures can't carry the image inside them (most mail apps block embedded images), so
the logo has to be at a public `https://` address. `signature.html` expects:

    https://jonmorgan.au/visergy/visergy-logo.png

The logo is committed to the public `jonmorgan-site` repo at `visergy/visergy-logo.png`
(jonmorgan.au is served from it by GitHub Pages). To use another address, change the `src` in
`signature.html`. Check that the address opens in a private browser window before installing
the signature.

**Caution:** `jonmorgan-site` is generated. Each publish from the private `tech-profile` repo
replaces everything in it, which removes the logo. After each site publish, add
`visergy/visergy-logo.png` to `jonmorgan-site` again, or the logo stops showing in emails,
including ones already sent.

## 2. Install it

Open `signature.html` in a browser, select the signature (from the logo to the website link),
copy it, and paste it into your mail app.

- **Fastmail**: Settings > Signatures. Paste into the signature editor, then choose the signature
  for your Visergy sending identity.
- **Gmail**: Settings > See all settings > General > Signature. Paste, then save at the bottom of
  the page.
- **Apple Mail**: Settings > Signatures. Paste, and untick "Always match my default message font".
- **Outlook**: Settings > Mail > Compose and reply > Email signature. Paste.

Send yourself a test email and check it on your phone as well.

## Notes

- Some mail apps (Outlook especially) hide images until the recipient allows them. The logo then
  shows its alt text, "Visergy".
- The details (name, title, phone, email, website) are written in `signature.html`; edit them
  there.
