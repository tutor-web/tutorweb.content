import binascii
import mimetypes
import os.path
import re
import shutil
import subprocess
import sys
import tempfile

from Acquisition import aq_parent

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

    def addDataFile(self, name, stream, overwrite_existing=True):
        if not(overwrite_existing) and os.path.exists(os.path.join(self.dir, name)):
            return False
        with open(os.path.join(self.dir, name), 'w') as f:
            shutil.copyfileobj(stream, f)
        return True

    def createPDF(self, tex):
        """Convert output into PDF"""
        for b in [TIMEOUT_BINARY, RUBBER_BINARY]:
            if not os.path.isfile(b):
                raise ValueError("Binary %s not available" % b)

        self.explodeTeX(tex)

        p = subprocess.Popen(
            [
                TIMEOUT_BINARY, TIMEOUT,
                RUBBER_BINARY, '--inplace', '--ps', '-ops2pdf', '-Wall', '--maxerr=100', '--force',
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
            return '\\includegraphics[width=\linewidth,height=5cm,keepaspectratio]{%s}' % os.path.basename(os.path.splitext(outFile)[0])

        with open(os.path.join(self.dir, 'exploded.tex'), 'w') as outputTeX:
            outputTeX.write(re.sub(
                r'\\includegraphicsdata\{data:([^:}]+):base64,([^:}]+)\}',
                replaceDataBlock,
                tex,
            ))

    def close(self, keepOutput=False):
        """Get rid of temporary directory"""
        if not keepOutput:
            shutil.rmtree(self.dir)


def main():
    import argparse
    import shutil
    import sys

    parser = argparse.ArgumentParser(description='Turn TeX into PDF')
    parser.add_argument(
        '--keep-output',
        action="store_true",
        default=False,
        help='Keep temporary directory with intermediate files')
    parser.add_argument(
        'filename',
        type=str,
        help='Name of TeX file')
    args = parser.parse_args()

    targetFileName = 'output.pdf'
    tw = TexWriter()
    print "Working in tempdir %s" % tw.dir
    with open(args.filename) as f:
        print tw.createPDF(f.read())

    pdfOut = tw.outputPdf()
    if pdfOut is None:
        print "No PDF generated"
        return 1
    shutil.copy(pdfOut, targetFileName)
    print "Saved %s" % targetFileName
    tw.close(args.keep_output)
    return 0


class TexGenerator(object):
    def __init__(self, tutorial):
        """Produce TeX based on tutorial, return a list of file paths"""
        self._tex = ""

        self.texPreamble(tutorial)
        self.texTutorialHeader(tutorial)

        for lecture in self.children(tutorial):
            self.texLectureHeader(lecture)

            for slide in self.children(lecture):
                self.texSlideHeader(slide)
                for section in slide.sections:
                    self.texSlideSection(section)
                self.texSlideFooter(slide)

            self.texLectureFooter(lecture)

        self.texTutorialFooter(tutorial)
        self.texPostamble(tutorial)

    def children(self, obj):
        # TODO: Should filter by workflow state
        return (
            l.getObject()
            for l
            in obj.restrictedTraverse('@@folderListing')(
                Type=dict(
                    Tutorial='Lecture',
                    Lecture='Slide',
                )[obj.Type()],
                sort_on="id",
            )
        )

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

    def slideSectionType(self, obj):
        if not obj.title:  # Main section
            return 'main'
        if obj.title.strip().lower() == 'explanation':
            return 'explanation'
        return 'other'

    ############### TeX File header / footer

    def texPreamble(self, tutorial):
        preamble = getattr(tutorial, 'pdf_preamble', "") or ""
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
            self.writeTeX([preamble])

    def texPostamble(self, tutorial):
        if getattr(tutorial, 'pdf_postamble', ''):
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
                '\n\n',
                '\\vspace{12pt}',
                '{\\small'
                '{\\bf Acknowledgements}',
                ' ',
                tutorial.sponsors_description,
            ])
            for rel in tutorial.sponsors:
                institution = rel.to_object;
                self.writeTeX([
                    '\n\n',
                    institution.text,
                    '\\\\ {\\tt %s}' % institution.url.strip(),
                ])
            self.writeTeX(['}\n\n'])

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
        type = self.slideSectionType(section)
        # Neither image or text, ignore section
        if not section.image_code and not section.text:
            return
        if type == 'explanation':
            # Explanations are only useful as footnotes to slides
            return

        if type == 'main':
            # Write out approximation to slide

            self.writeTeX(['\\fbox{']);

            # Main section text goes into a slide minipage
            if section.text and section.text.raw:
                self.writeTeX([
                    '\\begin{minipage}{' + ('0.58' if section.image_code else '0.97') + '\\textwidth}',
                    section.text,
                    '\\end{minipage}',
                ])

            # If there is an image, write it into a minipage
            if section.image_code and section.image_code.raw:
                tf = ScriptToTeX()
                data = tf.convert(
                    section.image_code.raw,
                    datastream("scriptToImage"),
                    mimetype='text/x-uri' if section.image_code.mimeType == 'text/x-url' else section.image_code.mimeType)

                self.writeTeX([
                    '\\hspace{0.5mm}',
                    '\\begin{minipage}{' + ('0.38' if type != 'main' or section.text else '0.97') + '\\textwidth}',
                    data.getData(),
                    '\scriptsize ' + section.image_caption if section.image_caption else '',
                    '\\end{minipage}',
                ])

            self.writeTeX(['}']);

        else:
            self.writeTeX(['\\subsubsection{' + section.title + '}'])

            # Write out floating image
            if section.image_code and section.image_code.raw:
                tf = ScriptToTeX()
                data = tf.convert(
                    section.image_code.raw,
                    datastream("scriptToImage"),
                    mimetype='text/x-uri' if section.image_code.mimeType == 'text/x-url' else section.image_code.mimeType)

                self.writeTeX([
                    '\\begin{figure}[h]',
                    '\\hspace{0.5mm}',
                    '\\begin{minipage}{0.48\\textwidth}',
                    data.getData(),
                    '\\caption{%s}' % section.image_caption if section.image_caption else '',
                    '\\end{minipage}',
                    '\\end{figure}',
                ])

            # Rest of text goes in verbatim
            self.writeTeX([section.text])


