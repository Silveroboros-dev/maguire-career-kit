# Export a CV or application document

Use an existing candidate-approved CV as the design reference by default. Do not
make the candidate ask again for its typography and layout to be reused. Preserve
the original CV and selected editable master. Exports are fresh derivatives in the
role's draft package; they do not replace the master or imply approval or sending.

## Prepare the design and the employer-facing content

1. Read the CV index and identify the original design reference and the approved
   editable master. Look at the supplied original's actual pages, including a PDF
   render or the document preview. Extract page size, margins, fonts, heading
   hierarchy, paragraph and bullet spacing, date alignment, links, and page breaks.
   Preserve the existing design unless the candidate requests a change or a
   material readability problem needs their decision. If no reference exists,
   use the neutral fallback below and say so.
2. Prepare a clean employer-facing Markdown derivative, for example
   `applications/APP-001/drafts/cv-content.md`, from approved claims. The kit's
   `drafts/cv.md` template is a **review record**, containing internal metadata,
   evidence maps and open questions. Do not export that record as a CV. Keep
   internal notes, review status, unsupported claims, Markdown template prompts,
   and claim-to-evidence maps out of the employer-facing content. Read the clean
   content before converting it.
3. If the reference is DOCX, use its paragraph/character styles and page settings
   with `--reference-doc`. The helper creates a private rendering copy and adds
   any missing Pandoc paragraph/character styles, such as `Compact`, so lists
   render correctly with an ordinary Word CV. Existing styles and page settings
   retain priority; the original reference is never edited. If it is PDF or an image, inspect it visually and create
   a separate reusable `reference.docx` matching those settings with the local
   document editor or an available document authoring tool. Record that derived
   reference and its relationship to the original in the CV index or role notes.
   A PDF is not a Pandoc reference document. Never rename a PDF to DOCX or send it
   to `--reference-doc`.
4. Pandoc copies DOCX **styles and page settings**, not the reference document's
   body content or arbitrary layout. A two-column design, text boxes, tables,
   headers, or manually positioned dates may need a native DOCX derivative and
   local-editor export instead. Do not promise an exact design clone from a
   reference flag. Keep the same preservation and review steps for that route.

## Check the local renderers

The Python wrapper has no Python-package dependencies. It uses local **Pandoc**
for DOCX and **LibreOffice** (`soffice` or `libreoffice` on `PATH`) to export that
DOCX to PDF. This keeps the two formats based on the same styles. It does not
install software or connect a cloud conversion service.

From the career workspace:

```sh
python3 .maguire/kit/tools/export.py --check
python3 .maguire/kit/tools/export.py --check --format docx
```

The JSON reports the executable paths, missing tools, and `ready`; a missing
required renderer returns exit code 2. First reuse any suitable native document
tool or already licensed editor available in the environment without a new
purchase. If no suitable route is available, install the missing free converters
as part of the requested export task using the environment's existing permissions.
A paid subscription is not required, and a missing converter is a setup step
rather than a reason to hand the candidate an unfinished export immediately.

### Install the free fallback when needed

Detect the OS and an available package manager, check existing installations,
then run only the commands for missing components on that platform:

| Platform | Pandoc for DOCX | LibreOffice for PDF |
| --- | --- | --- |
| macOS with Homebrew | `brew install pandoc` | `brew install --cask libreoffice` |
| Debian/Ubuntu | `apt-get install -y pandoc` | `apt-get install -y libreoffice-writer` |
| Windows with winget | `winget install --id JohnMacFarlane.Pandoc --exact` | `winget install --id TheDocumentFoundation.LibreOffice --exact` |

