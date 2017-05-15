# -*- coding: utf-8 -*-
"""The exim4 file event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class Exim4LineFormatter(interface.ConditionalEventFormatter):
  """Formatter for a exim4 line event."""

  DATA_TYPE = u'exim4:line'

  FORMAT_STRING_SEPARATOR = u''

  FORMAT_STRING_PIECES = [
      u'{body}']

  SOURCE_LONG = u'Log File'
  SOURCE_SHORT = u'LOG'


manager.FormattersManager.RegisterFormatters(
    [Exim4LineFormatter])