class TexSlideGenerator(TexGenerator):
    def __init__(self, lecture):
        """Produce TeX slides"""
        self._tex = ""

        self.texPreamble(lecture)
        self.texLectureHeader(lecture)

        for slide in self.children(lecture):
            self.texSlideHeader(slide)
            for section in slide.sections:
                self.texSlideSection(section)
            self.texSlideFooter(slide)

        self.texLectureFooter(lecture)
        self.texPostamble(lecture)

    ############### TeX File header / footer

    def texPreamble(self, obj):
        tutorial = aq_parent(obj)
        self.writeTeX([
            '\\documentclass[%\n]{beamer}',
            '\\usepackage{graphics,amsmath,amsfonts,amssymb}',
            '\\usepackage[T1]{fontenc}',
            '\\usepackage[numbers, sort&compress]{natbib}',
            '\\usepackage[utf8]{inputenc}',
            '\\usepackage{float, rotating, subfigure}',
            '\\usepackage[skip=2pt]{caption}',
            '\\usepackage{setspace}',
            '\\usepackage{etex}',
            '\\usepackage{wrapfig}',
            '\\usepackage{pictexwd}',
            '\\newcommand{\\bs}{\\boldsymbol}',
            '\\newcommand{\\bi}{\\begin{itemize}\\item}',
            '\\newcommand{\\ei}{\\end{itemize}}',
            '\\newcommand{\\eq}[1]{\\begin{equation} #1 \\end{equation}}',
            '\\newcommand{\\ea}[1]{\\begin{eqnarray} #1 \\end{eqnarray}}',
            '\\newcommand{\\vs}{\\vspace{2mm}}',
            '\\makeatletter',
            '\\makeatother',
            '\\usetheme{CambridgeUS}',
            '\\usecolortheme{dolphin}',
            '\\setbeamerfont{caption name}{size=\scriptsize}',
            '\\title{' + obj.Title() + '}',
            '\\subtitle{%s\n%s\n}' % (tutorial.id, tutorial.Title()),
            '\\author{{%s}}' % (tutorial.author or 'No author set yet'),

            '\\begin{document}'+'\n',
            '\\maketitle' + '\n',
        ])

    def texPostamble(self, obj):
        self.writeTeX([
            '\\end{document}',
        ])

    ############### TeX Slides

    def texSlideHeader(self, obj):
        self.writeTeX([
            '%% Slide ' + obj.absolute_url(),
            '\\begin{frame}[fragile]',
            '\\frametitle{' + obj.Title() +'}',
        ])

        sect = dict(
            (self.slideSectionType(obj), section)
            for section in obj.sections
        )
        self.slideInfo = dict(
            mainText=(sect.get('main', None) and sect['main'].text and sect['main'].text.raw),
            mainImage=(sect.get('main', None) and sect['main'].image_code and mainSection.image_code.raw),
            explText=(sect.get('explanation', None) and sect['explanation'].text and sect['explanation'].text.raw),
            explImage=(sect.get('explanation', None) and sect['explanation'].image_code and sect['explanation'].image_code.raw),
        )

    def texSlideFooter(self, obj):
        self.writeTeX([
            '\\end{frame}',
        ])

    def texSlideSection(self, obj):
        type = self.slideSectionType(obj)
        if type == 'main':
            isExpl = False
        elif type == 'explanation':
            isExpl = True
        else:
            # Ignore other sections
            return

        haveText = (obj.text and obj.text.raw)
        haveImage = (obj.image_code and obj.image_code.raw)

        if self.slideInfo['mainText'] and self.slideInfo['explText']:
            imageSize = 5
        elif self.slideInfo['mainText'] and not self.slideInfo['explText']:
            imageSize = 6
        elif not self.slideInfo['mainText'] and self.slideInfo['explText']:
            imageSize = 7
        else:
            imageSize = 9
        if self.slideInfo['explImage'] or isExpl:
            imageSize -= 1
        imageSize -= 1
        imageSize = str(imageSize)

        self.writeTeX([
            '%% Section ' + (obj.title or "main"),
            '\\begin{tabular}{ll}',
        ])

        # Slide text
        if haveText:
            self.writeTeX([
                '\\begin{minipage}{' + ('0.58' if haveImage else '0.97') + '\\textwidth}',
                '{\\scriptsize' if isExpl else '',
                '\\vfill' if isExpl else '',
                obj.text,
                '}' if isExpl else '',
                '\\end{minipage}',
            ])

        # Slide image
        if haveImage:
            tf = ScriptToTeX()
            data = tf.convert(
                obj.image_code.raw,
                datastream("scriptToImage"),
                mimetype='text/x-uri' if obj.image_code.mimeType == 'text/x-url' else obj.image_code.mimeType)

            self.writeTeX([
                '\\hspace{0.5mm}',
                '\\begin{minipage}{' + ('0.38' if haveText else '0.97') + '\\textwidth}',
                '\\begin{figure}',
                data.getData(),
                '\\caption{\scriptsize ' + obj.image_caption + '}' if obj.image_caption else '',
                '\\end{figure}',
                '\\end{minipage}',
            ])

        self.writeTeX([
            '\\end{tabular}',
        ])
