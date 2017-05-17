import os
import random

import math
from time import perf_counter

import pytest

from ledger.stores.chunked_file_store import ChunkedFileStore
from ledger.stores.text_file_store import TextFileStore


def countLines(fname) -> int:
    with open(fname) as f:
        return sum(1 for _ in f)


def getValue(key) -> str:
    return str(key) + " Some data"


chunkSize = 3
dataSize = 101
data = [getValue(i) for i in range(1, dataSize+1)]


@pytest.fixture(scope="module")
def chunkedTextFileStore() -> ChunkedFileStore:
    return ChunkedFileStore("/tmp", "chunked_data", True, True, chunkSize,
                            chunkStoreConstructor=TextFileStore)


@pytest.yield_fixture(scope="module")
def populatedChunkedFileStore(chunkedTextFileStore) -> ChunkedFileStore:
    store = chunkedTextFileStore
    store.reset()
    dirPath = "/tmp/chunked_data"
    for d in data:
        store.put(d)
    assert len(os.listdir(dirPath)) == math.ceil(dataSize / chunkSize)
    assert all(countLines(dirPath + os.path.sep + f) <= chunkSize
               for f in os.listdir(dirPath))
    yield store
    store.close()


def testWriteToNewFileOnceChunkSizeIsReached(populatedChunkedFileStore):
    pass


def testRandomRetrievalFromChunkedFiles(populatedChunkedFileStore):
    keys = [2*chunkSize,
            3*chunkSize+1,
            3*chunkSize+chunkSize,
            random.randrange(1, dataSize + 1)]
    for key in keys:
        value = getValue(key)
        assert populatedChunkedFileStore.get(key) == value


def testSizeChunkedFileStore(populatedChunkedFileStore):
    s = perf_counter()
    c1 = sum(1 for l in populatedChunkedFileStore.iterator())
    e = perf_counter()
    t1 = e - s
    s = perf_counter()
    c2 = populatedChunkedFileStore.numKeys
    e = perf_counter()
    t2 = e - s
    # It should be faster to use ChunkedStore specific implementation
    # of `numKeys`
    assert t1 > t2
    assert c1 == c2
    assert c2 == dataSize


def testIterateOverChunkedFileStore(populatedChunkedFileStore):
    store = populatedChunkedFileStore
    for k, v in store.iterator():
        assert data[int(k)-1] == v


def test_get_range(populatedChunkedFileStore):
    # Test for range spanning multiple chunks

    # Range begins and ends at chunk boundaries
    num = 0
    for k, v in populatedChunkedFileStore.get_range(chunkSize+1, 2*chunkSize):
        assert data[int(k) - 1] == v
        num += 1
    assert num == chunkSize

    # Range does not begin or end at chunk boundaries
    num = 0
    for k, v in populatedChunkedFileStore.get_range(chunkSize+2, 2*chunkSize+1):
        assert data[int(k) - 1] == v
        num += 1
    assert num == chunkSize

    # Range spans multiple full chunks
    num = 0
    for k, v in populatedChunkedFileStore.get_range(chunkSize + 2,
                                                    5 * chunkSize + 1):
        assert data[int(k) - 1] == v
        num += 1
    assert num == 4*chunkSize
