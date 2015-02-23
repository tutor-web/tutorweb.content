import re
import urllib

def encodeDataUri(data, mimeType=None, characterSet=None, encoding="base64"):
    if encoding is None or encoding == "uri":
        encodedData = "," + urllib.quote(data.encode(characterSet if characterSet else 'US-ASCII'))
    elif encoding == "base64":
        encodedData = ";base64,%s" % data.encode("base64").replace("\n", "")
    else:
        raise ValueError("Unknown encoding %s" % encoding)

    return "".join([
        "data:",
        mimeType if mimeType else "",
        ";charset=%s" % characterSet if characterSet else "",
        encodedData,
    ])

def decodeDataUri(uri):
    if uri == "data:":
        return dict(data=None, mimeType="text/plain")

    m = re.match(r'data:(.*?)(,|$)(.*)', uri)
    if not m:
        raise ValueError("Invalid Data URI %s" % uri)

    # Work out charset, mime, encoding
    out = dict(mimeType='text/plain')
    charSet = 'US-ASCII'
    encoding = 'uri'
    for l in m.group(1).split(";"):
        if l == "":
            continue
        elif l in ("base64", "uri"):
            encoding = l
        elif re.match(r'[a-zA-Z0-9]+/', l):
            out['mimeType'] = l
        elif l.startswith("charset="):
            charSet = l.replace("charset=", "")

    # Decode Data
    data = m.group(3)
    if m.group(2) != ",":
        # No data block, so no data
        data = None
    elif encoding == 'uri':
        try:
            data = urllib.unquote(data).decode(charSet)
        except LookupError:
            # Mozilla says we should just ignore unknown encodings
            data = urllib.unquote(data).decode("US-ASCII")
    elif encoding == 'base64':
        try:
            data = data.decode("base64")
        except:
            data = None
        if charSet != "US-ASCII":
            try:
                data = data.decode(charSet)
            except LookupError:
                pass
    out['data'] = data

    # Turn into dict
    return out
