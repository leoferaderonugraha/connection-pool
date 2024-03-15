from .connection_pool import ConnectionPool  # type: ignore
from greenstalk import Client  # type: ignore
from concurrent.futures import ThreadPoolExecutor, as_completed


def test_connection(pool: ConnectionPool) -> None:
    print(pool.size())
    conn = pool.acquire()
    conn.stats()
    pool.release(conn)


if __name__ == '__main__':
    pool = ConnectionPool(10,
                          Client,
                          lambda x: len(x.stats()) > 0,
                          lambda x: x(('localhost', 11300)),
                          Client)

    with ThreadPoolExecutor(max_workers=10) as executor:
        awaitables = []

        for _ in range(100):
            awaitables.append(executor.submit(test_connection, pool))

        for awaitable in as_completed(awaitables):
            awaitable.result()

    print('final pool size:', pool.size())
