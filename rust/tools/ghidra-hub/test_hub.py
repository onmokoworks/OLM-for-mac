import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor

from decompiler_pool import DecompilerPool
from matching import match_functions
from runtime import RWLock
from hub import owned_process


def row(address, raw='a', normalized='n', instructions=8, rva=0):
    return dict(address=address, raw_hash=raw, normalized_hash=normalized,
                instructions=instructions, rva=rva)


class MatchingTests(unittest.TestCase):
    def test_same_hash_uses_rva_and_can_match_tiny_functions(self):
        result = match_functions([row('old', instructions=1, rva=42)],
                                 [row('new', raw='b', instructions=1, rva=42)], True)
        self.assertEqual(result['matches']['old']['target'], 'new')

    def test_unique_raw_match(self):
        result = match_functions([row('old')], [row('new')])
        self.assertEqual(result['matches']['old']['method'], 'raw_hash')

    def test_duplicate_fingerprints_are_not_guessed(self):
        self.assertEqual(match_functions([row('a'), row('b')], [row('c')])['matches'], {})

    def test_tiny_functions_not_guessed_across_hashes(self):
        self.assertEqual(match_functions([row('a', instructions=2)], [row('b')])['matches'], {})

    def test_relocated_normalized_match(self):
        result = match_functions([row('a', raw='old')], [row('b', raw='new')])
        self.assertEqual(result['matches']['a']['method'], 'normalized_hash')

    def test_no_name_or_address_fallback(self):
        result = match_functions([row('same', raw='a', normalized='x')],
                                 [row('same', raw='b', normalized='y')])
        self.assertEqual(result['unmatched'], ['same'])


class LockTests(unittest.TestCase):
    def test_readers_overlap_writer_is_exclusive(self):
        lock = RWLock()
        barrier = threading.Barrier(3)
        entered = threading.Event()
        release = threading.Event()
        def reader():
            with lock.read():
                barrier.wait(timeout=3)
                release.wait(timeout=3)
        def writer():
            with lock.write():
                entered.set()
        with ThreadPoolExecutor(3) as executor:
            futures = [executor.submit(reader) for _ in range(2)]
            barrier.wait(timeout=3)
            future = executor.submit(writer)
            self.assertFalse(entered.wait(.05))
            release.set()
            for f in futures+[future]:
                f.result(timeout=3)
        self.assertTrue(entered.is_set())

    def test_exception_releases_writer(self):
        lock = RWLock()
        with self.assertRaises(ValueError), lock.write():
            raise ValueError('abort')
        with lock.read():
            self.assertEqual(lock.readers, 1)


class PoolTests(unittest.TestCase):
    def test_bounded_reuse_and_dispose(self):
        created = []
        class Fake:
            disposed = False
            def dispose(self):
                self.disposed = True
        def factory():
            d = Fake(); created.append(d); return d
        pool = DecompilerPool(factory, size=2)
        def work(_):
            with pool.acquire() as dec:
                self.assertFalse(dec.disposed)
                time.sleep(.01)
        with ThreadPoolExecutor(6) as executor:
            list(executor.map(work, range(12)))
        self.assertEqual(len(created), 2)
        pool.dispose()
        self.assertTrue(all(d.disposed for d in created))
        with self.assertRaises(RuntimeError), pool.acquire():
            pass

    def test_lifecycle_refuses_unowned_process(self):
        import os
        import psutil
        self.assertIsNone(owned_process(dict(pid=os.getpid(), created=psutil.Process().create_time(), token='wrong')))
        self.assertIsNone(owned_process(dict(pid=os.getpid(), created=0, token='wrong')))


if __name__ == '__main__':
    unittest.main()
