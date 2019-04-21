#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import argparse
import datetime
import csv
import os
import re
import warnings
from plaso.cli import pinfo_tool
from plaso.cli import tools
import plaso.lib.errors
import json
from google.cloud import storage


class PlasoCIFetcher(object):
  """Fetches test files for Plaso continuous integration.

  Test files are stored in a GCS bucket the following heirachry:

  gs://<BUCKET NAME>/<RESULTS_ROOT>/<test_series_argument>/<test_number
  >/<output_file>

  Test series is called a "project" or "item" by Jenkins. The test number is
  called a "build number" in Jenkins.

  Test series example are "plaso-linux-e2e-studentpc1" and
  "plaso-windows-e2e-student_pc1".

  An example full path to a storage file is:
  gs://test-bucket/jenkins/build_results/plaso-linux-e2e-studentpc1/3
  /acserver.plaso
  """
  RESULTS_ROOT = 'jenkins/build_results'
  PLASO_FILE_EXTENSION = '.plaso'

  def __init__(
      self, bucket_name='', project_name='',
      storage_file_temporary_directory=''):
    """Initializes a class that fetches results from a Plaso test store.

    Args:
      bucket_name (str): name of the Google cloud storage bucket to fetch from.
      project_name (str): name of the Google cloud project to bill the API
          request to.
      storage_file_temporary_directory (str): path to a local directory to store
          files from continuous integration.
    """
    super(PlasoCIFetcher, self).__init__()
    self._storage_file_temporary_directory = storage_file_temporary_directory
    self._bucket_name = bucket_name
    self._project_name = project_name

  def _ParseTestBlobName(self, blob_name):
    """Extracts fields from a GCS blob.

    Args:
      blob_name (str): name of the blob.

    Returns:
      str: test series
      int: build number
      str: file name.
    """
    if not blob_name.startswith(self.RESULTS_ROOT):
      raise ValueError(
          'Invalid blob name {0:s} does not start with {1:s}'.format(blob_name,
              self.RESULTS_ROOT))

    blob_name = blob_name[len(self.RESULTS_ROOT) + 1:]
    try:
      fields = blob_name.split('/')
      if fields[1] == 'gold':
        return fields[0], 0, fields[-1]

      test_series = fields[0]
      test_number = int(fields[1], 10)
      file_name = fields[-1]
    except ValueError:
      return None, 0, None
    return test_series, test_number, file_name

  def DownloadTestFiles(self, test_series, suffix, minimum_test_number=0):
    """

    Args:
      test_series (str): name of test series to get storage files for.
      suffix: TODO
      minimum_test_number: TODO

    Yields:
      Blob: a Google Cloud Storage blob.
    """
    with warnings.catch_warnings():
      warnings.simplefilter('ignore')
      storage_client = storage.Client(project=self._project_name)
      bucket = storage_client.get_bucket(self._bucket_name)
      prefix = '{0:s}/{1:s}/'.format(self.RESULTS_ROOT, test_series)
      for blob in bucket.list_blobs(prefix=prefix):
        if minimum_test_number:
          _, test_number, _ = self._ParseTestBlobName(blob.name)
          if test_number < minimum_test_number:
            continue
        if blob.name.endswith(suffix):
          yield blob

  def GetPinfoOutput(self, test_series, minimum_test_number=0):
    """Iterates over pinfo output files for an end-to-end test.

    Args:
      test_series (str): name of test series to get test output files for.
      minimum_test_number (int): TODO

    Yields:
      names of all pinfo output files for the given test.
    """
    for blob in self.DownloadTestFiles(
        test_series, '-pinfo.out', minimum_test_number=minimum_test_number):
      yield blob

  def GetStorageFileBlobs(self, test_series, minimum_test_number=0):
    """Iterates over plaso storage files for an end-to-end test.

    Args:
      test_series (str): name of test series to get storage files for.
      minimum_test_number: TODO


    Yields:
      names of all .plaso storage files for the given test.
    """
    for blob in self.DownloadTestFiles(
        test_series, self.PLASO_FILE_EXTENSION, minimum_test_number=minimum_test_number):
      yield blob

  def _GetNameForBlob(self, blob):
    """Sanitizes a blob name into something that can be a path."""
    return blob.name.replace('/', '!')

  def DownloadPinfoFiles(self, test_series, minimum_test_number=0):
    """Downloads all pinfo files for a given test.

    Args:
      test_series (str): name of test series to get pinfo files for.
      minimum_test_number: TODO


    Yields:
      str: path to a downloaded pinfo file.
    """
    storage_file_dir = os.path.join(self._storage_file_temporary_directory,
        test_series)
    try:
      os.makedirs(storage_file_dir)
    except OSError:
      # Directory already exists.
      pass

    for blob in self.GetPinfoOutput(test_series, minimum_test_number=minimum_test_number):
      temp_name = self._GetNameForBlob(blob)
      blob_path = os.path.join(storage_file_dir, temp_name)
      if os.path.exists(blob_path):
        print('Not downloading {0:s}. File already exists.'.format(blob_path))
        yield blob_path
        continue
      with open(blob_path, 'wb') as file_object:
        print('Downloading file {0:s}'.format(temp_name))
        blob.download_to_file(file_object)
      yield blob_path

  def DownloadTestFile(self, test_series, test_number, suffix):
    """

    Args:
      test_series (str): name of test series to get storage files for.
      test_number (int): test number to fetch files from.
      suffix: TODO

    Returns:
      str: path to a downloaded plaso file.
    """
    storage_file_directory = os.path.join(
        self._storage_file_temporary_directory,
        test_series)
    try:
      os.makedirs(storage_file_directory)
    except OSError:
      # Directory already exists.
      pass

    with warnings.catch_warnings():
      warnings.simplefilter('ignore')
      storage_client = storage.Client(project=self._project_name)
      bucket = storage_client.get_bucket(self._bucket_name)
      prefix = '{0:s}/{1:s}/{2:d}/'.format(
          self.RESULTS_ROOT, test_series, test_number)
      for blob in bucket.list_blobs(prefix=prefix):
        if blob.name.endswith(suffix):
          temp_name = self._GetNameForBlob(blob)
          blob_path = os.path.join(storage_file_directory, temp_name)
          if os.path.exists(blob_path):
            print('Not downloading {0:s}. File already exists.'.format(blob_path))
            return blob_path
          print('Downloading file {0:s}'.format(temp_name))
          with open(blob_path, 'wb') as file_object:
            blob.download_to_file(file_object)
          return blob_path
    return None

  def DownloadStorageFile(self, test_series, test_number):
    """Downloads a storage file for a given test series and test number.

    Args:
      test_series (str): name of the test series to download a storage file
      from.
      test_number (int): the test number to fetch a storage file from.

    Returns:
      str: path to a storage file or None.
    """
    return self.DownloadTestFile(
        test_series, test_number, suffix=self.PLASO_FILE_EXTENSION)

  def DownloadStorageFiles(self, test_series):
    """Downloads all the storage files for a given test.

    Args:
      test_series (str): name of the test series to download pinfo files from.

    Yields:
      str: path to a downloaded plaso file.
    """
    storage_file_directory = os.path.join(
        self._storage_file_temporary_directory,
        test_series)
    try:
      os.makedirs(storage_file_directory)
    except OSError:
      # Directory already exists.
      pass
    for blob in self.GetStorageFileBlobs(test_series):
      temp_name = self._GetNameForBlob(blob)
      blob_path = os.path.join(storage_file_directory, temp_name)
      if os.path.exists(blob_path):
        print('Not downloading {0:s}. File already exists.'.format(blob_path))
        yield blob_path
        continue
      with open(blob_path, 'w') as file_object:
        print('Downloading file {0:s}'.format(temp_name))
        blob.download_to_file(file_object)
      yield blob_path

  def UploadMetadataFile(self, filename, test_series):
    """Uploads the results of processing back to the cloud bucket.

    Args:
      filename (str): name of a file to upload.
      test_series (str): name of test series to upload metadata file for.
    """
    storage_file_dir = os.path.join(self._storage_file_temporary_directory,
        test_series)
    if not filename.startswith(storage_file_dir):
      raise ValueError
    translated_name = filename.replace('!', '/')
    translated_name = translated_name.replace(storage_file_dir, '')
    with warnings.catch_warnings():
      warnings.simplefilter('ignore')
      storage_client = storage.Client(project=self._project_name)
      bucket = storage_client.get_bucket(self._bucket_name)
      print('Uploading file {0:s}'.format(filename))
      blob = bucket.blob(translated_name)
      blob.upload_from_filename(filename)


