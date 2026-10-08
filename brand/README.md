# Brand assets

Everything that makes a Visergy document look like Visergy. The Typst templates in `templates/` read
from here; nothing in this folder is sensitive.

- `theme.toml`: colours, font names, logo file names, page size and margins.
- `logo.svg`, `logo-white.svg`: the wordmark in turquoise and white.
- `sunburst.svg`, `sunburst-white.svg`: the radial-lines graphic, used cropped off the page edge
  on the cover and back page (as on the business card).
- `sunburst-thin-white.svg`, `sunburst-thin-turquoise.svg`: the same rays redrawn as fine lines,
  for the "field" cover style.
  Generated from `sunburst-white.svg` by `make_thin_sunburst.py` (keeps each ray's angle and
  length); re-run it if the artwork changes.
- `email-signature/`: the HTML email signature and its logo PNG (see the README there).
- `fonts/`: Source Sans 3 (SIL Open Font License, see `fonts/LICENSE-SourceSans3.md`).

## Where these came from

The originals are in the Nextcloud brand folder (`Work/Visergy/Admin/Brand/OneDegree/`), as EPS
files from the 2015 brand work. The SVGs were converted from those EPS files:

```
epstopdf --outfile=logo.pdf Visergy_logo_turquoise.eps
pdftocairo -svg logo.pdf logo.svg
```

Colours: `accent` is the logo turquoise from the EPS (RGB 0, 171, 191). `primary` is the blue on
the printed business card (`VISERGY_Business_Card_01.pdf`), sampled from the PDF.

Font: the brand typeface is Myriad Pro, which is commercially licensed and can't be committed.
Source Sans 3 is Adobe's open-licence face in the same humanist style. If you hold a Myriad Pro
licence for embedding, put the font files in `fonts/` (gitignored is safer) and change
`theme.toml`.
