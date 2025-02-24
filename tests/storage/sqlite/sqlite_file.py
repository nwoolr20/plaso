#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the SQLite-based storage."""

import os
import unittest

from plaso.containers import events
from plaso.containers import sessions
from plaso.containers import tasks
from plaso.lib import definitions
from plaso.storage.sqlite import sqlite_file

from tests import test_lib as shared_test_lib
from tests.containers import test_lib as containers_test_lib
from tests.storage import test_lib


class _TestSQLiteStorageFileV1(sqlite_file.SQLiteStorageFile):
  """Test class for testing format compatibility checks."""

  _FORMAT_VERSION = 1
  _APPEND_COMPATIBLE_FORMAT_VERSION = 1
  _READ_COMPATIBLE_FORMAT_VERSION = 1


class _TestSQLiteStorageFileV2(sqlite_file.SQLiteStorageFile):
  """Test class for testing format compatibility checks."""

  _FORMAT_VERSION = 2
  _APPEND_COMPATIBLE_FORMAT_VERSION = 2
  _READ_COMPATIBLE_FORMAT_VERSION = 1


class SQLiteStorageFileTest(test_lib.StorageTestCase):
  """Tests for the SQLite-based storage file object."""

  # pylint: disable=protected-access

  def testInitialization(self):
    """Tests the __init__ function."""
    test_store = sqlite_file.SQLiteStorageFile()
    self.assertIsNotNone(test_store)

  def testCacheAttributeContainerByIndex(self):
    """Tests the _CacheAttributeContainerByIndex function."""
    event_data_stream = events.EventDataStream()

    with shared_test_lib.TempDirectory():
      test_store = sqlite_file.SQLiteStorageFile()

      self.assertEqual(len(test_store._attribute_container_cache), 0)

      test_store._CacheAttributeContainerByIndex(event_data_stream, 0)
      self.assertEqual(len(test_store._attribute_container_cache), 1)

  def testCheckStorageMetadata(self):
    """Tests the _CheckStorageMetadata function."""
    with shared_test_lib.TempDirectory():
      test_store = sqlite_file.SQLiteStorageFile()

      metadata_values = {
          'compression_format': definitions.COMPRESSION_FORMAT_ZLIB,
          'format_version': '{0:d}'.format(test_store._FORMAT_VERSION),
          'serialization_format': definitions.SERIALIZER_FORMAT_JSON,
          'storage_type': definitions.STORAGE_TYPE_SESSION}
      test_store._CheckStorageMetadata(metadata_values)

      metadata_values['format_version'] = 'bogus'
      with self.assertRaises(IOError):
        test_store._CheckStorageMetadata(metadata_values)

      metadata_values['format_version'] = '1'
      with self.assertRaises(IOError):
        test_store._CheckStorageMetadata(metadata_values)

      metadata_values['format_version'] = '{0:d}'.format(
          test_store._FORMAT_VERSION)
      metadata_values['compression_format'] = None
      with self.assertRaises(IOError):
        test_store._CheckStorageMetadata(metadata_values)

      metadata_values['compression_format'] = (
          definitions.COMPRESSION_FORMAT_ZLIB)
      metadata_values['serialization_format'] = None
      with self.assertRaises(IOError):
        test_store._CheckStorageMetadata(metadata_values)

      metadata_values['serialization_format'] = (
          definitions.SERIALIZER_FORMAT_JSON)
      metadata_values['storage_type'] = None
      with self.assertRaises(IOError):
        test_store._CheckStorageMetadata(metadata_values)

  def testCreateAttributeContainerTable(self):
    """Tests the _CreateAttributeContainerTable function."""
    event_data_stream = events.EventDataStream()

    with shared_test_lib.TempDirectory() as temp_directory:
      test_path = os.path.join(temp_directory, 'plaso.sqlite')
      test_store = sqlite_file.SQLiteStorageFile()
      test_store.Open(path=test_path, read_only=False)

      with self.assertRaises(IOError):
        test_store._CreateAttributeContainerTable(
            event_data_stream.CONTAINER_TYPE)

      test_store.Close()

  # TODO: add tests for _CreatetAttributeContainerFromRow

  # TODO: add tests for _GetAttributeContainersWithFilter

  def testGetCachedAttributeContainer(self):
    """Tests the _GetCachedAttributeContainer function."""
    event_data_stream = events.EventDataStream()

    with shared_test_lib.TempDirectory():
      test_store = sqlite_file.SQLiteStorageFile()

      attribute_container = test_store._GetCachedAttributeContainer(
          event_data_stream.CONTAINER_TYPE, 1)
      self.assertIsNone(attribute_container)

      test_store._CacheAttributeContainerByIndex(event_data_stream, 1)

      attribute_container = test_store._GetCachedAttributeContainer(
          event_data_stream.CONTAINER_TYPE, 1)
      self.assertIsNotNone(attribute_container)

  def testHasTable(self):
    """Tests the _HasTable function."""
    with shared_test_lib.TempDirectory() as temp_directory:
      test_path = os.path.join(temp_directory, 'plaso.sqlite')
      test_store = sqlite_file.SQLiteStorageFile()
      test_store.Open(path=test_path, read_only=False)

      result = test_store._HasTable(
          test_store._CONTAINER_TYPE_EVENT_DATA_STREAM)
      self.assertTrue(result)

      result = test_store._HasTable('bogus')
      self.assertFalse(result)

      test_store.Close()

  # TODO: add tests for _RaiseIfNotReadable
  # TODO: add tests for _RaiseIfNotWritable
  # TODO: add tests for _ReadAndCheckStorageMetadata
  # TODO: add tests for _SerializeAttributeContainer
  # TODO: add tests for _UpdateAttributeContainerAfterDeserialize
  # TODO: add tests for _UpdateAttributeContainerBeforeSerialize
  # TODO: add tests for _UpdateEventAfterDeserialize
  # TODO: add tests for _UpdateEventBeforeSerialize
  # TODO: add tests for _UpdateEventDataAfterDeserialize
  # TODO: add tests for _UpdateEventDataBeforeSerialize
  # TODO: add tests for _UpdateEventTagAfterDeserialize
  # TODO: add tests for _UpdateEventTagBeforeSerialize
  # TODO: add tests for _UpdateStorageMetadataFormatVersion

  def testWriteExistingAttributeContainer(self):
    """Tests the _WriteExistingAttributeContainer function."""
    event_data_stream = events.EventDataStream()

    with shared_test_lib.TempDirectory() as temp_directory:
      test_path = os.path.join(temp_directory, 'plaso.sqlite')
      test_store = sqlite_file.SQLiteStorageFile()
      test_store.Open(path=test_path, read_only=False)

      number_of_containers = test_store.GetNumberOfAttributeContainers(
          event_data_stream.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 0)

    with self.assertRaises(IOError):
      test_store._WriteExistingAttributeContainer(event_data_stream)

      test_store._WriteNewAttributeContainer(event_data_stream)

      number_of_containers = test_store.GetNumberOfAttributeContainers(
          event_data_stream.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 1)

      test_store._WriteExistingAttributeContainer(event_data_stream)

      number_of_containers = test_store.GetNumberOfAttributeContainers(
          event_data_stream.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 1)

      test_store.Close()

  # TODO: add tests for _WriteMetadata
  # TODO: add tests for _WriteMetadataValue

  def testWriteNewAttributeContainer(self):
    """Tests the _WriteNewAttributeContainer function."""
    event_data_stream = events.EventDataStream()

    with shared_test_lib.TempDirectory() as temp_directory:
      test_path = os.path.join(temp_directory, 'plaso.sqlite')
      test_store = sqlite_file.SQLiteStorageFile()
      test_store.Open(path=test_path, read_only=False)

      number_of_containers = test_store.GetNumberOfAttributeContainers(
          event_data_stream.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 0)

      test_store._WriteNewAttributeContainer(event_data_stream)

      number_of_containers = test_store.GetNumberOfAttributeContainers(
          event_data_stream.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 1)

      test_store.Close()

  def testAddAttributeContainer(self):
    """Tests the AddAttributeContainer function."""
    event_data_stream = events.EventDataStream()

    with shared_test_lib.TempDirectory() as temp_directory:
      test_path = os.path.join(temp_directory, 'plaso.sqlite')
      test_store = sqlite_file.SQLiteStorageFile()
      test_store.Open(path=test_path, read_only=False)

      number_of_containers = test_store.GetNumberOfAttributeContainers(
          event_data_stream.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 0)

      test_store.AddAttributeContainer(event_data_stream)

      number_of_containers = test_store.GetNumberOfAttributeContainers(
          event_data_stream.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 1)

      test_store.Close()

      with self.assertRaises(IOError):
        test_store.AddAttributeContainer(event_data_stream)

  # TODO: add tests for CheckSupportedFormat

  def testGetAttributeContainers(self):
    """Tests the GetAttributeContainers function."""
    event_data_stream = events.EventDataStream()

    with shared_test_lib.TempDirectory() as temp_directory:
      test_path = os.path.join(temp_directory, 'plaso.sqlite')
      test_store = sqlite_file.SQLiteStorageFile()
      test_store.Open(path=test_path, read_only=False)

      containers = list(test_store.GetAttributeContainers(
          event_data_stream.CONTAINER_TYPE))
      self.assertEqual(len(containers), 0)

      test_store.AddAttributeContainer(event_data_stream)

      containers = list(test_store.GetAttributeContainers(
          event_data_stream.CONTAINER_TYPE))
      self.assertEqual(len(containers), 1)

      with self.assertRaises(IOError):
        list(test_store.GetAttributeContainers('bogus'))

      test_store.Close()

  def testGetAttributeContainerByIdentifier(self):
    """Tests the GetAttributeContainerByIdentifier function."""
    event_data_stream = events.EventDataStream()

    with shared_test_lib.TempDirectory() as temp_directory:
      test_path = os.path.join(temp_directory, 'plaso.sqlite')
      test_store = sqlite_file.SQLiteStorageFile()
      test_store.Open(path=test_path, read_only=False)

      test_store.AddAttributeContainer(event_data_stream)
      identifier = event_data_stream.GetIdentifier()

      container = test_store.GetAttributeContainerByIdentifier(
          event_data_stream.CONTAINER_TYPE, identifier)
      self.assertIsNotNone(container)

      identifier.sequence_number = 99

      container = test_store.GetAttributeContainerByIdentifier(
          event_data_stream.CONTAINER_TYPE, identifier)
      self.assertIsNone(container)

      test_store.Close()

  def testGetAttributeContainerByIndex(self):
    """Tests the GetAttributeContainerByIndex function."""
    event_data_stream = events.EventDataStream()

    with shared_test_lib.TempDirectory() as temp_directory:
      test_path = os.path.join(temp_directory, 'plaso.sqlite')
      test_store = sqlite_file.SQLiteStorageFile()
      test_store.Open(path=test_path, read_only=False)

      container = test_store.GetAttributeContainerByIndex(
          event_data_stream.CONTAINER_TYPE, 0)
      self.assertIsNone(container)

      test_store.AddAttributeContainer(event_data_stream)

      container = test_store.GetAttributeContainerByIndex(
          event_data_stream.CONTAINER_TYPE, 0)
      self.assertIsNotNone(container)

      with self.assertRaises(IOError):
        test_store.GetAttributeContainerByIndex('bogus', 0)

      test_store.Close()

  def testGetEventTagByEventIdentifier(self):
    """Tests the GetEventTagByEventIdentifier function."""
    with shared_test_lib.TempDirectory() as temp_directory:
      test_path = os.path.join(temp_directory, 'plaso.sqlite')
      test_store = sqlite_file.SQLiteStorageFile()
      test_store.Open(path=test_path, read_only=False)

      index = 0
      for event, event_data, event_data_stream in (
          containers_test_lib.CreateEventsFromValues(self._TEST_EVENTS)):
        test_store.AddAttributeContainer(event_data_stream)

        event_data.SetEventDataStreamIdentifier(
            event_data_stream.GetIdentifier())
        test_store.AddAttributeContainer(event_data)

        event.SetEventDataIdentifier(event_data.GetIdentifier())
        test_store.AddAttributeContainer(event)

        if index == 1:
          event_tag = events.EventTag()
          event_tag.AddLabels(['Malware', 'Benign'])

          event_identifier = event.GetIdentifier()
          event_tag.SetEventIdentifier(event_identifier)
          test_store.AddAttributeContainer(event_tag)

        index += 1

      test_store.Close()

      test_store = sqlite_file.SQLiteStorageFile()
      test_store.Open(path=test_path)

      test_event = test_store.GetAttributeContainerByIndex(
          events.EventObject.CONTAINER_TYPE, 1)
      self.assertIsNotNone(test_event)

      test_event_identifier = test_event.GetIdentifier()
      self.assertIsNotNone(test_event_identifier)

      test_event_tag = test_store.GetEventTagByEventIdentifier(
          test_event_identifier)
      self.assertIsNotNone(test_event_tag)

      self.assertEqual(test_event_tag.labels, ['Malware', 'Benign'])

      test_store.Close()

  def testGetNumberOfAttributeContainers(self):
    """Tests the GetNumberOfAttributeContainers function."""
    event_data_stream = events.EventDataStream()

    with shared_test_lib.TempDirectory() as temp_directory:
      test_path = os.path.join(temp_directory, 'plaso.sqlite')
      test_store = sqlite_file.SQLiteStorageFile()
      test_store.Open(path=test_path, read_only=False)

      number_of_containers = test_store.GetNumberOfAttributeContainers(
          event_data_stream.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 0)

      test_store.AddAttributeContainer(event_data_stream)

      number_of_containers = test_store.GetNumberOfAttributeContainers(
          event_data_stream.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 1)

      with self.assertRaises(ValueError):
        test_store.GetNumberOfAttributeContainers('bogus')

      # Test for a supported container type that does not have a table
      # present in the storage file.
      query = 'DROP TABLE {0:s}'.format(event_data_stream.CONTAINER_TYPE)
      test_store._cursor.execute(query)
      number_of_containers = test_store.GetNumberOfAttributeContainers(
          event_data_stream.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 0)

      test_store.Close()

  # TODO: add tests for GetSessions

  def testGetSortedEvents(self):
    """Tests the GetSortedEvents function."""
    with shared_test_lib.TempDirectory() as temp_directory:
      test_path = os.path.join(temp_directory, 'plaso.sqlite')
      test_store = sqlite_file.SQLiteStorageFile()
      test_store.Open(path=test_path, read_only=False)

      for event, event_data, event_data_stream in (
          containers_test_lib.CreateEventsFromValues(self._TEST_EVENTS)):
        test_store.AddAttributeContainer(event_data_stream)

        event_data.SetEventDataStreamIdentifier(
            event_data_stream.GetIdentifier())
        test_store.AddAttributeContainer(event_data)

        event.SetEventDataIdentifier(event_data.GetIdentifier())
        test_store.AddAttributeContainer(event)

      test_store.Close()

      test_store = sqlite_file.SQLiteStorageFile()
      test_store.Open(path=test_path)

      test_events = list(test_store.GetSortedEvents())
      self.assertEqual(len(test_events), 4)

      test_store.Close()

    # TODO: add test with time range.

  def testHasAttributeContainers(self):
    """Tests the HasAttributeContainers function."""
    event_data_stream = events.EventDataStream()

    with shared_test_lib.TempDirectory() as temp_directory:
      test_path = os.path.join(temp_directory, 'plaso.sqlite')
      test_store = sqlite_file.SQLiteStorageFile()
      test_store.Open(path=test_path, read_only=False)

      result = test_store.HasAttributeContainers(
          event_data_stream.CONTAINER_TYPE)
      self.assertFalse(result)

      test_store.AddAttributeContainer(event_data_stream)

      result = test_store.HasAttributeContainers(
          event_data_stream.CONTAINER_TYPE)
      self.assertTrue(result)

      with self.assertRaises(ValueError):
        test_store.HasAttributeContainers('bogus')

      test_store.Close()

  # TODO: add tests for Open and Close

  def testUpdateAttributeContainer(self):
    """Tests the UpdateAttributeContainer function."""
    event_data_stream = events.EventDataStream()

    with shared_test_lib.TempDirectory() as temp_directory:
      test_path = os.path.join(temp_directory, 'plaso.sqlite')
      test_store = sqlite_file.SQLiteStorageFile()
      test_store.Open(path=test_path, read_only=False)

      number_of_containers = test_store.GetNumberOfAttributeContainers(
          event_data_stream.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 0)

    with self.assertRaises(IOError):
      test_store.UpdateAttributeContainer(event_data_stream)

      test_store.AddAttributeContainer(event_data_stream)

      number_of_containers = test_store.GetNumberOfAttributeContainers(
          event_data_stream.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 1)

      test_store.UpdateAttributeContainer(event_data_stream)

      number_of_containers = test_store.GetNumberOfAttributeContainers(
          event_data_stream.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 1)

      test_store.Close()

  def testWriteTaskStartAndCompletion(self):
    """Tests the WriteTaskStart and WriteTaskCompletion functions."""
    session = sessions.Session()
    task_start = tasks.TaskStart(session_identifier=session.identifier)
    task_completion = tasks.TaskCompletion(
        identifier=task_start.identifier,
        session_identifier=session.identifier)

    with shared_test_lib.TempDirectory() as temp_directory:
      test_path = os.path.join(temp_directory, 'plaso.sqlite')
      test_store = sqlite_file.SQLiteStorageFile(
          storage_type=definitions.STORAGE_TYPE_TASK)
      test_store.Open(path=test_path, read_only=False)

      test_store.WriteTaskStart(task_start)
      test_store.WriteTaskCompletion(task_completion)

      test_store.Close()

  def testVersionCompatibility(self):
    """Tests the version compatibility methods."""
    with shared_test_lib.TempDirectory() as temp_directory:
      v1_storage_path = os.path.join(temp_directory, 'v1.sqlite')
      v1_test_store = _TestSQLiteStorageFileV1(
          storage_type=definitions.STORAGE_TYPE_SESSION)
      v1_test_store.Open(path=v1_storage_path, read_only=False)
      v1_test_store.Close()

      v2_test_store_rw = _TestSQLiteStorageFileV2(
          storage_type=definitions.STORAGE_TYPE_SESSION)

      with self.assertRaises((IOError, OSError)):
        v2_test_store_rw.Open(path=v1_storage_path, read_only=False)

      v2_test_store_ro = _TestSQLiteStorageFileV2(
          storage_type=definitions.STORAGE_TYPE_SESSION)
      v2_test_store_ro.Open(path=v1_storage_path, read_only=True)
      v2_test_store_ro.Close()


if __name__ == '__main__':
  unittest.main()
