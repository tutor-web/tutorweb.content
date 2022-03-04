# -*- coding: utf8 -*-
import os
import os.path
import unittest
import urllib

from tutorweb.content.tex_generator import TexWriter


def slurp(*path_parts):
    with open(os.path.join(*path_parts), 'rb') as f:
        return f.read()


class TexWriterTest(unittest.TestCase):
    maxDiff = None

    def test_explodeTeX(self):
        tw = TexWriter()
        tw.explodeTeX("""
\\begin{document}

\\includegraphics{https://tutor-web.net/++theme++www.tutor-web.net/images/tutorweb-logo.png}

\\includegraphics[width=10]{https://tutor-web.net/++theme++www.tutor-web.net/images/tutorweb-logo.png}

\\includegraphicsdata{data:image/gif:base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7}

\\end{document}
        """.strip())
        self.assertEqual(set(os.listdir(tw.dir)), set((
            'exploded.tex',
            'img0.eps',
            'img1.png',
            'img2.png',
        )))
        self.assertEqual(slurp(tw.dir, 'exploded.tex'), """
\\begin{document}

\\includegraphics[width=\\linewidth,height=5cm,keepaspectratio]{img1}

\\includegraphics[width=10]{img2}

\\includegraphics[width=\\linewidth,height=5cm,keepaspectratio]{img0}

\\end{document}
        """.strip())
        # NB: .gif got converted to .eps
        self.assertEqual(slurp(tw.dir, 'img0.eps')[0:4], b'%!PS')
        self.assertEqual(slurp(tw.dir, 'img1.png')[0:4], b'\x89PNG')
        self.assertEqual(slurp(tw.dir, 'img2.png')[0:4], b'\x89PNG')
