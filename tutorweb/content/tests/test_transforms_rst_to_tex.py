# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName

from .base import IntegrationTestCase

class RestToTeXTest(IntegrationTestCase):

    def test_transformText(self):
        """Should get LaTeX output
        """

        # Can transform
        self.assertEquals(self.doTransform(u"""
Tutor-web drill settings
^^^^^^^^^^^^^^^^^^^^^^^^

There are a bunch of key:value settings that can be used to control the
behaviour of the drill interface.

These can be set by doing one of:

* Editing the relevant tutorial
* Editing the relevant lecture
* Editing the defaults

For each lecture, the 2 lists of settings will be combined, the settings from a
lecture winning over any matching settings from a tutorial.

Core list of settings
=====================

Plone stores a list of all settings, and what their defaults should be. You can alter this by going here::

    http://zoot:8080/portal_registry/edit/tutorweb.content.lectureSettings
"""), r"""\hypertarget{tutor-web-drill-settings}{%
\section{Tutor-web drill settings}\label{tutor-web-drill-settings}}

There are a bunch of key:value settings that can be used to control the
behaviour of the drill interface.

These can be set by doing one of:

\begin{itemize}
\tightlist
\item
  Editing the relevant tutorial
\item
  Editing the relevant lecture
\item
  Editing the defaults
\end{itemize}

For each lecture, the 2 lists of settings will be combined, the settings
from a lecture winning over any matching settings from a tutorial.

\hypertarget{core-list-of-settings}{%
\subsection{Core list of settings}\label{core-list-of-settings}}

Plone stores a list of all settings, and what their defaults should be.
You can alter this by going here:

\begin{verbatim}
http://zoot:8080/portal_registry/edit/tutorweb.content.lectureSettings
\end{verbatim}
""")

    def doTransform(self, content, mimetype='text/restructured'):
        pt = getToolByName(self.layer['portal'], 'portal_transforms')
        raw = pt.convertTo(
            'text/x-tex',
            content.encode('utf-8'),
            mimetype=mimetype,
            encoding='utf-8',
        ).getData()
        return raw.decode('utf-8')
