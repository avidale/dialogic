import urllib.request


def encode_uri(url):
    """ Produce safe ASCII urls, like in the Russian Wikipedia"""
    return urllib.request.quote(url, safe='~@#$&()*!+=:;,.?/\'')
