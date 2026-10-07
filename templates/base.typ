// Shared layout for every Visergy document: brand theme, page setup, cover page, back page.
// All document data arrives as JSON via sys.inputs (see render.py). Strings from that JSON are
// placed as text, never evaluated as markup.

#let theme = toml("/brand/theme.toml")

#let colours = (
  primary: rgb(theme.colours.primary),
  accent: rgb(theme.colours.accent),
  text: rgb(theme.colours.text),
  muted: rgb(theme.colours.muted),
)

#let load-data() = json(bytes(sys.inputs.at("data")))

#let logo(width: 45mm) = image("/brand/" + theme.logo.file, width: width)

#let lines(items) = items.join(linebreak())

#let label-text(body, fill: colours.muted) = text(size: 8pt, weight: "semibold", fill: fill, tracking: 0.08em, upper(body))

#let draft-mark = rotate(-35deg, text(size: 96pt, weight: "bold", fill: luma(92%))[DRAFT])

// Page setup, header and footer. `running-header: false` for one-page documents (invoices).
#let setup(data, running-header: true, body) = {
  let doc = data.doc
  set document(title: doc.title + " " + doc.reference, author: data.business.display_name)
  set page(
    paper: theme.page.paper,
    margin: (x: theme.page.margin_mm * 1mm, top: 28mm, bottom: 22mm),
    background: if doc.draft { draft-mark },
    header: if running-header {
      set text(size: 8pt, fill: colours.muted)
      grid(
        columns: (1fr, auto),
        align: (left + bottom, right + bottom),
        logo(width: 26mm), [#doc.title · #data.project.title],
      )
      v(-2mm)
      line(length: 100%, stroke: 0.5pt + colours.accent)
    },
    footer: {
      set text(size: 8pt, fill: colours.muted)
      grid(
        columns: (1fr, auto),
        [#doc.reference · #data.project.number],
        context [Page #counter(page).display() of #counter(page).final().first()],
      )
    },
  )
  set text(font: theme.fonts.body, size: 10.5pt, fill: colours.text, lang: "en", region: "AU")
  set par(leading: 0.7em, spacing: 1.1em)
  show heading: set text(font: theme.fonts.heading, fill: colours.primary, weight: "semibold")
  show heading.where(level: 1): it => {
    v(4mm)
    it
    v(1mm)
  }
  set table(stroke: 0.5pt + luma(80%), inset: 6pt)
  show figure.caption: set text(size: 9pt, fill: colours.muted)
  body
}

#let brand-image(key, width) = image("/brand/" + theme.logo.at(key), width: width)

// Width of the corner sunburst on the cover and back page; it is centred on the page corner.
#let corner-sunburst = 130mm

// Cover grid: everything lines up on these side margins. The diagonal runs from `cut-right` down
// the right edge to `cut-left` down the left edge; the back page turns it through 180 degrees.
#let cover-margin = 22mm
#let cover-width = 210mm - 2 * cover-margin
#let cut-right = 110mm
#let cut-left = 200mm
#let strip-height = 14mm

// The title, set as large as fits. Two-line titles are balanced so no word is left on its own
// line; titles that need three or more lines drop to the smallest size and wrap normally.
#let cover-title(title, width) = context {
  let style(size, body) = text(size: size, weight: "semibold", fill: white, body)
  let words = title.split(" ").filter(w => w != "")
  for size in (40pt, 32pt) {
    if measure(style(size, title)).width <= width {
      return style(size, title)
    }
    let best = none
    for i in range(1, words.len()) {
      let first = words.slice(0, i).join(" ")
      let second = words.slice(i).join(" ")
      let w = calc.max(measure(style(size, first)).width, measure(style(size, second)).width)
      if w <= width and (best == none or w < best.at(0)) { best = (w, first, second) }
    }
    if best != none {
      return par(leading: size * 0.22, style(size, best.at(1)) + linebreak() + style(size, best.at(2)))
    }
  }
  par(leading: 26pt * 0.22, style(26pt, title))
}

// Full-page cover for proposals and reports. The blue field fills the top of the page down to a
// shallow diagonal, with the white sunburst in the top-right corner as the one graphic device.
// The kicker, title and subtitle sit at the foot of the blue; the details table sits on white
// below, above a strip with the email and copyright line. The ABN is on the back page only.
// `details` is a list of (label, value) pairs; empty values are skipped.
#let cover(data, title, subtitle: none, details: ()) = page(
  header: none,
  footer: none,
  margin: 0mm,
)[
  #let b = data.business
  #let x = cover-margin
  #place(polygon(fill: colours.primary, (0mm, 0mm), (210mm, 0mm), (210mm, cut-right), (0mm, cut-left)))
  #place(top + left, dx: 210mm - corner-sunburst / 2, dy: -corner-sunburst / 2, brand-image("sunburst_white", corner-sunburst))
  #place(top + left, dx: x, dy: 24mm, brand-image("white", 64mm))

  // Bottom-anchored at 122mm, which keeps a 140mm-wide block clear of the diagonal.
  #place(bottom + left, dx: x, dy: 122mm - 297mm, block(width: 140mm)[
    #text(size: 11pt, fill: white.transparentize(25%), tracking: 0.15em, weight: "semibold", upper(data.doc.title))
    #v(5mm, weak: true)
    #cover-title(title, 140mm)
    #if subtitle not in (none, "") {
      v(8mm, weak: true)
      text(size: 18pt, fill: white.transparentize(10%), subtitle)
    }
  ])

  // Details span the full grid width, between the same margins as the title and the strip text.
  #place(bottom + left, dx: x, dy: -(strip-height + 14mm), block(width: cover-width)[
    #line(length: 100%, stroke: 0.5pt + colours.accent)
    #v(5mm, weak: true)
    #set text(size: 10pt)
    #let shown = details.filter(d => d.at(1) not in (none, ""))
    #grid(
      columns: (30mm, 1fr),
      row-gutter: 3.4mm,
      ..shown.map(d => (label-text(d.at(0)), d.at(1))).flatten()
    )
  ])

  #place(bottom + left, block(fill: colours.primary, width: 100%, height: strip-height, inset: (x: x))[
    #set text(size: 10pt, fill: white)
    #align(horizon)[#b.email #h(1fr) #text(size: 9pt, data.doc.copyright)]
  ])
]

