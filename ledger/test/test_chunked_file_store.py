import os
import random
import pytest

from ledger.stores.chunked_file_store import ChunkedFileStore
from ledger.stores.text_file_store import TextFileStore


def countLines(fname) -> int:
    with open(fname) as f:
        return sum(1 for _ in f)


def getValue(key) -> str:
    return str(key) + " Some data"


chunkSize = 2
dataSize = 100


@pytest.fixture(scope="module")
def chunkedTextFileStore() -> ChunkedFileStore:
    return ChunkedFileStore("/tmp", "chunked_data", True, True, chunkSize,
                            chunkStoreConstructor=TextFileStore)


@pytest.yield_fixture(scope="module")
def populatedChunkedFileStore(chunkedTextFileStore) -> ChunkedFileStore:
    store = chunkedTextFileStore
    store.reset()
    dirPath = "/tmp/chunked_data"
    for i in range(1, dataSize + 1):
        store.put(getValue(i), str(i))
    assert len(os.listdir(dirPath)) == dataSize / chunkSize
    assert all(countLines(dirPath + os.path.sep + f) == chunkSize
               for f in os.listdir(dirPath))
    yield store
    store.close()


def testWriteToNewFileOnceChunkSizeIsReached(populatedChunkedFileStore):
    pass


def testRandomRetrievalFromChunkedFiles(populatedChunkedFileStore):
    key = random.randrange(1, dataSize + 1)
    value = getValue(key)
    assert populatedChunkedFileStore.get(key) == value


def testIterateOverChunkedFileStore(populatedChunkedFileStore):
    store = populatedChunkedFileStore
    iterator = store.iterator()
    assert sum(1 for _ in iterator) == dataSize
