# -*- coding: utf-8 -*-
import os
import random
import string
import time

from ydb.tests.library.common import yatest_common
from ydb.tests.library.harness.kikimr_cluster import KiKiMR
from ydb.tests.library.harness.kikimr_config import KikimrConfigGenerator
from ydb.tests.library.harness.param_constants import kikimr_driver_path
from ydb.tests.library.common.types import Erasure
from ydb.tests.oss.ydb_sdk_import import ydb


class TestCompatibility(object):
    @classmethod
    def setup_class(cls):
        # binary_paths = [kikimr_driver_path()]
        binary_paths = ["/home/maxim-yurchuk/ydbs/ydbd243", "/home/maxim-yurchuk/ydbs/ydbd242"]
        cls.cluster = KiKiMR(KikimrConfigGenerator(erasure=Erasure.MIRROR_3_DC, binary_paths=binary_paths))
        cls.cluster.start()
        cls.endpoint = "%s:%s" % (
            cls.cluster.nodes[2].host, cls.cluster.nodes[2].port
        )
        cls.driver = ydb.Driver(
            ydb.DriverConfig(
                database='/Root',
                endpoint=cls.endpoint
            )
        )
        cls.driver.wait()

    @classmethod
    def teardown_class(cls):
        if hasattr(cls, 'driver'):
            cls.driver.stop()

        if hasattr(cls, 'cluster'):
            cls.cluster.stop(kill=True)  # TODO fix

    def test(self):
        session = ydb.retry_operation_sync(lambda: self.driver.table_client.session().create())
        table_name = "foo"
        
        with ydb.SessionPool(self.driver, size=1) as pool:
            with pool.checkout() as session:
                session.execute_scheme(
                    "create table `sample_table` (id Int32, group Int32, value Int32, PRIMARY KEY(id)) WITH (AUTO_PARTITIONING_BY_SIZE = ENABLED, AUTO_PARTITIONING_PARTITION_SIZE_MB = 1);"
                )
                id_ = 0
                iterations = 20

                for i in range(iterations):
                    print(i)
                    try:
                        query = """ $n=500; 
                        $q={}; 
                        UPSERT INTO sample_table  (
                        SELECT (a.value * $n + b.group + $q) as id, a.value AS value, b.group AS group
                        FROM 
                        (SELECT value FROM as_table(AsList(AsStruct(ListFromRange(0, $n) AS value))) FLATTEN BY value) as a 
                        CROSS JOIN 
                        (SELECT group FROM as_table(AsList(AsStruct(ListFromRange(0, $n) AS group)))  FLATTEN BY group) as b
                        )
                        """.format(id_)
                        id_ += 500 * 500
                        result_sets = session.transaction().execute(
                            query, commit_tx=True
                        )
                    except Exception:
                        pass
                """
                n = 20 
                total = n * n
                pk = 2 ** 64 // total // 2
                diff = pk
                for i in range(n):
                    for j in range(n):
                        random_string = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20000))
                        pk = random.randint(0, 2 ** 64)
                        session.transaction().execute(
                            'insert into sample_table (id, group, value, payload) values ({}, {}, {}, "{}");'.format(pk, i, j, random_string), commit_tx=True)
                        # pk += diff
                """
                for i in range(50):
                    time.sleep(10)
                    result_sets = session.transaction().execute(
                        "SELECT group, SUM(value) as sum_value from sample_table WHERE 1<2 GROUP BY group ORDER BY group", commit_tx=True
                    )
                    for row in result_sets[0].rows:
                        print(" ".join([str(x) for x in list(row.values())]))
                    
                    print("~/ydb/ydb/apps/ydb/ydb -e grpc://{} -d /Root ".format(self.endpoint))

        # time.sleep(10000)
        
        return
        session.execute_scheme(
            "CREATE TABLE %s",format(
                table_name
            )
        )
        return
        time.sleep(1000)
        yatest_common.execute(
            [
                yatest_common.binary_path(os.getenv("YDB_CLI_BINARY")),
                "--verbose",
                "--endpoint", "grpc://localhost:%d" % self.cluster.nodes[1].grpc_port,
                "--database=/Root",

                "workload", "kv", "init",

                "--min-partitions", "1",
                "--partition-size", "10",
                "--auto-partition", "0",
                "--init-upserts", "0",
                "--cols", "5",
                "--int-cols", "2",
                "--key-cols", "3"
            ],
            wait=True
        )

        yatest_common.execute(
            [
                yatest_common.binary_path(os.getenv("YDB_CLI_BINARY")),
                "--verbose",
                "--endpoint", "grpc://localhost:%d" % self.cluster.nodes[1].grpc_port,
                "--database=/Root",

                "workload", "kv", "run", "mixed",
                "--seconds", "100",
                "--threads", "10",

                "--cols", "5",
                "--len", "200",
                "--int-cols", "2",
                "--key-cols", "3"
            ],
            wait=True
        )