def ProcessTest(test_series, project_name='', bucket_name='',
    storage_file_temporary_directory=''):
  """

  Args:
    bucket_name (str): name of the Google cloud storage bucket to fetch from.
    test_series (str): name of the test series to process.
    project_name (str): name of the Google cloud project the bucket belongs
        to.
    storage_file_temporary_directory (str): path to a local directory to store
        files from continuous integration.
  """
  fetcher = PlasoCIFetcher(project_name=project_name,
      storage_file_temporary_directory=storage_file_temporary_directory,
      bucket_name=bucket_name)
  list(fetcher.DownloadPinfoFiles(test_series))
  for storage_file in fetcher.DownloadPinfoFiles(test_series):
    filename, _, _ = storage_file.partition('.')
    output_path = '{0:s}.{1:s}'.format(filename, 'json')
    if os.path.exists(output_path):
      continue
    try:
      with open(output_path, 'w') as output_file:
        output_writer = tools.FileObjectOutputWriter(output_file)
        tool = pinfo_tool.PinfoTool(output_writer=output_writer)
        tool._storage_file_path = storage_file
        tool._output_format = 'json'
        tool.PrintStorageInformation()
    except plaso.lib.errors.BadConfigOption:
      # File couldn't be processed.
      os.unlink(output_path)
      continue

    fetcher.UploadMetadataFile(output_path, test_series)


