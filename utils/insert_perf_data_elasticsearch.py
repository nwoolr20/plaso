#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals
import argparse

import os
import re
import json
import datetime

import elasticsearch

class ElasticImporter(object):
  INDEX_NAME = 'plaso_test_summaries'

  def __init__(self, host='localhost', port=9200):
    super(ElasticImporter, self).__init__()
    self._client = elasticsearch.Elasticsearch([{'host': host, 'port': port}])

  def AddTestResult(self, test_name, build_number, document):
    """

    Args:
      test_name (str): name of the test
      build_number (int): number of the build of the test
      document (str): JSON document describing the test result
    """
    identifier = '{0:s}-{1:d}'.format(test_name, build_number)
    try:
      resource = self._client.index(
          index=self.INDEX_NAME, doc_type='test-summary', body=document,
          id=identifier)
    except elasticsearch.exceptions.RequestError as exception:
      print(exception)
      return

    print(resource)

class TestReader(object):

  def ReadTests(self, temporary_directory, elastic_importer):
    for test_dir in os.listdir(temporary_directory):
      test_path = '{0:s}/{1:s}/'.format(temporary_directory, test_dir)
      if not os.path.isdir(test_path):
        continue
      for filename in os.listdir(test_path):
        build_number_match = re.search('!(\d+)!', filename)
        build_number = 0
        if build_number_match:
          build_number = build_number_match.group(1)
          build_number = int(build_number)
        file_path = '{0:s}/{1:s}/{2:s}'.format(
            temporary_directory, test_dir, filename)
        with open(file_path, 'r') as metric_file:
          try:
            pinfo_output = json.load(metric_file)
          except ValueError:
            print('Couldn\'t load {0:s}'.format(filename))
            continue
          document = self.BuildTestDocument(pinfo_output, test_dir, build_number)
          elastic_importer.AddTestResult(test_dir, build_number, document)

  def BuildTestDocument(self, pinfo_output, test_name, build_number):
    fieldnames = ['build_number', 'start_date', 'elapsed_time',
      'number_of_parsers', 'total_events']
    document = {
      'test_name': test_name,
      'build_number': build_number,
    }
    session = pinfo_output.items()[0][1]
    start_date = datetime.datetime.utcfromtimestamp(
        session['start_time'] / 1000000)
    elapsed_time = (session['completion_time'] - session[
      'start_time']) / 10000
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

    events_counter = session['parsers_counter']
    del events_counter['__type__']
    del events_counter['total']
    total_events = sum(events_counter.values())
    document['build_number'] = build_number
    document['start_date'] = start_date
    document['elapsed_time'] = elapsed_time
    document['number_of_parsers'] = number_of_parsers
    document['total_events'] = total_events
    document['events'] = events

    return document



if __name__ == '__main__':
  argument_parser = argparse.ArgumentParser()

  argument_parser.add_argument('temporary_directory', type=str,
      help='Path to a temporary directory where storage files are cached')
  argument_parser.add_argument('host', type=str, default='localhost',
      help='hostname or IP address of the elasticsearch server.')
  options = argument_parser.parse_args()

  importer = ElasticImporter(host=options.host)
  reader = TestReader()
  reader.ReadTests(options.temporary_directory, importer)