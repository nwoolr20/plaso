#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the exim4 file event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import exim4

from tests.formatters import test_lib


class Exim4LineFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the exim4 line event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = exim4.Exim4LineFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = exim4.Exim4LineFormatter()

    expected_attribute_names = [
        'body']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

    # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
