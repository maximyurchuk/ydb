# -*- coding: utf-8 -*-
import os
import random
import string
import time
import traceback

import pytest 
# asdasdas
from unittest.mock import Mock
pytest.config = Mock()
pytest.config.current_test_name = "test_name"
ya = Mock()
pytest.config.ya = ya
ya.get_param = lambda key, default: default
ya.get_context = lambda key: None

from ydb.tests.library.harness.kikimr_cluster import KiKiMR
from ydb.tests.library.harness.kikimr_config import KikimrConfigGenerator
from ydb.tests.library.common.types import Erasure
from ydb.tests.oss.ydb_sdk_import import ydb


def main():
    # binary_paths = [kikimr_driver_path()]
    binary_paths = [
        # "/home/maxim-yurchuk/ydbs/ydbd243",
        "/home/maxim-yurchuk/ydb243/ydb/apps/ydbd/ydbd",
        # "/home/maxim-yurchuk/ydb/ydb/apps/ydbd/ydbd",
        "/home/maxim-yurchuk/ydbs/ydbd242",
        ]
    cluster = KiKiMR(KikimrConfigGenerator(erasure=Erasure.MIRROR_3_DC, binary_paths=binary_paths, output_path="/tmp/"))
    cluster.start()
    endpoint = "%s:%s" % (
        cluster.nodes[2].host, cluster.nodes[2].port
    )
    driver = ydb.Driver(
        ydb.DriverConfig(
            database='/Root',
            endpoint=endpoint
        )
    )
    print("~/ydb/ydb/apps/ydb/ydb -e grpc://{} -d /Root ".format(endpoint))

    iterations = 20
    id_ = 0

    with ydb.SessionPool(driver, size=1) as pool:
        with pool.checkout() as session:
            session.execute_scheme(
                "create table `sample_table` (id Int32, group Int32, value Int32, PRIMARY KEY(id)) WITH (AUTO_PARTITIONING_BY_SIZE = ENABLED, AUTO_PARTITIONING_PARTITION_SIZE_MB = 1);"
            )
            www = session.explain("select 1")
            print(www.query_plan)
            print(www.query_ast)
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
                    result_sets = session.transaction().execute(
                        query, commit_tx=True
                    )
                    id_ += 500 * 500
                except Exception as e:
                    # print(e)
                    traceback.print_exc()
            
            # ~/ydb/ydb/apps/ydb/ydb -e  grpc://localhost:4974 -d /Root sql -s "SELECT  group, SUM(value) as sum_value from sample_table GROUP BY group ORDER BY group LIMIT 10" --stats full --format json-base64
            for i in range(50):
                time.sleep(10)
                q = "SELECT RandomUuid(group), group, SUM(value) as sum_value from sample_table WHERE 1<2 GROUP BY group ORDER BY group"
                result_sets = session.transaction().execute(
                    q, commit_tx=True
                )
                for row in result_sets[0].rows:
                    print(" ".join([str(x) for x in list(row.values())]))
                
                www = session.explain(q)
                print(www.query_plan)
                print(www.query_ast)

                print("~/ydb/ydb/apps/ydb/ydb -e grpc://{} -d /Root ".format(endpoint))
    time.sleep(100000)
    driver.wait()