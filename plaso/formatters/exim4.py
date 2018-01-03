# -*- coding: utf-8 -*-
"""The exim4 file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class Exim4LineFormatter(interface.ConditionalEventFormatter):
  """Formatter for an exim4 line event."""

  DATA_TYPE = 'exim4:line'

  FORMAT_STRING_SEPARATOR = ''

  FORMAT_STRING_PIECES = [
      '{body}']

  SOURCE_LONG = 'Log File'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(Exim4LineFormatter)
