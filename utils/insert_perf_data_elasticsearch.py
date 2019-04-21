#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals
import argparse

import os
import re
import json
import datetime

import elasticsearch

from plaso.cli import pinfo_tool
from tests.cli import test_lib

from utils.build_performance_csv import PlasoCIFetcher



class ElasticImporter(object):
  """Inserts documents into an elasticsearch index."""

  def __init__(self, host='localhost', port=9200,
      index='plaso_test_summaries2'):
    """Initializes an elastic importer.

    Args:
      host (Optional[str]): hostname of the elasticsearch server.
      port (Optional[int]): port the elasticsearch server is listening on.
      index (Optional[str]): elastiosearch index name.
    """
    super(ElasticImporter, self).__init__()
    self._client = elasticsearch.Elasticsearch([{'host': host, 'port': port}])
    self._index_name = index
    self._doc_type = 'test-summary-v2'
    self._CreateIndex()
    self._UpdateMapping()

  def AddTestResult(self, test_series, test_number, document):
    """Adds a test result to the elasticsearch index.

    Args:
      test_series (str): name of the test
      test_number (int): number of the build of the test
      document (dict): JSON document describing the test result
    """
    identifier = '{0:s}-{1:d}'.format(test_series, test_number)
    try:
      resource = self._client.index(
          index=self._index_name, doc_type=self._doc_type, body=document,
          id=identifier)
    except elasticsearch.exceptions.RequestError as exception:
      print(exception)
      return

    print(resource)

  def _CreateIndex(self):
    """Creates an index."""
    if not self._client.indices.exists(self._index_name):
      self._client.indices.create(self._index_name)

  def _UpdateMapping(self):
    """Updates the elasticsearch mapping."""
    self._client.indices.put_mapping(
        index=self._index_name,
        doc_type=self._doc_type,
        body={
          "properties": {
            "test_series": {
              "type": "keyword",
              "doc_values": True
            },
            "test_number": {
              "type": "long"
            }
          }
        })

  def GetLatestTestNumber(self, test_series):
    try:
      results = self._client.search(
          index=self._index_name,
          q='test_series:"{0:s}"'.format(test_series),
          sort='test_number:desc', size=1)
    except elasticsearch.exceptions.RequestError:
      return 0

    # The elasticsearch result isn't very strongly structured...
    try:
      test_number = results['hits']['hits'][0]['_source']['test_number']
      return test_number
    except (KeyError, IndexError):
      return 0



