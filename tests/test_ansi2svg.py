"""tools/ansi2svg.py: Farben, Spalten und Kürzen der Bildschirmfotos in docs/img/."""
from pathlib import Path
import importlib.util
import unittest
import xml.dom.minidom

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ansi2svg', ROOT / 'tools' / 'ansi2svg.py')
a2s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a2s)


class Ansi2Svg(unittest.TestCase):
    def test_colours_and_columns(self):
        runs, width = a2s.parse('\x1b[2m12:00:00\x1b[0m \x1b[32m✓\x1b[0m run valid')
        self.assertEqual(width, 20)
        self.assertEqual([(c, t) for c, t, _ in runs], [(0, '12:00:00'), (9, '✓'), (11, 'run valid')])
        self.assertEqual([st for _, _, st in runs], [(None, False, True), (32, False, False), (None, False, False)])

    def test_other_escape_codes_are_dropped(self):
        runs, _ = a2s.parse('\x1b[2K\x1b[1mbold\x1b[0m')
        self.assertEqual([(c, t, st[1]) for c, t, st in runs], [(0, 'bold', True)])

    def test_valid_svg_with_title_and_clipped_lines(self):
        svg = a2s.render('x' * 50 + '\n\x1b[36m━━\x1b[0m <a & b>\n', 'a "title"', cmd='./reproduce status', cols=20)
        dom = xml.dom.minidom.parseString(svg)
        self.assertEqual(dom.getElementsByTagName('title')[0].firstChild.data, 'a "title"')
        texts = [t.firstChild.data for t in dom.getElementsByTagName('text') if t.firstChild]
        self.assertIn('x' * 19 + '…', texts)   # 20 columns: 19 characters and the ellipsis
        self.assertIn('<a & b>', texts)


if __name__ == '__main__':
    unittest.main()
