#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import json
import elasticsearch
import argparse
import requests


class ElasticInserter(object):

  def __init__(self, host='localhost', port=9200, index='commits'):
    super(ElasticInserter, self).__init__()
    self._client = elasticsearch.Elasticsearch([{'host': host, 'port': port}])
    self._index_name = index
    self._doc_type = 'commit'
    self._CreateIndex()
    self._UpdateMapping()

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

  def _CreateIndex(self):
    if not self._client.indices.exists(self._index_name):
      self._client.indices.create(self._index_name)

  def _UpdateMapping(self):
    self._client.indices.put_mapping(
        index=self._index_name,
        doc_type=self._doc_type,
        body={
          "properties": {
            "project_path": {
              "type": "keyword",
              "doc_values": True
            }
          }
        })


class GithubFetcher(object):

  def __init__(self, project_path):
    self.project_path = project_path

  def GetCommits(self):
    request = requests.get(
        'https://api.github.com/repos/{0:s}/commits?sha=master'.format(
            self.project_path))
    if not request.ok:
      return []
    commit_documents = json.loads(request.content)
    return commit_documents

  def BuildCommitDocument(self, commit):
    timestamp = commit['commit']['committer']['date']
    commit['@timestamp'] = timestamp
    commit['project_path'] = self.project_path
    return commit


if __name__ == '__main__':
  argument_parser = argparse.ArgumentParser()

  argument_parser.add_argument('--host', type=str, default='localhost',
      help='hostname or IP address of the elasticsearch server.')

  argument_parser.add_argument('--project_path', type=str,
      default='log2timeline/plaso',
      help='Github path of project (eg. log2timeline/plaso).')

  options = argument_parser.parse_args()

  inserter = ElasticInserter(host=options.host)
  fetcher = GithubFetcher(project_path=options.project_path)
  commits = fetcher.GetCommits()
  for commit in commits:
    commit_document = fetcher.BuildCommitDocument(commit)
    inserter.AddCommit(commit_document)
