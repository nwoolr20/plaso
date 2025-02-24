# -*- coding: utf-8 -*-
"""Storage writer for Redis."""

from plaso.storage import writer
from plaso.storage.redis import redis_store


class RedisStorageWriter(writer.StorageWriter):
  """Redis-based storage writer."""

  # pylint: disable=redundant-returns-doc,useless-return
  def GetFirstWrittenEventSource(self):
    """Retrieves the first event source that was written after open.

    Using GetFirstWrittenEventSource and GetNextWrittenEventSource newly
    added event sources can be retrieved in order of addition.

    Returns:
      EventSource: None as there are no newly written event sources.

    Raises:
      IOError: if the storage writer is closed.
      OSError: if the storage writer is closed.
    """
    if not self._store:
      raise IOError('Unable to read from closed storage writer.')

    return None

  # pylint: disable=redundant-returns-doc,useless-return
  def GetNextWrittenEventSource(self):
    """Retrieves the next event source that was written after open.

    Returns:
      EventSource: None as there are no newly written event sources.

    Raises:
      IOError: if the storage writer is closed.
      OSError: if the storage writer is closed.
    """
    if not self._store:
      raise IOError('Unable to read from closed storage writer.')

    return None

  # pylint: disable=arguments-differ
  def Open(
      self, redis_client=None, session_identifier=None, task_identifier=None,
      **unused_kwargs):
    """Opens the storage writer.

    Args:
      redis_client (Optional[Redis]): Redis client to query. If specified, no
          new client will be created. If no client is specified a new client
          will be opened connected to the Redis instance specified by 'url'.
      session_identifier (Optional[str]): session identifier.
      task_identifier (Optional[str]): task identifier.

    Raises:
      IOError: if the storage writer is already opened.
      OSError: if the storage writer is already opened.
    """
    if self._store:
      raise IOError('Storage writer already opened.')

    self._store = redis_store.RedisStore(storage_type=self._storage_type)

    if self._serializers_profiler:
      self._store.SetSerializersProfiler(self._serializers_profiler)

    if self._storage_profiler:
      self._store.SetStorageProfiler(self._storage_profiler)

    self._store.Open(
        redis_client=redis_client, session_identifier=session_identifier,
        task_identifier=task_identifier)

  def WritePreprocessingInformation(self, knowledge_base):
    """Writes preprocessing information.

    Args:
      knowledge_base (KnowledgeBase): contains the preprocessing information.

    Raises:
      IOError: always as the Redis store does not support preprocessing
          information.
      OSError: always as the Redis store does not support preprocessing
          information.
    """
    raise IOError(
        'Preprocessing information is not supported by the redis store.')

  def WriteSessionCompletion(self, session):
    """Writes session completion information.

    Args:
      session (Session): session the storage changes are part of.

    Raises:
      IOError: always, as the Redis store does not support writing a session
          completion.
      OSError: always, as the Redis store does not support writing a session
          completion.
    """
    raise IOError('Session completion is not supported by the redis store.')

  def WriteSessionConfiguration(self, session):
    """Writes session configuration information.

    Args:
      session (Session): session the storage changes are part of.

    Raises:
      IOError: always, as the Redis store does not support writing a session
          configuration.
      OSError: always, as the Redis store does not support writing a session
          configuration.
    """
    raise IOError('Session configuration is not supported by the redis store.')

  def WriteSessionStart(self, session):
    """Writes session start information.

    Args:
      session (Session): session the storage changes are part of.

    Raises:
      IOError: always, as the Redis store does not support writing a session
          start.
      OSError: always, as the Redis store does not support writing a session
          start.
    """
    raise IOError('Session start is not supported by the redis store.')