def BuildCSV(test_series, storage_file_temporary_directory, metric_file_name):
  """Builds a CSV file with a

  Args:
    test_series (str): name of test series to build a CSV for.
    storage_file_temporary_directory (str): path to a local directory to store
        files from continuous integration.
    metric_file_name:
  """
  path = storage_file_temporary_directory
  fieldnames = ['test_number', 'start_date', 'elapsed_time',
    'number_of_parsers', 'total_events']
  metrics_rows = []
  storage_file_dir = os.path.join(storage_file_temporary_directory, test_series)
  for filename in os.listdir(storage_file_dir):
    file_path = '{0:s}/{1:s}/{2:s}'.format(path, test_series, filename)
    if '-pinfo.out' not in filename:
      continue
    if 'gold' in filename:
      continue
    test_number_match = re.search('!(\d+)!', filename)
    test_number = 0
    if test_number_match:
      test_number = test_number_match.group(1)

    with open(file_path, 'r') as metric_file:
      try:
        results = json.load(metric_file)
      except ValueError:
        print('Couldn\'t load {0:s}'.format(filename))
        continue
      session = results.items()[0][1]
      metrics_row = {}
      start_date = datetime.datetime.utcfromtimestamp(
          session['start_time'] / 1000000)
      elapsed_time = (session['completion_time'] - session[
        'start_time']) / 1000000
      enabled_parser_names = session.get('enabled_parser_names', [])
      number_of_parsers = len(enabled_parser_names)

      # Add counts from parsers
      for parser_name, event_count in session['parsers_counter'].items():
        if parser_name in ['__type__', 'total']:
          continue
        if event_count > 0:
          csv_field_name = '{0:s}_events'.format(parser_name)
          if csv_field_name not in fieldnames:
            fieldnames.append(csv_field_name)
          metrics_row[csv_field_name] = event_count

      events_counter = session['parsers_counter']
      del events_counter['__type__']
      del events_counter['total']
      total_events = sum(events_counter.values())
      metrics_row['test_number'] = test_number
      metrics_row['start_date'] = start_date
      metrics_row['elapsed_time'] = elapsed_time
      metrics_row['number_of_parsers'] = number_of_parsers
      metrics_row['total_events'] = total_events
      metrics_rows.append(metrics_row)

  metric_file_name = os.path.join('/tmp', metric_file_name)
  with open(metric_file_name, 'w') as csvfile:
    csvwriter = csv.DictWriter(csvfile, fieldnames=fieldnames, restval=0)
    csvwriter.writeheader()
    rows = sorted(metrics_rows)
    for row in rows:
      csvwriter.writerow(row)


if __name__ == '__main__':
  argument_parser = argparse.ArgumentParser()

  argument_parser.add_argument(
      'temporary_directory', type=str,
      help='Path to a temporary directory to cache storage files')

  argument_parser.add_argument(
      'project_name', type=str,
      help='Project where the tests were run')

  argument_parser.add_argument(
      'bucket_name', type=str,
      help='Bucket where test results are stored')

  argument_parser.add_argument(
      'test_seriess', type=str,
      help='Comma separated list of test names to process')

  options = argument_parser.parse_args()

  # test_seriess = [
  #  'plaso_registrar_end_to_end', 'plaso_studentpc1_end_to_end',
  #  'plaso_dean_end_to_end', 'plaso_acserver_end_to_end',
  #  'plaso_end_to_end_windows_studentpc1']
  # test_series_argument = ['plaso_registrar_end_to_end']
  # test_series_argument = ['plaso-e2e-registrar-sqlite']
  # test_series_argument = ['plaso-e2e-registrar']
  # test_series_argument = ['plaso-linux-e2e-registrar']
  test_seriess = options.test_seriess.split(',')
  for test in test_series:
    ProcessTest(test, project_name=options.project_name,
        bucket_name=options.bucket_name,
        storage_file_temporary_directory=options.temporary_directory)
    output_name = '{0:s}_metrics.csv'.format(test)
    BuildCSV(test, storage_file_temporary_directory=options.temporary_directory,
        metric_file_name=output_name)
