from json import JSONEncoder

"""
Module that monkey-patches json module when it's imported so
JSONEncoder.default() automatically checks for a special "to_json()"
method and uses it to encode the object if found.
"""  # https://stackoverflow.com/a/18561055/3423324#making-object-json-serializable-with-regular-encoder


def _default(self, obj):
    return getattr(obj.__class__, "to_json", _default.default)(obj)
# end def


_default.default = JSONEncoder.default  # Save unmodified default.
JSONEncoder.default = _default  # Replace it.
