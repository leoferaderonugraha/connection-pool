import typing as t
import queue
import threading


T = t.TypeVar('T')


class ConnectionPool:
    def __init__(self,
                 size: int,
                 class_name: t.Type[T], 
                 ping_fn: t.Callable[[T], bool],
                 creation_fn: t.Callable[[t.Any], T],
                 *creation_args: t.List[t.Any]) -> None:
        self.__queue_size = size
        self.__queue: queue.Queue[T] = queue.Queue(maxsize=self.__queue_size)
        self.__class_name = class_name
        self.__ping_fn = ping_fn
        self.__creation_fn = creation_fn
        self.__args = creation_args
        self.__lock = threading.Lock()

        # populate connections on creation
        self.__populate()

    def size(self) -> int:
        return self.__queue.qsize()

    def acquire(self) -> t.Optional[T]:
        """Returns an alive connection or none"""
        conn = None

        with self.__lock:
            conn = self.__queue.get(block=False)

        if conn is not None:
            if not self.__ping_fn(conn):
                return None

        return conn

    def release(self, conn: T) -> None:
        """Put back the connection if it's still alive"""
        if not isinstance(conn, self.__class_name):
            raise TypeError

        if not self.__ping_fn(conn):
            return None

        with self.__lock:
            try:
                self.__queue.put_nowait(conn)
            except queue.Full:
                pass

    def __populate(self) -> None:
        size = self.__queue_size - self.size()

        for _ in range(size):
            conn = self.__creation_fn(*self.__args)
            if self.__ping_fn(conn):
                with self.__lock:
                    try:
                        self.__queue.put_nowait(conn)
                    except queue.Full:
                        pass
