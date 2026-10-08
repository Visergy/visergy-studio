// Report: cover, document control, contents, Markdown body, back page.
// The Markdown arrives as a string in the JSON and is rendered by cmarker with raw-typst off,
// so nothing in the report text can run as Typst code. Images were copied to /report/ by render.py.
#import "@preview/cmarker:0.1.10"
#import "base.typ": *

#let data = load-data()
#let r = data.report
#show: setup.with(data)

#cover(data, r.title, subtitle: r.subtitle, details: (
  ("Client", data.client.name),
  ("Attention", if data.contact != none { data.contact.name }),
  ("Project", data.project.number + " · " + data.project.title),
  ("Reference", r.number + " · Rev " + r.revision),
  ("Date", data.doc.date),
))

#heading(level: 1, outlined: false)[Document control]
#table(
  columns: (auto, auto, 1fr),
  table.header(label-text("Revision"), label-text("Date"), label-text("Description")),
  ..r.history.map(h => (h.revision, h.date, h.description)).flatten(),
)

#if r.toc {
  v(8mm)
  outline(title: [Contents], depth: 2)
}
#pagebreak()

#set heading(numbering: "1.1")
#cmarker.render(
  r.body,
  raw-typst: false,
  scope: (
    image: (path, alt: none) => figure(
      image("/report/" + path),
      caption: if alt in (none, "") { none } else { alt },
    ),
  ),
)

#back-page(data)
