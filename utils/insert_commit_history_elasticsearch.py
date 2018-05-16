#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import json
import elasticsearch
import argparse
import requests


class ElasticInserter(object):

  def __init__(self, host='localhost', port=9200, index='plaso_commits'):
    super(ElasticInserter, self).__init__()
    self._client = elasticsearch.Elasticsearch([{'host': host, 'port': port}])
    self._index_name = index
    self._doc_type = 'commit'

  def AddCommit(self, commit):
    identifier = commit['sha']
    try:
      resource = self._client.index(
          index=self._index_name, doc_type=self._doc_type, body=commit,
          id=identifier)
    except elasticsearch.exceptions.RequestError as exception:
      print(exception)
      return

    print(resource)


class GithubFetcher(object):

  def GetCommits(self):
    request = requests.get(
        'https://api.github.com/repos/log2timeline/plaso/commits')
    if not request.ok:
      return []
    commit_documents = json.loads(request.content)
    return commit_documents


if __name__ == '__main__':
  argument_parser = argparse.ArgumentParser()

  argument_parser.add_argument('--host', type=str, default='localhost',
      help='hostname or IP address of the elasticsearch server.')

  options = argument_parser.parse_args()

  inserter = ElasticInserter(host=options.host)
  fetcher = GithubFetcher()
  commits = fetcher.GetCommits()
  for commit in commits:
    inserter.AddCommit(commit)
