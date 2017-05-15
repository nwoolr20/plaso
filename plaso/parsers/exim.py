# -*- coding: utf-8 -*-
"""Parser for exim4 formatted log files"""
import re

import pyparsing

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import manager
from plaso.parsers import text_parser


class Exim4LineEventData(events.EventData):
  """Exim4 line event data.

  Attributes:
    body (str): message body.
  """

  DATA_TYPE = u'exim4:line'

  def __init__(self, data_type=DATA_TYPE):
    """Initializes an event data attribute container.

    Args:
      data_type (Optional[str]): event data type indicator.
    """
    super(Exim4LineEventData, self).__init__(data_type=data_type)
    self.body = None

class Exim4Parser(text_parser.PyparsingSingleLineTextParser):
  """Parses exim4 formatted log files"""
  NAME = u'exim4'

  DESCRIPTION = u'Exim4 Parser'

  _ENCODING = u'utf-8'

  _plugin_classes = {}

  _BODY_CONTENT = (r'.*?(?=($|\n\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}))')

  _VERIFICATION_REGEX = \
      re.compile(r'^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\s' +
                 _BODY_CONTENT)

  _PYPARSING_COMPONENTS = {
      u'year': text_parser.PyparsingConstants.FOUR_DIGITS.setResultsName(
          u'year'),
      u'month': text_parser.PyparsingConstants.TWO_DIGITS.setResultsName(
          u'month'),
      u'day': text_parser.PyparsingConstants.TWO_DIGITS.setResultsName(
          u'day'),
      u'hour': text_parser.PyparsingConstants.TWO_DIGITS.setResultsName(
          u'hour'),
      u'minute': text_parser.PyparsingConstants.TWO_DIGITS.setResultsName(
          u'minute'),
      u'second': text_parser.PyparsingConstants.TWO_DIGITS.setResultsName(
          u'second'),
      u'body': pyparsing.Regex(_BODY_CONTENT, re.DOTALL).
               setResultsName(u'body')
  }

  _PYPARSING_COMPONENTS[u'date'] = (
      _PYPARSING_COMPONENTS[u'year'] + pyparsing.Suppress(u'-') +
      _PYPARSING_COMPONENTS[u'month'] + pyparsing.Suppress(u'-') +
      _PYPARSING_COMPONENTS[u'day'] +
      _PYPARSING_COMPONENTS[u'hour'] + pyparsing.Suppress(u':') +
      _PYPARSING_COMPONENTS[u'minute'] + pyparsing.Suppress(u':') +
      _PYPARSING_COMPONENTS[u'second'])

  _EXIM4_LINE = (
      _PYPARSING_COMPONENTS[u'date'] +
      pyparsing.Optional(pyparsing.Suppress(u':')) +
      _PYPARSING_COMPONENTS[u'body'] + pyparsing.lineEnd())

  LINE_STRUCTURES = [
      (u'exim4_line', _EXIM4_LINE)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in LINE_STRUCTURES])

  def __init__(self):
    """Initializes a parser object."""
    super(Exim4Parser, self).__init__()
    self._last_month = 0
    self._maximum_year = 0
    self._plugin_objects_by_reporter = {}
    self._year_use = 0

  def EnablePlugins(self, plugin_includes):
    """Enables parser plugins.

    Args:
      plugin_includes (list[str]): names of the plugins to enable, where None
          or an empty list represents all plugins. Note that the default plugin
          is handled separately.
    """
    super(Exim4Parser, self).EnablePlugins(plugin_includes)

    self._plugin_objects_by_reporter = {}
    for plugin_object in self._plugin_objects:
      self._plugin_objects_by_reporter[plugin_object.REPORTER] = plugin_object

  def ParseRecord(self, mediator, key, structure):
    """Parses a matching entry.

    Args:
      mediator (ParserMediator): mediates the interactions between
          parsers and other components, such as storage and abort signals.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): elements parsed from the file.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key not in self._SUPPORTED_KEYS:
      raise errors.ParseError(
          u'Unable to parse record, unknown structure: {0:s}'.format(key))

    timestamp = timelib.Timestamp.FromTimeParts(
        year=structure.year, month=structure.month, day=structure.day,
        hour=structure.hour, minutes=structure.minute,
        seconds=structure.second, timezone=mediator.timezone)

    plugin_object = None
    event_data = Exim4LineEventData()
    event_data.body = structure.body
    plugin_object = self._plugin_objects_by_reporter.get(
        structure.reporter, None)
    if plugin_object:
      attributes = {
          u'body': structure.body}
      try:
        # TODO: pass event_data instead of attributes.
        plugin_object.Process(mediator, timestamp, attributes)

      except errors.WrongPlugin:
        plugin_object = None

    if not plugin_object:
      event = time_events.TimestampEvent(
          timestamp, eventdata.EventTimestamp.WRITTEN_TIME)
      mediator.ProduceEventWithEventData(event, event_data)

  def VerifyStructure(self, unused_mediator, line):
    """Verifies that this is a exim4-formatted file.

    Args:
      mediator (ParserMediator): mediates the interactions between
          parsers and other components, such as storage and abort signals.
      line (str): single line from the text file.

    Returns:
      bool: whether the line appears to contain syslog content.
    """
    return re.match(self._VERIFICATION_REGEX, line) is not None


manager.ParsersManager.RegisterParser(Exim4Parser)
