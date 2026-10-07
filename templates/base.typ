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

#let label-text(body, fill: colours.muted) = text(size: 8pt, fill: fill, tracking: 0.08em, upper(body))

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

// Full-page cover. The blue field fills the top of the page down to a shallow diagonal, with a
// translucent turquoise band of even depth along the cut; a small white sunburst sits in the
// top-right corner. Title on blue, details on white at the lower right, contact strip at the
// foot. `details` is a list of (label, value) pairs; empty values are skipped.
#let cover(data, title, subtitle: none, details: ()) = page(
  header: none,
  footer: none,
  margin: 0mm,
)[
  #let b = data.business
  #let faint = white.transparentize(30%)
  #let band = 20mm
  // Diagonal from 110mm down the right edge to 200mm down the left edge.
  #place(polygon(
    fill: colours.accent.transparentize(35%),
    (0mm, 0mm), (210mm, 0mm), (210mm, 110mm + band), (0mm, 200mm + band),
  ))
  #place(polygon(fill: colours.primary, (0mm, 0mm), (210mm, 0mm), (210mm, 110mm), (0mm, 200mm)))
  #place(top + left, dx: 210mm - corner-sunburst / 2, dy: -corner-sunburst / 2, brand-image("sunburst_white", corner-sunburst))
  #place(top + left, dx: 22mm, dy: 24mm, brand-image("white", 64mm))

  // Long titles drop a size so they stay on the blue.
  #let title-size = if title.len() > 45 { 26pt } else { 32pt }
  #place(top + left, dx: 22mm, dy: 70mm, block(width: 130mm, stack(
    spacing: 4mm,
    text(size: 11pt, fill: faint, tracking: 0.15em, weight: "semibold", upper(data.doc.title)),
    par(leading: title-size * 0.3, text(size: title-size, weight: "semibold", fill: white, title)),
    ..if subtitle not in (none, "") { (text(size: 16pt, weight: "light", fill: faint, subtitle),) },
  )))

  #place(bottom + right, dx: -22mm, dy: -28mm, block(width: 95mm)[
    #set text(size: 9.5pt)
    #set align(left)
    #let shown = details.filter(d => d.at(1) not in (none, ""))
    #grid(
      columns: (24mm, 1fr),
      row-gutter: 3.2mm,
      ..shown.map(d => (label-text(d.at(0)), d.at(1))).flatten()
    )
  ])

  #place(bottom + left, block(fill: colours.primary, width: 100%, height: 12mm, inset: (x: 22mm))[
    #set text(size: 9pt, fill: white)
    #align(horizon)[#b.email #h(8mm) #b.phone #h(1fr) #b.abn_label #b.abn]
  ])
]

// Closing page: the cover turned through 180 degrees. White above, the blue field below a
// diagonal with the translucent band on its upper side, the small sunburst in the bottom-left
// corner, a thin strip at the top, business details on white and the white logo on blue.
#let back-page(data) = page(header: none, footer: none, margin: 0mm)[
  #let b = data.business
  #let band = 20mm
  // The cover's cut, rotated: 187mm down the left edge up to 97mm down the right edge.
  #place(polygon(
    fill: colours.accent.transparentize(35%),
    (0mm, 297mm), (210mm, 297mm), (210mm, 97mm - band), (0mm, 187mm - band),
  ))
  #place(polygon(fill: colours.primary, (0mm, 297mm), (210mm, 297mm), (210mm, 97mm), (0mm, 187mm)))
  #place(top + left, dx: -corner-sunburst / 2, dy: 297mm - corner-sunburst / 2, brand-image("sunburst_white", corner-sunburst))
  #place(top + left, rect(fill: colours.primary, width: 100%, height: 12mm))

  // Mirrors the cover: details on white at the upper left, the logo alone on blue at the lower right.
  #place(top + left, dx: 22mm, dy: 30mm, block(width: 95mm)[
    #set text(size: 9.5pt)
    #text(weight: "semibold", fill: colours.primary, b.display_name) \
    #if b.trading_as != "" and b.trading_as != b.name [#b.name trading as #b.trading_as \ ]
    #b.abn_label #b.abn
    #v(2mm)
    #lines(b.address)
    #v(2mm)
    #b.email \
    #b.phone
  ])
  #place(bottom + right, dx: -22mm, dy: -24mm, brand-image("white", 64mm))
]

#let party(label, name, lines-list) = [
  #label-text(label) \
  #strong(name) \
  #lines(lines-list)
]
