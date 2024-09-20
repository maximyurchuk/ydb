PY3_PROGRAM()
ENV(YDB_DRIVER_BINARY="ydb/apps/ydbd/ydbd")
ENV(YDB_CLI_BINARY="ydb/apps/ydb/ydb")
ENV(YDB_ERASURE=mirror_3_dc)
ENV(YDB_USE_IN_MEMORY_PDISKS=true)

PY_MAIN(ydb.tests.functional.compatibility_cluster.main)

PY_SRCS(
    main.py
)

DEPENDS(
    ydb/apps/ydbd
    ydb/apps/ydb
)

PEERDIR(
    ydb/tests/library
)


END()
