#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import datetime
import json
import elasticsearch
import argparse
import requests
from launchpadlib import launchpad


class ElasticGithubInserter(object):

  def __init__(self, host='localhost', port=9200, index='commits'):
    super(ElasticGithubInserter, self).__init__()
    self._client = elasticsearch.Elasticsearch([{'host': host, 'port': port}])
    self._index_name = index
    self._doc_type = 'commit'
    self._CreateIndex()
    self._UpdateMapping()

  def AddCommit(self, commit):
    """Adds a commit to the index."""
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


class ElasticLaunchpadInserter(object):

  def __init__(self, host='localhost', port=9200, index='publishes'):
    super(ElasticLaunchpadInserter, self).__init__()
    self._client = elasticsearch.Elasticsearch([{'host': host, 'port': port}])
    self._index_name = index
    self._doc_type = 'binary_publish'
    self._CreateIndex()
    self._UpdateMapping()

  def AddPublish(self, publish):
    """Adds a publish to the index."""
    identifier = publish['display_name']
    try:
      resource = self._client.index(
          index=self._index_name, doc_type=self._doc_type, body=publish,
          id=identifier)
    except elasticsearch.exceptions.RequestError as exception:
      print(exception)
      return

    print(resource)

  def GetLatestPublish(self, distribution, architecture):
    try:
      results = self._client.search(
          index=self._index_name,
          q='distribution:"{0:s}" AND architecture:"{1:s}"'.format(distribution,
              architecture),
          sort='@timestamp:desc', size=1)
    except elasticsearch.exceptions.RequestError:
      return 0

    # The elasticsearch result isn't very strongly structured...
    try:
      test_number = results['hits']['hits'][0]['_source']['@timestamp']
      return test_number
    except (KeyError, IndexError):
      return 0

  def _CreateIndex(self):
    if not self._client.indices.exists(self._index_name):
      self._client.indices.create(self._index_name)

  def _UpdateMapping(self):
    self._client.indices.put_mapping(
        index=self._index_name,
        doc_type=self._doc_type,
        body={
          "properties": {
            "distribution": {
              "type": "keyword",
              "doc_values": True
            },
            "architecture": {
              "type": "keyword",
              "doc_values": True
            }
          }
        })

class GithubFetcher(object):
  """Fetches commits from github for insertion into Elasticsearch."""

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


class GIFTFetcher(object):

  def GetPackageChanges(self, distribution='xenial', architecture='amd64',
      changes_since=None):
    launchpad_client = launchpad.Launchpad.login_anonymously('giftstats',
        'production', '/tmp/giftstats')
    owner = launchpad_client.people['gift']
    ppa = owner.getPPAByName(name='dev')
    #last_month = datetime.datetime(2019, 3, 1)
    desired_dist_and_arch = (
        'https://api.launchpad.net/devel/ubuntu/{0:s}/{1:s}'.format(
            distribution, architecture))
    binaries = ppa.getPublishedBinaries(created_since_date=changes_since,
        status='Published', distro_arch_series=desired_dist_and_arch)
    for binary in binaries:
      yield binary

  def BuildBinaryPublishDocument(self, package_publish, distribution,
      architecture):
    document = {
      '@timestamp': package_publish.date_published,
      'display_name': package_publish.display_name,
      'package_name': package_publish.binary_package_name,
      'version': package_publish.binary_package_version,
      'distribution': distribution,
      'architecture': architecture
    }
    return document


if __name__ == '__main__':
  argument_parser = argparse.ArgumentParser()

  argument_parser.add_argument('--host', type=str, default='localhost',
      help='hostname or IP address of the elasticsearch server.')

  argument_parser.add_argument('--project_path', type=str,
      default='log2timeline/plaso',
      help='Github path of project (eg. log2timeline/plaso).')

  options = argument_parser.parse_args()

  inserter = ElasticGithubInserter(host=options.host)
  fetcher = GithubFetcher(project_path=options.project_path)
  commits = fetcher.GetCommits()
  for commit in commits:
    commit_document = fetcher.BuildCommitDocument(commit)
    inserter.AddCommit(commit_document)

  inserter = ElasticLaunchpadInserter(host=options.host)
  fetcher = GIFTFetcher()
  distribution = 'xenial'
  architecture = 'amd64'
  changes_since = inserter.GetLatestPublish(distribution, architecture)
  for binary_publish_record in fetcher.GetPackageChanges(
      distribution=distribution, architecture=architecture, changes_since=changes_since):
    document = fetcher.BuildBinaryPublishDocument(
        binary_publish_record, distribution=distribution,
        architecture=architecture)
    inserter.AddPublish(document)
