import binascii
import mimetypes
import os.path
import re
import shutil
import subprocess
import sys
import tempfile


from Products.PortalTransforms.data import datastream
from Products.CMFCore.utils import getToolByName
from plone.app.textfield.value import RichTextValue

from .transforms.script_to_html import ScriptToTeX

TIMEOUT = "3m"
TIMEOUT_BINARY = "/usr/bin/timeout"
RUBBER_BINARY = "/usr/bin/rubber"


class TexWriter(object):
    def __init__(self):
        self.dir = tempfile.mkdtemp()

    def createPDF(self, tex):
        """Convert output into PDF"""
        for b in [TIMEOUT_BINARY, RUBBER_BINARY]:
            if not os.path.isfile(b):
                raise ValueError("Binary %s not available" % b)

        self.explodeTeX(tex)

        p = subprocess.Popen(
            [
                TIMEOUT_BINARY, TIMEOUT,
                RUBBER_BINARY, '--inplace', '--pdf', '-Wall', '--maxerr=100', '--force',
                os.path.join(self.dir, 'exploded.tex'),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        (processOut, processErr) = p.communicate("")
        exitCode = p.wait()
        if exitCode != 0:
            return processOut + processErr + "\nCompilation of document failed!"

        self._outputFile = os.path.join(self.dir, 'exploded.pdf')
        return processOut + processErr

    def outputPdf(self):
        if not getattr(self, '_outputFile', ''):
            return None
        if not os.path.exists(self._outputFile):
            return None
        return self._outputFile

    def explodeTeX(self, tex):
        """Turn single TeX output into lots of files"""
        def mimeToExt(mime):
            if mime == 'application/postscript':
                return '.eps'
            else:
                return mimetypes.guess_extension(mime)

        def replaceDataBlock(m):
            if not(hasattr(self, '_imgcount')):
                self._imgcount = 0
            outFile = os.path.join(self.dir, 'img%d%s' % (
                self._imgcount,
                mimeToExt(m.group(1)),
            ))
            self._imgcount += 1

            with open(outFile, 'w') as f:
                f.write(binascii.a2b_base64(m.group(2)))
            return '\\includegraphics{%s}' % os.path.basename(os.path.splitext(outFile)[0])

        with open(os.path.join(self.dir, 'exploded.tex'), 'w') as outputTeX:
            outputTeX.write(re.sub(
                r'\\includegraphicsdata\{data:([^:}]+):base64,([^:}]+)\}',
                replaceDataBlock,
                tex,
            ))

    def close(self):
        """Get rid of temporary directory"""
        shutil.rmtree(self.dir)


class TexGenerator(object):
    def __init__(self, tutorial):
        """Produce TeX based on tutorial, return a list of file paths"""
        def children(obj, portal_type):
            # TODO: Should filter by workflow state
            return (
                l.getObject()
                for l
                in obj.restrictedTraverse('@@folderListing')(Type=portal_type)
            )

        self._tex = ""

        self.texPreamble(tutorial)
        self.texTutorialHeader(tutorial)

        for lecture in children(tutorial, 'Lecture'):
            self.texLectureHeader(lecture)

            for slide in children(lecture, 'Slide'):
                self.texSlideHeader(slide)
                for section in slide.sections:
                    self.texSlideSection(section)
                self.texSlideFooter(slide)

            self.texLectureFooter(lecture)

        self.texTutorialFooter(tutorial)
        self.texPostamble(tutorial)

    def tex(self):
        return self._tex

    def writeTeX(self, lines):
        def rtConvert(obj, newMimeType):
            """Create new RichTextValue with outputMimeType we want"""
        for l in lines:
            if hasattr(l, 'raw_encoded'):
                l = RichTextValue(
                    raw=l.raw,
                    mimeType=l.mimeType,
                    outputMimeType='text/x-tex',
                    encoding=l.encoding,
                ).output
            if isinstance(l, unicode):
                l = l.encode('utf-8')
            if l is not None:
                self._tex += l + "\n"

    ############### TeX File header / footer

    def texPreamble(self, tutorial):
        preamble = tutorial.pdf_preamble or ""
        if len(preamble) == 0:
            self.writeTeX([
                '\\documentclass[titlepage]{article}',
                '\\usepackage{mathptm}',
                '\\usepackage{a4,graphics,amsmath,amsfonts,amsbsy}',
                '\\usepackage[T1]{fontenc}',
                '\\usepackage[numbers,sort&compress]{natbib}',
                '\\usepackage[utf8]{inputenc}',
                '\\usepackage{float, rotating, subfigure}',
                '\\usepackage[font=scriptsize]{caption}',
                '\\usepackage{longtable}',
                '\\usepackage{framed}',
                '\\usepackage{enumerate}',
                '\\usepackage{epstopdf}',
            ])
        self.writeTeX([
            '\\newcommand{\\captionfonts}{\\tiny}',
            '\\makeatletter',
            '\\long\\def\\@makecaption#1#2{%',
            '\\vskip\\abovecaptionskip',
            '\\sbox\@tempboxa{{\captionfonts #1: #2}}%',
            '\\ifdim \\wd\\@tempboxa >\\hsize',
            '{\\captionfonts #1: #2\\par}',
            '\\else',
            '\\hbox to\\hsize{\\hfil\\box\\@tempboxa\\hfil}%',
            '\\fi',
            '\\vskip\\belowcaptionskip}',
            '\\makeatother',
            '\\parindent 0mm',
            '\\parskip 3mm',
            '\\topmargin -15mm',
            '\\input{epsf}',
            '\\oddsidemargin 15mm',
            '\\textheight 237mm',
            '\\textwidth 145mm',
            '\\headsep .35in',
            '\\fboxrule 0.2mm',
            '\\fboxsep 6mm',
        ])
        if len(preamble) == 0:
            self.writeTeX([
                '\\newcommand{\\bs}{\\boldsymbol}',
                '\\newcommand{\\bi}{\\begin{itemize}\\item}',
                '\\newcommand{\\ei}{\\end{itemize}}',
                '\\newcommand{\\eq}[1]{\\begin{equation} #1 \\end{equation}}',
                '\\newcommand{\\ea}[1]{\\begin{eqnarray} #1 \\end{eqnarray}}',
                '\\newcommand{\\vs}{\\vspace{2mm}}',
                '\\newenvironment{block}[1]{\\begin{framed} \\textbf{#1} \\\ }{\\end{framed}}',
                '\\begin{document}',
            ])
        else:
            self.writeTeX(preamble)

    def texPostamble(self, tutorial):
        if tutorial.pdf_postamble:
            self.writeTeX([tutorial.pdf_postamble])
        else:
            self.writeTeX(['\\end{document}'])

    ############### TeX Tutorials

    def texTutorialHeader(self, tutorial):
        def convertImage(img):
            """Convert an image into an included data-URI"""
            return '\\includegraphicsdata{%s}' % ":".join([
                'data',
                img.contentType,
                "base64,%s" % img.data.encode("base64").replace("\n", ""),
            ])

        self.writeTeX([
            '%% Tutorial ' + tutorial.absolute_url(),
            '\\title{%s\n%s\n}' % (tutorial.id, tutorial.Title()),
            '\\author{{%s}}' % (tutorial.author or 'No author set yet'),
            '\\maketitle',
            '{\\small{\\bf Copyright}',
            'This work is licensed under the Creative Commons Attribution-ShareAlike License. To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/1.0/ or send a letter to Creative Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.',
            '}',
        ])

        # Acknowledgements
        if len(getattr(tutorial, 'sponsors', [])) > 0:
            self.writeTeX([
                '{\\bf ACKNOWLEDGEMENTS}',
                ' ',
                '\\vspace{12pt}',
            ])
            for rel in tutorial.sponsors:
                institution = rel.to_object;
                self.writeTeX([
                    '\\begin{tabular}{p{6cm}l}',
                    institution.title,
                    institution.url,
                    '& \\resizebox{3cm}{!}{' + convertImage(institution.logo) + '}',
                    '\\end{tabular}',
                ])
            self.writeTeX([tutorial.sponsors_description])

        # ToC
        self.writeTeX(['\\newpage', '\\tableofcontents', '\\newpage'])

    def texTutorialFooter(self, tutorial):
        if tutorial.pdf_reference:
            self.writeTeX([
                '\\section{References}',
                tutorial.pdf_reference
            ])

    ############### TeX Lectures

    def texLectureHeader(self, lecture):
        self.writeTeX([
            '%% Lecture ' + lecture.absolute_url(),
            '\\section{' + lecture.Title() + '}'
        ])

    def texLectureFooter(self, lecture):
        if lecture.pdf_reference:
            self.writeTeX([
                '{\\bf References}',
                lecture.pdf_reference,
                '\\clearpage'
            ])

    ############### TeX Slides

    def texSlideHeader(self, slide):
        self.writeTeX([
            '%% Slide ' + slide.absolute_url(),
            '\\subsection{' + slide.title + '}',
        ])

    def texSlideFooter(self, slide):
        self.writeTeX([""])

    def texSlideSection(self, section):
        def scriptToImage(script):
            tf = ScriptToTeX()
            data = tf.convert(
                script.raw,
                datastream("scriptToImage"),
                mimetype='text/x-uri' if script.mimeType == 'text/x-url' else script.mimeType)
            return data.getData()

        if not section.image_code or not section.image_code.raw:
            self.writeTeX([section.text])
            return

        # Otherwise, write an image
        self.writeTeX([
            '\\begin{figure}[h]',
            '\\begin{tabular}{ll}',
            '\\begin{minipage}{%s\\textwidth}' % ('0.75' if section.text else '1.0'),
            '\\resizebox{7cm}{!}{',
            scriptToImage(section.image_code),
            '}',
        ])
        if section.image_caption:
            self.writeTeX(['\\caption{%s}' % section.image_caption])
        self.writeTeX([
            '\\end{minipage}',
        ])
        if section.text:
            self.writeTeX([
                '\\begin{minipage}{0.5\\textwidth}{',
                '\\tiny\\fbox{',
                '\\parbox[c]{3truecm}{',
                section.text,
                '}}}',
                '\\end{minipage}',
            ])
        self.writeTeX([
            '\\end{tabular}',
            '\\end{figure}',
            '\\clearpage',
        ])
