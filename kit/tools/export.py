#!/usr/bin/env python3
"""Export a Markdown draft to fresh DOCX/PDF derivatives using local tools.

Python standard library only; rendering requires Pandoc and, for PDF, LibreOffice.
Existing files are never overwritten. The receipt records bytes, not approval.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from xml.dom import minidom
import xml.etree.ElementTree as ET
import zipfile


WORD = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
ET.register_namespace("w", WORD)


def w(name: str) -> str:
    return "{" + WORD + "}" + name


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_path(value: Path) -> Path:
    """Resolve only after rejecting symlinks in the supplied path and parents."""
    path = value.expanduser().absolute()
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError(f"Symlink paths are not supported: {part}")
    return path.resolve()


def capabilities(output_format: str) -> dict:
    pandoc = shutil.which("pandoc")
    office = shutil.which("soffice") or shutil.which("libreoffice")
    missing = []
    if not pandoc:
        missing.append("Pandoc (pandoc)")
    if output_format in ("pdf", "both") and not office:
        missing.append("LibreOffice (soffice or libreoffice)")
    return {"format": output_format, "pandoc": pandoc, "libreoffice": office,
            "ready": not missing, "missing": missing}


def run(command: list[str]) -> bytes:
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                check=False, timeout=120)
    except subprocess.TimeoutExpired as error:
        raise ValueError(f"{Path(command[0]).name} exceeded the 120-second conversion limit") from error
    if result.returncode:
        # Renderer diagnostics can quote candidate text. Keep them in the local
        # caller's error, bounded; never claim that a failed render succeeded.
        detail = result.stderr.decode("utf-8", errors="replace").strip()[-2000:]
        raise ValueError(f"{Path(command[0]).name} failed ({result.returncode}): {detail}")
    return result.stdout


def child(parent: ET.Element, name: str, **attributes: str) -> ET.Element:
    node = parent.find(w(name))
    if node is None:
        node = ET.SubElement(parent, w(name))
    for key, value in attributes.items():
        node.set(w(key), value)
    # Theme fonts/colors override the explicit choices in Word and LibreOffice.
    if name == "rFonts" and attributes:
        for key in list(node.attrib):
            if key.rsplit("}", 1)[-1].lower().endswith("theme"):
                del node.attrib[key]
    if name == "color" and "val" in attributes:
        for key in ("themeColor", "themeTint", "themeShade"):
            node.attrib.pop(w(key), None)
    return node


def order_properties(style: ET.Element) -> None:
    """Keep modified OOXML properties in schema order, including new nodes."""
    sequences = {
        "pPr": "pStyle keepNext keepLines pageBreakBefore framePr widowControl numPr suppressLineNumbers pBdr shd tabs suppressAutoHyphens kinsoku wordWrap overflowPunct topLinePunct autoSpaceDE autoSpaceDN bidi adjustRightInd snapToGrid spacing ind contextualSpacing mirrorIndents suppressOverlap jc textDirection textAlignment textboxTightWrap outlineLvl divId cnfStyle rPr sectPr pPrChange",
        "rPr": "rStyle rFonts b bCs i iCs caps smallCaps strike dstrike outline shadow emboss imprint noProof snapToGrid vanish webHidden color spacing w kern position sz szCs highlight u effect bdr shd fitText vertAlign rtl cs em lang eastAsianLayout specVanish oMath rPrChange",
    }
    for name, sequence in sequences.items():
        node = style.find(w(name))
        if node is not None:
            order = {w(item): index for index, item in enumerate(sequence.split())}
            node[:] = sorted(node, key=lambda item: order.get(item.tag, len(order)))
    para = style.find(w("pPr"))
    run_properties = style.find(w("rPr"))
    if para is not None and run_properties is not None:
        style.remove(para)
        style.insert(list(style).index(run_properties), para)


def neutral_reference(pandoc: str, target: Path) -> None:
    """A plain, consistent fallback; candidate reference styles take precedence."""
    original = run([pandoc, "--print-default-data-file=reference.docx"])
    with zipfile.ZipFile(io.BytesIO(original)) as archive:
        files = {item.filename: archive.read(item) for item in archive.infolist()}
    root = ET.fromstring(files["word/styles.xml"])
    defaults = child(child(root, "docDefaults"), "rPrDefault")
    properties = child(defaults, "rPr")
    child(properties, "rFonts", ascii="Arial", hAnsi="Arial", cs="Arial")
    child(properties, "sz", val="21")
    child(properties, "szCs", val="21")
    styles = {node.get(w("styleId")): node for node in root.findall(w("style"))}
    for name in ("Normal", "BodyText", "FirstParagraph", "Compact"):
        if name not in styles:
            continue
        style = styles[name]
        props = child(style, "rPr")
        child(props, "rFonts", ascii="Arial", hAnsi="Arial", cs="Arial")
        child(props, "sz", val="21")
        child(props, "szCs", val="21")
        para = child(style, "pPr")
        child(para, "spacing", after="80", line="240", lineRule="auto")
        child(para, "widowControl")
    for name, size in (("Title", "38"), ("Heading1", "25"),
                       ("Heading2", "22"), ("Heading3", "21")):
        if name not in styles:
            continue
        style = styles[name]
        props = child(style, "rPr")
        child(props, "rFonts", ascii="Arial", hAnsi="Arial", cs="Arial")
        child(props, "sz", val=size)
        child(props, "szCs", val=size)
        child(props, "color", val="173B56")
        child(props, "b")
        para = child(style, "pPr")
        child(para, "keepNext")
        child(para, "spacing", before="180", after="80")
    for style in styles.values():
        order_properties(style)
    files["word/styles.xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    document = ET.fromstring(files["word/document.xml"])
    section = document.find(".//" + w("sectPr"))
    if section is None:
        raise ValueError("Pandoc default reference has no page settings")
    child(section, "pgSz", w="11906", h="16838")  # A4
    child(section, "pgMar", top="1134", bottom="1134", left="1134", right="1134")
    files["word/document.xml"] = ET.tostring(document, encoding="utf-8", xml_declaration=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, contents in files.items():
            archive.writestr(name, contents)


def complete_reference(pandoc: str, source: Path, target: Path) -> list[str]:
    """Add only missing Pandoc styles to a private copy of an ordinary Word CV.

    LibreOffice can drop list markers when Pandoc's Compact paragraph style is
    absent, even with correct numbering. Existing reference styles take priority.
    DOM preserves the source's namespace declarations, including mc:Ignorable
    prefix bindings that ElementTree would otherwise discard on serialization.
    """
    default_bytes = run([pandoc, "--print-default-data-file=reference.docx"])
    with zipfile.ZipFile(io.BytesIO(default_bytes)) as defaults:
        default_styles = minidom.parseString(defaults.read("word/styles.xml"))
    with zipfile.ZipFile(source) as original:
        styles = minidom.parseString(original.read("word/styles.xml"))
        binding = styles.documentElement.getAttribute("xmlns:w")
        if binding and binding != WORD:
            raise ValueError("Reference uses a conflicting xmlns:w binding; save a compatible DOCX reference in a document editor")
        # Pandoc also appends its own w:style siblings (e.g. SourceCode), outside
        # the imported subtrees. Give those nodes a document-level binding.
        if not binding:
            styles.documentElement.setAttribute("xmlns:w", WORD)
        existing = {node.getAttributeNS(WORD, "styleId")
                    for node in styles.getElementsByTagNameNS(WORD, "style")}
        added = []
        for node in default_styles.getElementsByTagNameNS(WORD, "style"):
            style_id = node.getAttributeNS(WORD, "styleId")
            if style_id not in existing:
                imported = styles.importNode(node, deep=True)
                # The original may bind WORD to a different prefix (e.g. x).
                # Imported nodes need their own default-reference bindings.
                for name, value in default_styles.documentElement.attributes.items():
                    if name == "xmlns" or name.startswith("xmlns:"):
                        imported.setAttribute(name, value)
                styles.documentElement.appendChild(imported)
                added.append(style_id)
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as completed:
            for entry in original.infolist():
                contents = (styles.toxml(encoding="utf-8") if entry.filename == "word/styles.xml"
                            else original.read(entry))
                completed.writestr(entry.filename, contents)
    default_styles.unlink()
    styles.unlink()
    return added


def validate_docx(path: Path) -> None:
    try:
        with zipfile.ZipFile(path) as archive:
            # A DOCX structure check is not a layout or semantic content review.
            for name in ("[Content_Types].xml", "word/document.xml", "word/styles.xml"):
                ET.fromstring(archive.read(name))
    except (OSError, KeyError, zipfile.BadZipFile, ET.ParseError) as error:
        raise ValueError(f"Invalid DOCX: {path.name}: {error}") from error


def file_record(path: Path) -> dict:
    return {"path": str(path), "sha256": sha256(path), "bytes": path.stat().st_size}


def export(source_value: Path, directory_value: Path, reference_value: Path | None,
           output_format: str) -> dict:
    source = checked_path(source_value)
    directory = checked_path(directory_value)
    reference = checked_path(reference_value) if reference_value else None
    if not source.is_file() or source.suffix.lower() not in (".md", ".markdown"):
        raise ValueError("Source must be an existing Markdown (.md or .markdown) file")
    if not source.read_bytes().strip():
        raise ValueError("Source Markdown is empty")
    if directory.exists() and not directory.is_dir():
        raise ValueError("Output directory is not a directory")
    if reference:
        if not reference.is_file() or reference.suffix.lower() != ".docx":
            raise ValueError("--reference-doc requires a DOCX file; inspect a PDF reference visually first")
        validate_docx(reference)
    formats = ("docx", "pdf") if output_format == "both" else (output_format,)
    targets = [directory / (source.stem + "." + item) for item in formats]
    receipt_target = directory / (source.stem + ".export.json")
    for target in (*targets, receipt_target):
        checked_path(target)
        if target.exists():
            raise ValueError(f"Refusing to overwrite existing file: {target}; choose a fresh output directory")
        if target == source or target == reference:
            raise ValueError("Export must not replace the source or reference")
    tools = capabilities(output_format)
    if not tools["ready"]:
        raise ValueError("Missing local rendering tools: " + ", ".join(tools["missing"]) +
                         ". Install them using your computer's normal package manager; then rerun --check.")
    source_record = file_record(source)
    reference_record = file_record(reference) if reference else None
    directory.mkdir(parents=True, exist_ok=True)
    published: list[tuple[Path, Path]] = []
    # Staging on the destination filesystem lets os.link publish files without
    # replacing anything, including a file created by another export meanwhile.
    with tempfile.TemporaryDirectory(prefix=".maguire-export-", dir=directory) as temporary:
        staging = Path(temporary)
        # Keep the generated reference out of the document filename namespace.
        # A candidate may legitimately name a source "reference.md".
        reference_directory = staging / "reference"
        reference_directory.mkdir()
        reference_doc = reference_directory / "reference.docx"
        added_styles = []
        if reference is None:
            neutral_reference(tools["pandoc"], reference_doc)
        else:
            added_styles = complete_reference(tools["pandoc"], reference, reference_doc)
        docx = staging / (source.stem + ".docx")
        run([tools["pandoc"], "--from=markdown", "--to=docx", "--standalone",
             "--resource-path=" + str(source.parent), "--reference-doc=" + str(reference_doc),
             "--output=" + str(docx), str(source)])
        validate_docx(docx)
        if "pdf" in formats:
            pdf_directory = staging / "pdf"
            pdf_directory.mkdir()
            profile = staging / "libreoffice-profile"
            run([tools["libreoffice"], "-env:UserInstallation=" + profile.as_uri(),
                 "--headless", "--convert-to", "pdf:writer_pdf_Export", "--outdir",
                 str(pdf_directory), str(docx)])
            pdf = pdf_directory / (source.stem + ".pdf")
            if not pdf.is_file() or not pdf.read_bytes().startswith(b"%PDF-"):
                raise ValueError("LibreOffice did not produce a PDF; no exports were published")
        staged = {"docx": docx}
        if "pdf" in formats:
            staged["pdf"] = pdf
        # Never publish a receipt bound to inputs that changed during rendering.
        if sha256(source) != source_record["sha256"]:
            raise ValueError("Source changed during export; rerun from the reviewed draft")
        if reference and sha256(reference) != reference_record["sha256"]:
            raise ValueError("Reference changed during export; rerun from a stable reference")
        artifacts = []
        for item, target in zip(formats, targets):
            record = file_record(staged[item])
            record["path"] = str(target)
            artifacts.append(record)
        receipt = {
            "format": "maguire-export.1",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source": source_record,
            "reference": reference_record or {"builtin": "neutral-v1", "sha256": sha256(reference_doc)},
            "reference_preparation": {"added_styles": added_styles,
                                      "effective_sha256": sha256(reference_doc)},
            "backends": {"docx": "pandoc", "pdf": "libreoffice" if "pdf" in formats else None},
            "artifacts": artifacts,
            "review": {"content": "pending", "layout": "pending", "candidate": "pending"},
        }
        staged_receipt = staging / "receipt.json"
        staged_receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        try:
            for item, target in zip(formats, targets):
                checked_path(target)
                os.link(staged[item], target)
                published.append((target, staged[item]))
            checked_path(receipt_target)
            os.link(staged_receipt, receipt_target)
            published.append((receipt_target, staged_receipt))
        except BaseException:
            for target, original in reversed(published):
                try:
                    current = target.lstat()
                    created = original.stat()
                    if (current.st_dev, current.st_ino) == (created.st_dev, created.st_ino):
                        target.unlink()
                except FileNotFoundError:
                    pass
            raise
    receipt["receipt_path"] = str(receipt_target)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, nargs="?")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--reference-doc", type=Path)
    parser.add_argument("--format", choices=("docx", "pdf", "both"), default="both")
    parser.add_argument("--check", action="store_true", help="Report local renderer availability; do not export")
    args = parser.parse_args(argv)
    if args.check:
        result = capabilities(args.format)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["ready"] else 2
    if args.source is None or args.output_dir is None:
        parser.error("source and --output-dir are required unless --check is used")
    try:
        result = export(args.source, args.output_dir, args.reference_doc, args.format)
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print("Export failed: " + str(error), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
