PY3TEST()

PEERDIR(
    contrib/python/thrift
    contrib/python/tornado
)

DATA(
    arcadia/contrib/python/thrift/py3/tests/keys
)

TEST_SRCS(
    test_socket.py
    test_sslsocket.py
    thrift_json.py
)

NO_LINT()

END()
