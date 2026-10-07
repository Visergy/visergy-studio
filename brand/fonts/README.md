# Fonts

Source Sans 3 (Adobe, SIL Open Font License; see `LICENSE-SourceSans3.md`), the open-licence stand-in
for the brand typeface Myriad Pro. Static TTFs from the 3.052R release: Light, Regular, Semibold, Bold
and their italics.

`render.py` passes this folder to Typst as its only font path (system fonts are ignored), so PDFs are
identical across machines. Font names used by the templates are set in `brand/theme.toml`.
