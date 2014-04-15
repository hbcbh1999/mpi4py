from mpi4py import MPI
import mpiunittest as unittest
from arrayimpl import allclose

typemap = MPI._typedict

try:
    import array
    HAVE_ARRAY = True
except ImportError:
    HAVE_ARRAY = False
try:
    import numpy
    HAVE_NUMPY = True
except ImportError:
    HAVE_NUMPY = False

def Sendrecv(smsg, rmsg):
    comm = MPI.COMM_SELF
    sts = MPI.Status()
    comm.Sendrecv(sendbuf=smsg, recvbuf=rmsg, status=sts)

class TestMessageP2P(unittest.TestCase):

    TYPECODES = "hil"+"HIL"+"fd"

    def _test1(self, equal, zero, s, r, t):
        r[:] = zero
        Sendrecv(s, r)
        self.assertTrue(equal(s, r))

    def _test21(self, equal, zero, s, r, typecode):
        datatype = typemap[typecode]
        for type in (None, typecode, datatype):
            r[:] = zero
            Sendrecv([s, type],
                     [r, type])
            self.assertTrue(equal(s, r))

    def _test22(self, equal, zero, s, r, typecode):
        size = len(r)
        for count in range(size):
            r[:] = zero
            Sendrecv([s, count],
                     [r, count])
            for i in range(count):
                self.assertTrue(equal(r[i], s[i]))
            for i in range(count, size):
                self.assertTrue(equal(r[i], zero[0]))
        for count in range(size):
            r[:] = zero
            Sendrecv([s, (count, None)],
                     [r, (count, None)])
            for i in range(count):
                self.assertTrue(equal(r[i], s[i]))
            for i in range(count, size):
                self.assertTrue(equal(r[i], zero[0]))
        for disp in range(size):
            r[:] = zero
            Sendrecv([s, (None, disp)],
                     [r, (None, disp)])
            for i in range(disp):
                self.assertTrue(equal(r[i], zero[0]))
            for i in range(disp, size):
                self.assertTrue(equal(r[i], s[i]))
        for disp in range(size):
            for count in range(size-disp):
                r[:] = zero
                Sendrecv([s, (count, disp)],
                         [r, (count, disp)])
                for i in range(0, disp):
                    self.assertTrue(equal(r[i], zero[0]))
                for i in range(disp, disp+count):
                    self.assertTrue(equal(r[i], s[i]))
                for i in range(disp+count, size):
                    self.assertTrue(equal(r[i], zero[0]))

    def _test31(self, equal, z, s, r, typecode):
        datatype = typemap[typecode]
        for type in (None, typecode, datatype):
            for count in (None, len(s)):
                r[:] = z
                Sendrecv([s, count, type],
                         [r, count, type])
                self.assertTrue(equal(s, r))

    def _test32(self, equal, z, s, r, typecode):
        datatype = typemap[typecode]
        for type in (None, typecode, datatype):
            for p in range(0, len(s)):
                r[:] = z
                Sendrecv([s, (p, None), type],
                         [r, (p, None), type])
                self.assertTrue(equal(s[:p], r[:p]))
                for q in range(p, len(s)):
                    count, displ = q-p, p
                    r[:] = z
                    Sendrecv([s, (count, displ), type],
                             [r, (count, displ), type])
                    self.assertTrue(equal(s[p:q], r[p:q]))
                    self.assertTrue(equal(z[:p], r[:p]))
                    self.assertTrue(equal(z[q:], r[q:]))

    def _test4(self, equal, z, s, r, typecode):
        datatype = typemap[typecode]
        for type in (None, typecode, datatype):
            for p in range(0, len(s)):
                r[:] = z
                Sendrecv([s, p, None, type],
                         [r, p, None, type])
                self.assertTrue(equal(s[:p], r[:p]))
                for q in range(p, len(s)):
                    count, displ = q-p, p
                    r[:] = z
                    Sendrecv([s, count, displ, type],
                             [r, count, displ, type])
                    self.assertTrue(equal(s[p:q], r[p:q]))
                    self.assertTrue(equal(z[:p], r[:p]))
                    self.assertTrue(equal(z[q:], r[q:]))

    def testBadMessage(self):
        buf = MPI.Alloc_mem(4)
        empty = [None, 0, "B"]
        def f(): Sendrecv([buf, 0, 0, "i", None], empty)
        self.assertRaises(ValueError, f)
        def f(): Sendrecv([buf,  0, "\0"], empty)
        self.assertRaises(KeyError, f)
        def f(): Sendrecv([buf, -1, "i"], empty)
        self.assertRaises(ValueError, f)
        def f(): Sendrecv([buf, 0, -1, "i"], empty)
        self.assertRaises(ValueError, f)
        def f(): Sendrecv([buf, 0, +2, "i"], empty)
        self.assertRaises(ValueError, f)
        def f(): Sendrecv([None, 1,  0, "i"], empty)
        self.assertRaises(ValueError, f)
        MPI.Free_mem(buf)

    if HAVE_ARRAY:
        def _testArray(self, test):
            from array import array
            from operator import eq as equal
            for t in tuple(self.TYPECODES):
                for n in range(1, 10):
                    z = array(t, [0]*n)
                    s = array(t, list(range(n)))
                    r = array(t, [0]*n)
                    test(equal, z, s, r, t)
        def testArray1(self):
            self._testArray(self._test1)
        def testArray21(self):
            self._testArray(self._test21)
        def testArray22(self):
            self._testArray(self._test22)
        def testArray31(self):
            self._testArray(self._test31)
        def testArray32(self):
            self._testArray(self._test32)
        def testArray4(self):
            self._testArray(self._test4)

    if HAVE_NUMPY:
        def _testNumPy(self, test):
            from numpy import zeros, arange, empty
            for t in tuple(self.TYPECODES):
                for n in range(10):
                    z = zeros (n, dtype=t)
                    s = arange(n, dtype=t)
                    r = empty (n, dtype=t)
                    test(allclose, z, s, r, t)
        def testNumPy1(self):
            self._testNumPy(self._test1)
        def testNumPy21(self):
            self._testNumPy(self._test21)
        def testNumPy22(self):
            self._testNumPy(self._test22)
        def testNumPy31(self):
            self._testNumPy(self._test31)
        def testNumPy32(self):
            self._testNumPy(self._test32)
        def testNumPy4(self):
            self._testNumPy(self._test4)


if __name__ == '__main__':
    unittest.main()
