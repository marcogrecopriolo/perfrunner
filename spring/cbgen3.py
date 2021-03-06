from datetime import timedelta
from urllib import parse

from couchbase.cluster import (
    Cluster,
    ClusterOptions,
    ClusterTimeoutOptions,
    QueryOptions,
)
from couchbase.management.collections import CollectionSpec
from couchbase.management.users import User
from txcouchbase.cluster import TxCluster

from couchbase_core.cluster import PasswordAuthenticator
from logger import logger
from spring.cbgen_helpers import backoff, quiet, timeit


class CBAsyncGen3:

    TIMEOUT = 60  # seconds

    def __init__(self, **kwargs):
        connection_string = 'couchbase://{host}?password={password}'
        connection_string = connection_string.format(host=kwargs['host'],
                                                     password=kwargs['password'])

        pass_auth = PasswordAuthenticator(kwargs['username'], kwargs['password'])
        timeout = ClusterTimeoutOptions(kv_timeout=timedelta(seconds=self.TIMEOUT))
        options = ClusterOptions(authenticator=pass_auth, timeout_options=timeout)
        self.cluster = TxCluster(connection_string=connection_string, options=options)
        self.bucket_name = kwargs['bucket']
        self.collections = dict()
        self.collection = None
        logger.info("Connection string: {}".format(connection_string))

    def connect_collections(self, scope_collection_list):
        self.bucket = self.cluster.bucket(self.bucket_name)
        for scope_collection in scope_collection_list:
            scope, collection = scope_collection.split(":")
            if scope == "_default" and collection == "_default":
                self.collections[scope_collection] = self.bucket.default_collection()
            else:
                self.collections[scope_collection] = self.bucket.scope(scope).collection(collection)

    def create(self, *args, **kwargs):
        self.collection = self.collections[args[0]]
        return self.do_create(*args[1:], **kwargs)

    def do_create(self, key: str, doc: dict, persist_to: int = 0,
                  replicate_to: int = 0, ttl: int = 0):
        return self.collection.upsert(key, doc,
                                      persist_to=persist_to,
                                      replicate_to=replicate_to,
                                      ttl=ttl)

    def create_durable(self, *args, **kwargs):
        self.collection = self.collections[args[0]]
        return self.do_create_durable(*args[1:], **kwargs)

    def do_create_durable(self, key: str, doc: dict, durability: int = None, ttl: int = 0):
        return self.collection.upsert(key, doc,
                                      durability_level=durability,
                                      ttl=ttl)

    def read(self, *args, **kwargs):
        self.collection = self.collections[args[0]]
        return self.do_read(*args[1:], **kwargs)

    def do_read(self, key: str):
        return self.collection.get(key)

    def update(self, *args, **kwargs):
        self.collection = self.collections[args[0]]
        return self.do_update(*args[1:], **kwargs)

    def do_update(self, key: str, doc: dict, persist_to: int = 0,
                  replicate_to: int = 0, ttl: int = 0):
        return self.collection.upsert(key,
                                      doc,
                                      persist_to=persist_to,
                                      replicate_to=replicate_to,
                                      ttl=ttl)

    def update_durable(self, *args, **kwargs):
        self.collection = self.collections[args[0]]
        return self.do_update_durable(*args[1:], **kwargs)

    def do_update_durable(self, key: str, doc: dict, durability: int = None, ttl: int = 0):
        return self.collection.upsert(key, doc,
                                      durability_level=durability,
                                      ttl=ttl)

    def delete(self, *args, **kwargs):
        self.collection = self.collections[args[0]]
        return self.do_delete(*args[1:], **kwargs)

    def do_delete(self, key: str):
        return self.collection.remove(key)


class CBGen3(CBAsyncGen3):

    TIMEOUT = 10  # seconds

    def __init__(self, ssl_mode: str = 'none', n1ql_timeout: int = None, **kwargs):
        connection_string = 'couchbase://{host}?password={password}&{params}'
        connstr_params = parse.urlencode(kwargs["connstr_params"])

        if ssl_mode == 'data':
            connection_string = connection_string.replace('couchbase',
                                                          'couchbases')
            connection_string += '&certpath=root.pem'

        connection_string = connection_string.format(host=kwargs['host'],
                                                     password=kwargs['password'],
                                                     params=connstr_params)

        pass_auth = PasswordAuthenticator(kwargs['username'], kwargs['password'])
        if n1ql_timeout:
            timeout = ClusterTimeoutOptions(kv_timeout=timedelta(seconds=self.TIMEOUT),
                                            query_timeout=timedelta(seconds=n1ql_timeout))
        else:
            timeout = ClusterTimeoutOptions(kv_timeout=timedelta(seconds=self.TIMEOUT))
        options = ClusterOptions(authenticator=pass_auth, timeout_options=timeout)
        self.cluster = Cluster(connection_string=connection_string, options=options)
        self.bucket_name = kwargs['bucket']
        self.bucket = None
        self.collections = dict()
        self.collection = None
        if n1ql_timeout:
            self.bucket.n1ql_timeout = n1ql_timeout
        logger.info("Connection string: {}".format(connection_string))

    def create(self, *args, **kwargs):
        self.collection = self.collections[args[0]]
        return self.do_create(*args[1:], **kwargs)

    @quiet
    @backoff
    def do_create(self, *args, **kwargs):
        super().do_create(*args, **kwargs)

    def create_durable(self, *args, **kwargs):
        self.collection = self.collections[args[0]]
        return self.do_create_durable(*args[1:], **kwargs)

    @quiet
    @backoff
    def do_create_durable(self, *args, **kwargs):
        super().do_create_durable(*args, **kwargs)

    def read(self, *args, **kwargs):
        self.collection = self.collections[args[0]]
        return self.do_read(*args[1:], **kwargs)

    @quiet
    @backoff
    @timeit
    def do_read(self, *args, **kwargs):
        super().do_read(*args, **kwargs)

    def update(self, *args, **kwargs):
        self.collection = self.collections[args[0]]
        return self.do_update(*args[1:], **kwargs)

    @quiet
    @backoff
    @timeit
    def do_update(self, *args, **kwargs):
        super().do_update(*args, **kwargs)

    def update_durable(self, *args, **kwargs):
        self.collection = self.collections[args[0]]
        return self.do_update_durable(*args[1:], **kwargs)

    @quiet
    @backoff
    @timeit
    def do_update_durable(self, *args, **kwargs):
        super().do_update_durable(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.collection = self.collections[args[0]]
        return self.do_delete(*args[1:], **kwargs)

    @quiet
    def do_delete(self, *args, **kwargs):
        super().do_delete(*args, **kwargs)

    @quiet
    @timeit
    def n1ql_query(self, n1ql_query: str, options: QueryOptions):
        tuple(self.cluster.query(n1ql_query, options))

    def create_user_manager(self):
        self.user_manager = self.cluster.users()

    def create_collection_manager(self):
        if not self.bucket:
            self.bucket = self.cluster.bucket(self.bucket_name)
        self.collection_manager = self.bucket.collections()

    @quiet
    @backoff
    def do_upsert_user(self, *args, **kwargs):
        return self.user_manager.upsert_user(User(username=args[0],
                                                  roles=args[1],
                                                  password=args[2]))

    def get_roles(self):
        return self.user_manager.get_roles()

    def do_collection_create(self, *args, **kwargs):
        self.collection_manager.create_collection(
            CollectionSpec(scope_name=args[0],
                           collection_name=args[1]))

    def do_collection_drop(self, *args, **kwargs):
        self.collection_manager.drop_collection(
            CollectionSpec(scope_name=args[0],
                           collection_name=args[1]))