For Debian/Ubuntu, use the environment's authorized administrator route when
needed and refresh package metadata with `apt-get update` if necessary. For
winget, verify the exact package ID with `winget show --id ID --exact` before
installing; restart the export process with the updated executable path if the
current shell does not see the installation. For other systems, use their
available package manager or the official [Pandoc installation guide](https://pandoc.org/installing.html)
and [LibreOffice downloads](https://www.libreoffice.org/download/download-libreoffice/).
The [Homebrew Pandoc](https://formulae.brew.sh/formula/pandoc) and
[LibreOffice](https://formulae.brew.sh/cask/libreoffice) entries document the macOS
commands above. Install only Pandoc when DOCX alone is requested.

The helper finds executables through `PATH`. Before installing again, check an
existing LibreOffice app at `/Applications/LibreOffice.app/Contents/MacOS/soffice`
on macOS or `C:\Program Files\LibreOffice\program\soffice.exe` on Windows (also
check the user's chosen install location). Add its executable directory to
`PATH` for the export process only; preserve global shell configuration.

After setup, rerun `--check`, export a small synthetic Markdown sample to fresh
temporary outputs and inspect its text and rendered pages. Then export the
candidate's clean content with the selected design reference. Record the tools
actually used. The Python helper and kit installer do not install software;
the agent carries out these setup instructions when needed.

If an unavailable permission, network connection, or package manager actually
blocks installation, state the specific blocker and retain the clean Markdown
and design-reference instructions. Do not require a paid service to continue.
Report what is available and what remains to be exported; do not call a Markdown
file a PDF or claim a conversion was performed when it was not.

## Export fresh files

Use a new output directory for each revised version. Quote paths with spaces:

```sh
python3 .maguire/kit/tools/export.py applications/APP-001/drafts/cv-content.md --reference-doc originals/reference.docx --output-dir applications/APP-001/drafts/export-v1
```

By default this creates `cv-content.docx`, `cv-content.pdf`, and
`cv-content.export.json`. `--format docx` or `--format pdf` exports only the named
format and the receipt. PDF-only mode uses an intermediate DOCX without publishing
it. Existing output files are never overwritten; source/reference/output symlink
paths are refused. Conversion is staged in a temporary destination folder with
an isolated LibreOffice profile, and exports are published only after every
requested conversion succeeds. If publication fails partway, this invocation's
published files are removed; pre-existing files are preserved.

Omitting `--reference-doc` produces a neutral A4 design with 20 mm margins,
10.5-point Arial body text, restrained blue headings, consistent spacing, and
headings kept with the following paragraph. It is a fallback, not a reconstruction
of an existing CV. Check the actual installed fonts: a renderer may substitute a
missing font, including fonts used by a supplied reference.

The receipt binds source, original reference, and output bytes with SHA-256,
records any added compatibility styles and the effective rendering reference
hash, records the backends, and leaves `content`, `layout`, and `candidate` review `pending`. For the
fallback it records `neutral-v1` and the generated reference hash. It does not
prove that the text is correct, the design matches, a human reviewed it, or the
document was sent. Keep any later review result separately in the role notes;
the export receipt describes the original conversion.

## Inspect the result before handoff

- Render **every PDF page** to images or use a document preview. For example, if
  Poppler is installed: `pdftoppm -png -r 110 PATH.pdf PREVIEW_PREFIX`. Open the
  images. Compare with the reference: margins, headings, dates, bullets, whitespace,
  page count, orphan headings, split role descriptions, clipping and overlap.
- Extract PDF text with an available tool such as `pdftotext -layout PATH.pdf -`
  and compare names, contacts, links, dates, numbers, Unicode characters and body
  content with the approved Markdown. Check links and ensure internal notes or
  evidence maps did not leak. Text extraction alone does not verify visual layout.
- Open DOCX in the intended editor when possible, especially when it is the
  required delivery format. A PDF preview cannot prove that every Word client
  will paginate DOCX identically.
- If anything is wrong, correct the clean Markdown/reference derivative, export
  to a fresh version folder, and inspect again. Keep previous reviewed or sent
  versions intact. Record the source/export relationship in the existing CV index.
- Hand over the actual PDF/DOCX paths with what was inspected and any unresolved
  limits. A successful conversion does not mark the application reviewed, ready,
  or submitted. The candidate controls approval and sending.

In a cloud agent with no local renderers or durable filesystem, use the available
document tool and return named downloadable files, or state the missing capability
and return the clean Markdown plus reference instructions for local export. Check
where the candidate can retain the artifacts; do not imply cloud Git or temporary
files are storage on their own computer.
