#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the image export CLI tool."""

import os
import unittest

from plaso.cli import image_export_tool
from plaso.lib import errors

from tests import test_lib as shared_test_lib
from tests.cli import test_lib as test_lib


class ImageExportToolTest(test_lib.CLIToolTestCase):
  """Tests for the image export CLI tool."""

  # pylint: disable=protected-access

  def _RecursiveList(self, path):
    """Recursively lists a file or directory.

    Args:
      path (str): path of the file or directory to list.

    Returns:
      list[str]: names of files and sub directories within the path.
    """
    results = []
    for sub_path, _, files in os.walk(path):
      if sub_path != path:
        results.append(sub_path)

      for file_entry in files:
        results.append(os.path.join(sub_path, file_entry))

    return results

  def testListSignatureIdentifiers(self):
    """Tests the ListSignatureIdentifiers function."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    test_tool._data_location = self._TEST_DATA_PATH

    test_tool.ListSignatureIdentifiers()

    expected_output = (
        b'Available signature identifiers:\n'
        b'7z, bzip2, esedb, evt, evtx, ewf_e01, ewf_l01, exe_mz, gzip, lnk, '
        b'msiecf, nk2,\n'
        b'olecf, olecf_beta, pdf, pff, qcow, rar, regf, tar, tar_old, '
        b'vhdi_footer,\n'
        b'vhdi_header, wtcdb_cache, wtcdb_index, zip\n'
        b'\n')

    output = output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split(b'\n'), expected_output.split(b'\n'))

    test_tool._data_location = self._GetTestFilePath([u'tmp'])

    with self.assertRaises(errors.BadConfigOption):
      test_tool.ListSignatureIdentifiers()

  def testParseArguments(self):
    """Tests the ParseArguments function."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    result = test_tool.ParseArguments()
    self.assertFalse(result)

    # TODO: check output.
    # TODO: improve test coverage.

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.image = self._GetTestFilePath([u'image.qcow2'])

    test_tool.ParseOptions(options)

    options = test_lib.TestOptions()

    with self.assertRaises(errors.BadConfigOption):
      test_tool.ParseOptions(options)

    # TODO: improve test coverage.

  @shared_test_lib.skipUnlessHasTestFile([u'image.qcow2'])
  def testPrintFilterCollection(self):
    """Tests the PrintFilterCollection function."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.date_filters = [u'ctime,2012-05-25 15:59:00,2012-05-25 15:59:20']
    options.image = self._GetTestFilePath([u'image.qcow2'])
    options.quiet = True

    test_tool.ParseOptions(options)

    test_tool.PrintFilterCollection()

    expected_output = b'\n'.join([
        b'Filters:',
        (b'\tctime between 2012-05-25T15:59:00+00:00 and '
         b'2012-05-25T15:59:20+00:00'),
        b''])
    output = output_writer.ReadOutput()
    self.assertEqual(output, expected_output)

  def testProcessSourcesImage(self):
    """Tests the ProcessSources function on a single partition image."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.image = self._GetTestFilePath([u'ímynd.dd'])
    options.quiet = True

    with shared_test_lib.TempDirectory() as temp_directory:
      options.path = temp_directory

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

      expected_output = b'\n'.join([
          b'Export started.',
          b'Extracting file entries.',
          b'Export completed.',
          b'',
          b''])

      output = output_writer.ReadOutput()
      self.assertEqual(output, expected_output)

  @shared_test_lib.skipUnlessHasTestFile([u'image.qcow2'])
  def testProcessSourcesExtractWithDateTimeFilter(self):
    """Tests the ProcessSources function with a date time filter."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.date_filters = [u'ctime,2012-05-25 15:59:00,2012-05-25 15:59:20']
    options.image = self._GetTestFilePath([u'image.qcow2'])
    options.quiet = True

    with shared_test_lib.TempDirectory() as temp_directory:
      options.path = temp_directory

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

      expected_extracted_files = sorted([
          os.path.join(temp_directory, u'a_directory'),
          os.path.join(temp_directory, u'a_directory', u'a_file')])

      extracted_files = self._RecursiveList(temp_directory)
      self.assertEqual(sorted(extracted_files), expected_extracted_files)

  @shared_test_lib.skipUnlessHasTestFile([u'image.qcow2'])
  def testProcessSourcesExtractWithExtensionsFilter(self):
    """Tests the ProcessSources function with an extensions filter."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.extensions_string = u'txt'
    options.image = self._GetTestFilePath([u'image.qcow2'])
    options.quiet = True

    with shared_test_lib.TempDirectory() as temp_directory:
      options.path = temp_directory

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

      expected_extracted_files = sorted([
          os.path.join(temp_directory, u'passwords.txt')])

      extracted_files = self._RecursiveList(temp_directory)
      self.assertEqual(sorted(extracted_files), expected_extracted_files)

  @shared_test_lib.skipUnlessHasTestFile([u'image.qcow2'])
  def testProcessSourcesExtractWithNamesFilter(self):
    """Tests the ProcessSources function with a names filter."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.image = self._GetTestFilePath([u'image.qcow2'])
    options.names_string = u'another_file'
    options.quiet = True

    with shared_test_lib.TempDirectory() as temp_directory:
      options.path = temp_directory

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

      expected_extracted_files = sorted([
          os.path.join(temp_directory, u'a_directory'),
          os.path.join(temp_directory, u'a_directory', u'another_file')])

      extracted_files = self._RecursiveList(temp_directory)
      self.assertEqual(sorted(extracted_files), expected_extracted_files)

  @shared_test_lib.skipUnlessHasTestFile([u'image.qcow2'])
  def testProcessSourcesExtractWithFilter(self):
    """Tests the ProcessSources function with a filter file."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.image = self._GetTestFilePath([u'image.qcow2'])
    options.quiet = True

    with shared_test_lib.TempDirectory() as temp_directory:
      filter_file = os.path.join(temp_directory, u'filter.txt')
      with open(filter_file, 'wb') as file_object:
        file_object.write(b'/a_directory/.+_file\n')

      options.file_filter = filter_file
      options.path = temp_directory

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

      expected_extracted_files = sorted([
          os.path.join(temp_directory, u'filter.txt'),
          os.path.join(temp_directory, u'a_directory'),
          os.path.join(temp_directory, u'a_directory', u'another_file'),
          os.path.join(temp_directory, u'a_directory', u'a_file')])

      extracted_files = self._RecursiveList(temp_directory)

    self.assertEqual(sorted(extracted_files), expected_extracted_files)

  @shared_test_lib.skipUnlessHasTestFile([u'syslog_image.dd'])
  def testProcessSourcesExtractWithSignaturesFilter(self):
    """Tests the ProcessSources function with a signatures filter."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.image = self._GetTestFilePath([u'syslog_image.dd'])
    options.quiet = True
    options.signature_identifiers = u'gzip'

    with shared_test_lib.TempDirectory() as temp_directory:
      options.path = temp_directory

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

      expected_extracted_files = sorted([
          os.path.join(temp_directory, u'logs'),
          os.path.join(temp_directory, u'logs', u'sys.tgz')])

      extracted_files = self._RecursiveList(temp_directory)
      self.assertEqual(sorted(extracted_files), expected_extracted_files)


if __name__ == '__main__':
  unittest.main()