class TestReader(object):
  """Reads pinfo test files."""

  def DownloadAndRunPinfo(self, fetcher, test_series, test_number,
      cleanup=True):
    """Downloads a storage file and runs pinfo on it.

    Args:
      fetcher (PlasoCIFetcher): TODO
      test_series (str): TODO
      test_number (int): TODO
      cleanup (bool): TODO

    Returns:
      str: JSON pinfo output or None.
    """
    path = fetcher.DownloadStorageFile(test_series, test_number)
    if not path:
      return None
    output = self.RunPinfo(path)
    if cleanup:
      os.unlink(path)
    return output

  def ReadTests(self, fetcher, temporary_directory, elastic_importer,
      minimum_test_number=0):
    """Reads tests result data from a temporary directory.

    Args:
      fetcher (PlasoCIFetcher): TODO
      temporary_directory (str): path to a directory containing test results.
      elastic_importer (ElasticImporter): instance of elastic inserter client.
    """
    for test_directory in os.listdir(temporary_directory):
      test_path = '{0:s}/{1:s}/'.format(temporary_directory, test_directory)
      if not os.path.isdir(test_path):
        continue
      for filename in os.listdir(test_path):
        if not filename.endswith('-pinfo.out'):
          continue
        test_series_and_number_match = re.search('!([\w\-]+)!(\d+)!', filename)
        test_series = ''
        test_number = 0
        if test_series_and_number_match:
          test_series = test_series_and_number_match.group(1)
          test_number = test_series_and_number_match.group(2)
          test_number = int(test_number)
          if minimum_test_number and test_number < minimum_test_number:
            continue
        file_path = '{0:s}/{1:s}/{2:s}'.format(
            temporary_directory, test_directory, filename)
        with open(file_path, 'r') as pinfo_file:
          try:
            pinfo_output = json.load(pinfo_file)
          except ValueError:
            print('Unable to load {0:s}'.format(filename))
            continue
          document = self.BuildTestDocument(pinfo_output, test_directory,
              test_number)

          # Parsing the pinfo output failed, so we'll try regenerating it.
          if not document:
            pinfo_output = self.DownloadAndRunPinfo(fetcher, test_series,
                test_number)
            try:
              pinfo_output = json.loads(pinfo_output)
            except json.decoder.JSONDecodeError:
              pinfo_output = None
            if pinfo_output:
              document = self.BuildTestDocument(pinfo_output, test_directory,
                  test_number)
          if document:
            elastic_importer.AddTestResult(test_directory, test_number,
                document)

  def RunPinfo(self, storage_file_path):
    """Runs pinfo on a test file.

    Args:
      storage_file_path (str): path to a storage file to run pinfo on.

    Returns:
      str: JSON formatted output.
    """
    print('Running pinfo')
    output_writer = test_lib.TestOutputWriter()
    options = test_lib.TestOptions()
    options.storage_file = storage_file_path
    options.output_format = 'json'
    tool = pinfo_tool.PinfoTool(output_writer=output_writer)
    tool.ParseOptions(options)
    tool.PrintStorageInformation()
    output = output_writer.ReadOutput()
    return output

  def BuildTestDocument(self, pinfo_output, test_series, test_number):
    """Builds a JSON to represent the results of a test.

    The test document structure looks like this:

    {
      "test_series": "plaso-linux-e2e-studentpc1",
      "test_number": 11,
      "start_date": "2019-01-01T00:00",
      "elapsed_time": 600,
      "number_of_parsers": 4,
      "total_events": 100,
      "events": {
        "filestat_events": 50,
        "syslog_events": 25,
        "syslog/ssh_events": 25
      }
    }

    Args:
      pinfo_output (str): JSON output from pinfo.
      test_series (str): name of the test.
      test_number (int): number of the build of the test

    Returns:
      JSON document.
    """

    fieldnames = ['test_number', 'start_date', 'elapsed_time',
      'number_of_parsers', 'total_events']

    document = {
      'test_series': test_series,
      'test_number': test_number,
    }
    if 'sessions' not in pinfo_output:
      return None

    elapsed_time = 0
    start_dates = []
    sessions = pinfo_output['sessions']
    for session_identifier, session in sessions.items():
      start_date = datetime.datetime.utcfromtimestamp(
          session['start_time'] / 1000000)
      start_dates.append(start_date)
      elapsed_time += (session['completion_time'] - session[
        'start_time']) / 1000000
      enabled_parser_names = session.get('enabled_parser_names', [])
      number_of_parsers = len(enabled_parser_names)

    # Add counts from parsers
    events = {}
    for parser_name, event_count in session['parsers_counter'].items():
      if parser_name in ['__type__', 'total']:
        continue
      if event_count > 0:
        csv_field_name = '{0:s}_events'.format(parser_name)
        if csv_field_name not in fieldnames:
          fieldnames.append(csv_field_name)
        events[csv_field_name] = event_count

    counters = pinfo_output['storage_counters']

    events_counter = counters['parsers']
    del events_counter['total']
    total_events = sum(events_counter.values())

    warnings_by_parser_chain = counters['warnings_by_parser_chain']
    warnings_by_parser_chain['<no parser>'] = warnings_by_parser_chain.pop('')
    total_warnings = sum(warnings_by_parser_chain.values())

    warnings_by_pathspec = counters['warnings_by_path_spec']
    pathspecs_with_warnings = warnings_by_pathspec.keys()

    document['test_number'] = test_number
    document['@timestamp'] = document['start_date'] = min(start_dates)
    document['elapsed_time'] = elapsed_time
    document['number_of_parsers'] = number_of_parsers
    document['total_events'] = total_events
    document['total_warnings'] = total_warnings
    document['warnings_by_parser_chain'] = warnings_by_parser_chain
    document['pathspecs_with_warnings'] = list(pathspecs_with_warnings)
    document['events'] = events

    return document


if __name__ == '__main__':
  argument_parser = argparse.ArgumentParser()

  argument_parser.add_argument(
      '--project_name', type=str,
      help='Project where the tests were run')

  argument_parser.add_argument(
      '--bucket_name', type=str,
      help='Bucket where test results are stored')

  argument_parser.add_argument(
      '--test_series', type=str,
      help='Comma separated list of test series to process')

  argument_parser.add_argument('--temporary_directory', type=str,
      help='Path to a temporary directory where storage files are cached')

  argument_parser.add_argument('--host', type=str, default='localhost',
      help='hostname or IP address of the elasticsearch server.')

  options = argument_parser.parse_args()

  fetcher = PlasoCIFetcher(
      options.bucket_name, options.project_name, options.temporary_directory)
  importer = ElasticImporter(host=options.host)

  test_series_argument = options.test_series.split(',')
  for series in test_series_argument:
    minimum_test_number = importer.GetLatestTestNumber(series)
    _ = list(fetcher.DownloadPinfoFiles(
        series, minimum_test_number=minimum_test_number))

  reader = TestReader()
  reader.ReadTests(fetcher, options.temporary_directory, importer,
      minimum_test_number=minimum_test_number)