// Closing page: the cover turned through 180 degrees. White above with the business details, the
// blue field below the diagonal with the white logo, the sunburst in the bottom-left corner and a
// thin strip at the top to pair with the cover's contact strip. Shows the name, ABN and email;
// `contact: true` adds the address and phone (off for every document since 2026-10-08).
#let back-page(data, contact: false) = page(header: none, footer: none, margin: 0mm)[
  #let b = data.business
  #place(polygon(fill: colours.primary,
    (0mm, 297mm), (210mm, 297mm), (210mm, 297mm - cut-left), (0mm, 297mm - cut-right)))
  #place(top + left, dx: -corner-sunburst / 2, dy: 297mm - corner-sunburst / 2, brand-image("sunburst_white", corner-sunburst))
  #place(top + left, rect(fill: colours.primary, width: 100%, height: strip-height))

  #place(top + left, dx: cover-margin, dy: strip-height + 18mm, block(width: 95mm)[
    #set text(size: 10pt)
    #text(weight: "semibold", fill: colours.primary, b.display_name) \
    #b.abn_label #b.abn
    #v(2mm)
    #if contact {
      lines(b.address)
      v(2mm)
    }
    #b.email
    #if contact [\ #b.phone]
  ])
  #place(bottom + right, dx: -cover-margin, dy: -24mm, brand-image("white", 64mm))
]

#let party(label, name, lines-list) = [
  #label-text(label) \
  #strong(name) \
  #lines(lines-list)
]
