# -*- coding: utf8 -*-
import unittest

from ..datauri import encodeDataUri, decodeDataUri


class TestDataUri(unittest.TestCase):
    def test_encodeDataUri(self):
        def b64(s):
            return s.encode("base64").replace("\n", "")

        # By default encode as base64
        self.assertEqual(
            encodeDataUri("a b/c d"),
            "data:;base64," + b64("a b/c d"),
        )

        # Can turn this off
        self.assertEqual(
            encodeDataUri("a b/c d", encoding=None),
            "data:,a%20b/c%20d",
        )

        # First argument is the MIME type
        self.assertEqual(
            encodeDataUri("camel", "text/x-tex", encoding=None),
            "data:text/x-tex,camel",
        )

        # Complain about unknown encodings
        with self.assertRaisesRegexp(ValueError, "camel"):
            encodeDataUri("aa", encoding="camel")

        # By default, encode as ASCII
        with self.assertRaises(UnicodeEncodeError):
            encodeDataUri(u"Café", encoding=None)

        # Can do UTF-8 & latin-1
        self.assertEqual(
            encodeDataUri(u"Café", encoding=None, characterSet="UTF-8"),
            "data:;charset=UTF-8,Caf%C3%A9",
        )
        self.assertEqual(
            encodeDataUri(u"Café", encoding=None, characterSet="iso-8859-1"),
            "data:;charset=iso-8859-1,Caf%E9",
        )

        # Can specify a MIME
        self.assertEqual(
            encodeDataUri("a b/c d", mimeType="image/png"),
            "data:image/png;base64," + b64("a b/c d"),
        )

    def test_decodeDataUri(self):
        """Test cases from http://www-archive.mozilla.org/quality/networking/testing/datatests.html"""
        def b64(s):
            return s.encode("base64").replace("\n", "")

        # examples (from RFC)
        self.assertEqual(
            decodeDataUri("data:,A%20brief%20note"),
            dict(data="A brief note", mimeType="text/plain"),
        )
        self.assertEqual(
            decodeDataUri("data:image/gif;base64," + b64("GIFLarryImage")),
            dict(data="GIFLarryImage", mimeType="image/gif"),
        )
        self.assertEqual(
            decodeDataUri("data:text/plain;charset=iso-8859-7,%b8%f7%fe"),
            dict(data=u"Έχώ", mimeType="text/plain"),
        )

        # scheme only
        self.assertEqual(
            decodeDataUri("data:"),
            dict(data=None, mimeType="text/plain"),
        )

        # data w/o data segment
        self.assertEqual(
            decodeDataUri("data:,"),
            dict(data="", mimeType="text/plain"),
        )
        self.assertEqual(
            decodeDataUri("data:text/plain,"),
            dict(data="", mimeType="text/plain"),
        )

        # data w/o leading comma
        self.assertEqual(
            decodeDataUri("data:test"),
            dict(data=None, mimeType="text/plain"),
        )

        # data w/ traditionally reserved chaacters like ";"
        self.assertEqual(
            decodeDataUri("data:,;test"),
            dict(data=";test", mimeType="text/plain"),
        )

        # data w/ unneeded ";"
        self.assertEqual(
            decodeDataUri("data:;,test"),
            dict(data="test", mimeType="text/plain"),
        )

        # default mediatype w/ default character set
        self.assertEqual(
            decodeDataUri("data:text/plain,test"),
            dict(data="test", mimeType="text/plain"),
        )
        self.assertEqual(
            decodeDataUri("data:text/plain;charset=US-ASCII,test"),
            dict(data="test", mimeType="text/plain"),
        )

        # invalid character set
        self.assertEqual(
            decodeDataUri("data:;charset=UHT-8,Hello"),
            dict(data="Hello", mimeType="text/plain"),
        )

        # multiple commas
        self.assertEqual(
            decodeDataUri("data:,a,b"),
            dict(data="a,b", mimeType="text/plain"),
        )

        # base64
        self.assertEqual(
            decodeDataUri("data:;base64"),
            dict(data=None, mimeType="text/plain"),
        )
        self.assertEqual(
            decodeDataUri("data:;base64,"),
            dict(data="", mimeType="text/plain"),
        )
        self.assertEqual(
            decodeDataUri("data:;base64,hello"),
            dict(data=None, mimeType="text/plain"),
        )
        self.assertEqual(
            decodeDataUri("data:text/html;base64,VGhpcyBpcyBhIHRlc3QK"),
            dict(data="This is a test\n", mimeType="text/html"),
        )

        # all options
        self.assertEqual(
            decodeDataUri("data:text/plain;charset=thing;base64;test"),
            dict(data=None, mimeType="text/plain"),
        )

        # empty charset
        self.assertEqual(
            decodeDataUri("data:;charset=,test"),
            dict(data="test", mimeType="text/plain"),
        )

        # utf8
        self.assertEqual(
            decodeDataUri("data:text/plain;charset=iso-8859-8,%f9%ec%e5%ed"),
            dict(data=u"שלום", mimeType="text/plain"),
        )
        self.assertEqual(
            decodeDataUri("data:text/plain;charset=UTF-8,%d7%a9%d7%9c%d7%95%d7%9d"),
            dict(data=u"שלום", mimeType="text/plain"),
        )
        self.assertEqual(
            decodeDataUri("data:text/plain;charset=iso-8859-8;base64,+ezl7Q=="),
            dict(data=u"שלום", mimeType="text/plain"),
        )
        self.assertEqual(
            decodeDataUri("data:text/plain;charset=UTF-8;base64,16nXnNeV150="),
            dict(data=u"שלום", mimeType="text/plain"),
        )

    def test_unofficialExtras(self):
        """Should be able to store arbitary key/values"""
        self.assertEqual(
            encodeDataUri("camel", "text/x-tex", encoding=None, extra=dict(humps=2, spits="yes")),
            'data:text/x-tex;spits=yes;humps=2,camel',
        )
        self.assertEqual(
            decodeDataUri('data:text/x-tex;spits=yes;humps=2,camel'),
            dict(data=u"camel", mimeType="text/x-tex", extra=dict(spits="yes", humps="2")),
        )
