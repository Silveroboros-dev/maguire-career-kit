"""Synthetic preservation and failure tests for the optional local export helper."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock
import zipfile


TOOL = Path(__file__).resolve().parents[1] / "tools/export.py"
SPEC = importlib.util.spec_from_file_location("maguire_export", TOOL)
exporter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(exporter)


def docx(path):
    prefix = '<w:document xmlns:w="' + exporter.WORD + '"><w:body><w:p/></w:body></w:document>'
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        archive.writestr("word/document.xml", prefix)
        archive.writestr("word/styles.xml", '<w:styles xmlns:w="' + exporter.WORD + '"/>')


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "Fictional CV.md"
        self.source.write_text("# Fictional Candidate\n\n## Experience\n\n- Coordinated a synthetic project.\n", encoding="utf-8")
        self.reference = self.root / "Original reference.docx"
        docx(self.reference)
        self.directory = self.root / "export v1"
        self.tools = {"format": "both", "pandoc": "/local/pandoc", "libreoffice": "/local/soffice",
                      "ready": True, "missing": []}
        self.commands = []

    def render(self, command):
        self.commands.append(command)
        if "--print-default-data-file=reference.docx" in command:
            return self.reference.read_bytes()
        if command[0] == "/local/pandoc":
            target = Path(next(item.split("=", 1)[1] for item in command if item.startswith("--output=")))
            docx(target)
        else:
            target = Path(command[command.index("--outdir") + 1]) / (Path(command[-1]).stem + ".pdf")
            target.write_bytes(b"%PDF-1.7\nSynthetic PDF bytes\n")
        return b""

    def invoke(self, output_format="both"):
        with mock.patch.object(exporter, "capabilities", return_value=self.tools), \
             mock.patch.object(exporter, "run", side_effect=self.render):
            return exporter.export(self.source, self.directory, self.reference, output_format)

    def test_both_formats_reference_and_input_bytes_preserved(self):
        original_source = self.source.read_bytes()
        original_reference = self.reference.read_bytes()
        receipt = self.invoke()
        self.assertEqual(self.source.read_bytes(), original_source)
        self.assertEqual(self.reference.read_bytes(), original_reference)
        pandoc = next(command for command in self.commands if any(item.startswith("--output=") for item in command))
        argument = next(item for item in pandoc if item.startswith("--reference-doc="))
        self.assertTrue(argument.endswith("/reference/reference.docx"))
        self.assertEqual(pandoc[-1], str(self.source))
        self.assertEqual(receipt["reference"]["path"], str(self.reference))
        self.assertIn("effective_sha256", receipt["reference_preparation"])
        self.assertEqual(len(receipt["artifacts"]), 2)
        self.assertEqual(receipt["review"], {"content": "pending", "layout": "pending", "candidate": "pending"})
        for artifact in receipt["artifacts"]:
            self.assertEqual(exporter.sha256(Path(artifact["path"])), artifact["sha256"])
        self.assertEqual(json.loads((self.directory / "Fictional CV.export.json").read_text())["source"]["sha256"],
                         exporter.sha256(self.source))
        office = next(command for command in self.commands if command[0] == "/local/soffice")
        self.assertTrue(any(item.startswith("-env:UserInstallation=file:") for item in office))
        self.assertEqual(sorted(path.name for path in self.directory.iterdir()),
                         ["Fictional CV.docx", "Fictional CV.export.json", "Fictional CV.pdf"])

    def test_pdf_only_does_not_publish_intermediate_docx(self):
        receipt = self.invoke("pdf")
        self.assertEqual(len(receipt["artifacts"]), 1)
        self.assertTrue((self.directory / "Fictional CV.pdf").is_file())
        self.assertFalse((self.directory / "Fictional CV.docx").exists())

    def test_docx_only_does_not_need_office(self):
        with mock.patch.object(exporter.shutil, "which", side_effect=lambda name: "/local/pandoc" if name == "pandoc" else None):
            capabilities = exporter.capabilities("docx")
        self.assertTrue(capabilities["ready"])
        receipt = self.invoke("docx")
        self.assertTrue(all(command[0] == "/local/pandoc" for command in self.commands))
        self.assertEqual(receipt["backends"]["pdf"], None)

    def test_failed_pdf_conversion_publishes_no_partial_docx(self):
        def fail(command):
            if command[0] != "/local/pandoc":
                raise ValueError("synthetic conversion failure")
            return self.render(command)
        with mock.patch.object(exporter, "capabilities", return_value=self.tools), \
             mock.patch.object(exporter, "run", side_effect=fail):
            with self.assertRaisesRegex(ValueError, "synthetic conversion failure"):
                exporter.export(self.source, self.directory, self.reference, "both")
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_successful_command_without_pdf_is_failure(self):
        def no_pdf(command):
            return self.render(command) if command[0] == "/local/pandoc" else b""
        with mock.patch.object(exporter, "capabilities", return_value=self.tools), \
             mock.patch.object(exporter, "run", side_effect=no_pdf):
            with self.assertRaisesRegex(ValueError, "did not produce a PDF"):
                exporter.export(self.source, self.directory, self.reference, "both")
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_refuses_existing_receipt_without_running_renderers(self):
        self.directory.mkdir()
        receipt = self.directory / "Fictional CV.export.json"
        receipt.write_bytes(b"previous review bytes")
        with mock.patch.object(exporter, "run") as renderer:
            with self.assertRaisesRegex(ValueError, "Refusing to overwrite"):
                exporter.export(self.source, self.directory, self.reference, "both")
            renderer.assert_not_called()
        self.assertEqual(receipt.read_bytes(), b"previous review bytes")

    def test_pdf_is_not_accepted_as_reference(self):
        reference = self.root / "Original.pdf"
        reference.write_bytes(b"%PDF-1.7")
        with self.assertRaisesRegex(ValueError, "requires a DOCX"):
            exporter.export(self.source, self.directory, reference, "both")
        self.assertFalse(self.directory.exists())

    def test_source_and_output_parent_symlinks_are_refused(self):
        linked_source = self.root / "linked.md"
        linked_source.symlink_to(self.source)
        with self.assertRaisesRegex(ValueError, "Symlink"):
            exporter.export(linked_source, self.directory, self.reference, "docx")
        actual = self.root / "actual"
        actual.mkdir()
        linked_dir = self.root / "linked"
        linked_dir.symlink_to(actual, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "Symlink"):
            exporter.export(self.source, linked_dir / "exports", self.reference, "docx")
        self.assertEqual(list(actual.iterdir()), [])

    def test_source_changed_during_conversion_refuses_publish(self):
        def change(command):
            result = self.render(command)
            self.source.write_text("Changed midway", encoding="utf-8")
            return result
        with mock.patch.object(exporter, "capabilities", return_value=self.tools), \
             mock.patch.object(exporter, "run", side_effect=change):
            with self.assertRaisesRegex(ValueError, "Source changed"):
                exporter.export(self.source, self.directory, self.reference, "docx")
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_publication_collision_rolls_back_only_own_files(self):
        original_link = exporter.os.link
        def race(source, target):
            if str(target).endswith(".pdf"):
                Path(target).write_bytes(b"another export won")
            return original_link(source, target)
        with mock.patch.object(exporter, "capabilities", return_value=self.tools), \
             mock.patch.object(exporter, "run", side_effect=self.render), \
             mock.patch.object(exporter.os, "link", side_effect=race):
            with self.assertRaises(FileExistsError):
                exporter.export(self.source, self.directory, self.reference, "both")
        self.assertFalse((self.directory / "Fictional CV.docx").exists())
        self.assertEqual((self.directory / "Fictional CV.pdf").read_bytes(), b"another export won")
        self.assertFalse((self.directory / "Fictional CV.export.json").exists())

    def test_rollback_preserves_an_output_replaced_by_another_editor(self):
        original_link = exporter.os.link
        def race(source, target):
            if str(target).endswith(".pdf"):
                first = self.directory / "Fictional CV.docx"
                first.unlink()
                first.write_bytes(b"editor replacement")
                Path(target).write_bytes(b"another export won")
            return original_link(source, target)
        with mock.patch.object(exporter, "capabilities", return_value=self.tools), \
             mock.patch.object(exporter, "run", side_effect=self.render), \
             mock.patch.object(exporter.os, "link", side_effect=race):
            with self.assertRaises(FileExistsError):
                exporter.export(self.source, self.directory, self.reference, "both")
        self.assertEqual((self.directory / "Fictional CV.docx").read_bytes(), b"editor replacement")

    def test_missing_dependency_check_is_actionable_and_does_not_make_output(self):
        with mock.patch.object(exporter.shutil, "which", return_value=None):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = exporter.main(["--check"])
            self.assertEqual(result, 2)
            self.assertEqual(len(json.loads(output.getvalue())["missing"]), 2)
            with self.assertRaisesRegex(ValueError, "Missing local rendering tools"):
                exporter.export(self.source, self.directory, self.reference, "both")
        self.assertFalse(self.directory.exists())

    def test_stuck_renderer_returns_a_bounded_failure(self):
        with mock.patch.object(exporter.subprocess, "run", side_effect=subprocess.TimeoutExpired("pandoc", 120)):
            with self.assertRaisesRegex(ValueError, "120-second conversion limit"):
                exporter.run(["pandoc", "synthetic.md"])

    @unittest.skipUnless(shutil.which("pandoc"), "Optional Pandoc is not installed")
    def test_neutral_reference_has_consistent_page_and_body_styles(self):
        reference = self.root / "neutral.docx"
        exporter.neutral_reference(shutil.which("pandoc"), reference)
        exporter.validate_docx(reference)
        with zipfile.ZipFile(reference) as archive:
            styles = archive.read("word/styles.xml").decode()
            document = archive.read("word/document.xml").decode()
        self.assertIn("Arial", styles)
        self.assertIn('w:val="21"', styles)
        self.assertIn('w:w="11906"', document)
        self.assertIn('w:top="1134"', document)
        root = exporter.ET.fromstring(styles)
        for style in root.findall(exporter.w("style")):
            if style.get(exporter.w("styleId")) not in ("Normal", "BodyText", "FirstParagraph", "Compact", "Title", "Heading1", "Heading2", "Heading3"):
                continue
            props = style.find(exporter.w("rPr"))
            fonts = props.find(exporter.w("rFonts"))
            self.assertFalse(any(key.rsplit("}", 1)[-1].lower().endswith("theme") for key in fonts.attrib))
            color = props.find(exporter.w("color"))
            if color is not None and color.get(exporter.w("val")) == "173B56":
                self.assertNotIn(exporter.w("themeColor"), color.attrib)
            para = style.find(exporter.w("pPr"))
            if para is not None:
                self.assertLess(list(style).index(para), list(style).index(props))

    @unittest.skipUnless(shutil.which("pandoc"), "Optional Pandoc is not installed")
    def test_real_docx_fallback_exports_reference_named_source(self):
        source = self.root / "reference.md"
        source.write_text("# Fictional Candidate\n\n- Synthetic experience only.\n", encoding="utf-8")
        receipt = exporter.export(source, self.directory, None, "docx")
        exporter.validate_docx(self.directory / "reference.docx")
        with zipfile.ZipFile(self.directory / "reference.docx") as archive:
            self.assertIn(b"Fictional Candidate", archive.read("word/document.xml"))
        self.assertEqual(receipt["reference"]["builtin"], "neutral-v1")

    @unittest.skipUnless(shutil.which("pandoc"), "Optional Pandoc is not installed")
    def test_reference_completion_preserves_existing_styles_and_all_other_parts(self):
        # An ordinary Word file may use different namespace prefixes and carries
        # its own typography. Neither condition should be rewritten to defaults.
        custom = ('<x:styles xmlns:x="' + exporter.WORD + '" '
                  'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
                  'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" mc:Ignorable="w14">'
                  '<x:style x:type="paragraph" x:styleId="Normal"><x:name x:val="Normal"/>'
                  '<x:rPr><x:rFonts x:ascii="Liberation Serif"/><x:color x:val="226644"/></x:rPr>'
                  '</x:style></x:styles>')
        with zipfile.ZipFile(self.reference) as original_zip:
            files = {name: original_zip.read(name) for name in original_zip.namelist()}
        files["word/styles.xml"] = custom.encode("utf-8")
        with zipfile.ZipFile(self.reference, "w") as output:
            for name, contents in files.items():
                output.writestr(name, contents)
        original = self.reference.read_bytes()
        completed = self.root / "completed.docx"
        added = exporter.complete_reference(shutil.which("pandoc"), self.reference, completed)
        self.assertIn("Compact", added)
        self.assertIn("FirstParagraph", added)
        self.assertEqual(self.reference.read_bytes(), original)
        exporter.validate_docx(completed)
        with zipfile.ZipFile(self.reference) as source, zipfile.ZipFile(completed) as output:
            for name in source.namelist():
                if name != "word/styles.xml":
                    self.assertEqual(source.read(name), output.read(name))
            root = exporter.ET.fromstring(output.read("word/styles.xml"))
            compact = next(node for node in root.findall(exporter.w("style"))
                           if node.get(exporter.w("styleId")) == "Compact")
            self.assertEqual(compact.find(exporter.w("basedOn")).get(exporter.w("val")), "BodyText")
            self.assertIsNone(compact.find(exporter.w("rPr")))
            original_styles = exporter.minidom.parseString(source.read("word/styles.xml"))
            completed_styles = exporter.minidom.parseString(output.read("word/styles.xml"))
            original_normal = original_styles.getElementsByTagNameNS(exporter.WORD, "style")[0]
            completed_normal = completed_styles.getElementsByTagNameNS(exporter.WORD, "style")[0]
            self.assertEqual(original_normal.toxml(), completed_normal.toxml())
            self.assertEqual(completed_styles.documentElement.getAttribute("mc:Ignorable"), "w14")
            self.assertEqual(completed_styles.documentElement.getAttribute("xmlns:w14"),
                             "http://schemas.microsoft.com/office/word/2010/wordml")

    @unittest.skipUnless(shutil.which("pandoc") and (shutil.which("soffice") or shutil.which("libreoffice"))
                         and shutil.which("pdftotext"), "Optional PDF renderers are not installed")
    def test_real_reference_missing_pandoc_styles_keeps_pdf_bullet_markers(self):
        raw = exporter.run([shutil.which("pandoc"), "--print-default-data-file=reference.docx"])
        reference = self.root / "ordinary-word-cv.docx"
        with zipfile.ZipFile(io.BytesIO(raw)) as default, zipfile.ZipFile(reference, "w") as prepared:
            styles = exporter.minidom.parseString(default.read("word/styles.xml"))
            for node in list(styles.getElementsByTagNameNS(exporter.WORD, "style")):
                if node.getAttributeNS(exporter.WORD, "styleId") in ("Compact", "FirstParagraph"):
                    node.parentNode.removeChild(node)
            for name in default.namelist():
                # Valid alternative prefix binding: Pandoc may append its own
                # w:style siblings, which also need a root xmlns:w declaration.
                serialized = styles.toxml(encoding="utf-8").replace(b"w:", b"x:").replace(b"xmlns:w=", b"xmlns:x=")
                prepared.writestr(name, serialized if name == "word/styles.xml" else default.read(name))
        source = self.root / "clean-cv.md"
        source.write_text("# Fictional Candidate\n\n- Synthetic item alpha.\n- Synthetic item beta.\n", encoding="utf-8")
        original = reference.read_bytes()
        receipt = exporter.export(source, self.directory, reference, "both")
        text = subprocess.check_output([shutil.which("pdftotext"), "-layout",
                                        str(self.directory / "clean-cv.pdf"), "-"]).decode("utf-8")
        self.assertGreaterEqual(text.count("•"), 2)
        self.assertIn("Synthetic item alpha.", text)
        self.assertIn("Synthetic item beta.", text)
        self.assertEqual(reference.read_bytes(), original)
        self.assertIn("Compact", receipt["reference_preparation"]["added_styles"])


if __name__ == "__main__":
    unittest.main()
