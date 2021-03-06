import unittest

import numpy
try:
    import scipy.sparse
    scipy_available = True
except ImportError:
    scipy_available = False

import cupy
import cupy.sparse
from cupy import testing


def _make(xp, sp, dtype):
    data = xp.array([0, 1, 2, 3], dtype)
    row = xp.array([0, 0, 1, 2], 'i')
    col = xp.array([0, 1, 3, 2], 'i')
    # 0, 1, 0, 0
    # 0, 0, 0, 2
    # 0, 0, 3, 0
    return sp.coo_matrix((data, (row, col)), shape=(3, 4))


def _make_unordered(xp, sp, dtype):
    data = xp.array([1, 4, 3, 2], dtype)
    row = xp.array([0, 2, 1, 0], 'i')
    col = xp.array([0, 2, 3, 1], 'i')
    # 1, 2, 0, 0
    # 0, 0, 0, 3
    # 0, 0, 4, 0
    return sp.coo_matrix((data, (row, col)), shape=(3, 4))


@testing.parameterize(*testing.product({
    'dtype': [numpy.float32, numpy.float64],
}))
class TestCooMatrix(unittest.TestCase):

    def setUp(self):
        self.m = _make(cupy, cupy.sparse, self.dtype)

    def test_dtype(self):
        self.assertEqual(self.m.dtype, self.dtype)

    def test_data(self):
        self.assertEqual(self.m.data.dtype, self.dtype)
        testing.assert_array_equal(
            self.m.data, cupy.array([0, 1, 2, 3], self.dtype))

    def test_row(self):
        self.assertEqual(self.m.row.dtype, numpy.int32)
        testing.assert_array_equal(
            self.m.row, cupy.array([0, 0, 1, 2], self.dtype))

    def test_col(self):
        self.assertEqual(self.m.col.dtype, numpy.int32)
        testing.assert_array_equal(
            self.m.col, cupy.array([0, 1, 3, 2], self.dtype))

    def test_shape(self):
        self.assertEqual(self.m.shape, (3, 4))

    def test_ndim(self):
        self.assertEqual(self.m.ndim, 2)

    def test_nnz(self):
        self.assertEqual(self.m.nnz, 4)

    @unittest.skipUnless(scipy_available, 'requires scipy')
    def test_get(self):
        m = self.m.get()
        self.assertIsInstance(m, scipy.sparse.coo_matrix)
        expect = [
            [0, 1, 0, 0],
            [0, 0, 0, 2],
            [0, 0, 3, 0]
        ]
        numpy.testing.assert_allclose(m.toarray(), expect)

    @unittest.skipUnless(scipy_available, 'requires scipy')
    def test_str(self):
        self.assertEqual(str(self.m), '''  (0, 0)\t0.0
  (0, 1)\t1.0
  (1, 3)\t2.0
  (2, 2)\t3.0''')

    def test_toarray(self):
        m = self.m.toarray()
        expect = [
            [0, 1, 0, 0],
            [0, 0, 0, 2],
            [0, 0, 3, 0]
        ]
        cupy.testing.assert_allclose(m, expect)


@testing.parameterize(*testing.product({
    'dtype': [numpy.float32, numpy.float64],
}))
@unittest.skipUnless(scipy_available, 'requires scipy')
class TestCooMatrixInit(unittest.TestCase):

    def setUp(self):
        self.shape = (3, 4)

    def data(self, xp):
        return xp.array([0, 1, 2, 3], self.dtype)

    def row(self, xp):
        return xp.array([0, 0, 1, 2], 'i')

    def col(self, xp):
        return xp.array([0, 1, 3, 2], 'i')

    @testing.numpy_cupy_equal(sp_name='sp')
    def test_shape_none(self, xp, sp):
        x = sp.coo_matrix(
            (self.data(xp), (self.row(xp), self.col(xp))), shape=None)
        self.assertEqual(x.shape, (3, 4))

    @testing.numpy_cupy_equal(sp_name='sp')
    def test_dtype(self, xp, sp):
        data = self.data(xp).astype('i')
        x = sp.coo_matrix(
            (data, (self.row(xp), self.col(xp))), dtype=self.dtype)
        self.assertEqual(x.dtype, self.dtype)

    @testing.numpy_cupy_equal(sp_name='sp')
    def test_copy_true(self, xp, sp):
        data = self.data(xp)
        row = self.row(xp)
        col = self.col(xp)
        x = sp.coo_matrix((data, (row, col)), copy=True)

        self.assertIsNot(data, x.data)
        self.assertIsNot(row, x.row)
        self.assertIsNot(col, x.col)

    @testing.numpy_cupy_raises(sp_name='sp')
    def test_invalid_format(self, xp, sp):
        sp.coo_matrix(
            (self.data(xp), self.row(xp)), shape=self.shape)

    @testing.numpy_cupy_raises(sp_name='sp')
    def test_shape_invalid(self, xp, sp):
        sp.coo_matrix(
            (self.data(xp), (self.row(xp), self.col(xp))), shape=(2,))

    def test_data_invalid(self):
        with self.assertRaises(ValueError):
            cupy.sparse.coo_matrix(
                ('invalid', (self.row(cupy), self.col(cupy))),
                shape=self.shape)

    @testing.numpy_cupy_raises(sp_name='sp')
    def test_data_invalid_ndim(self, xp, sp):
        sp.coo_matrix(
            (self.data(xp)[None], (self.row(xp), self.col(xp))),
            shape=self.shape)

    def test_row_invalid(self):
        with self.assertRaises(ValueError):
            cupy.sparse.coo_matrix(
                (self.data(cupy), ('invalid', self.col(cupy))),
                shape=self.shape)

    @testing.numpy_cupy_raises(sp_name='sp')
    def test_row_invalid_ndim(self, xp, sp):
        sp.coo_matrix(
            (self.data(xp), (self.row(xp)[None], self.col(xp))),
            shape=self.shape)

    def test_col_invalid(self):
        with self.assertRaises(ValueError):
            cupy.sparse.coo_matrix(
                (self.data(cupy), (self.row(cupy), 'invalid')),
                shape=self.shape)

    @testing.numpy_cupy_raises(sp_name='sp')
    def test_col_invalid_ndim(self, xp, sp):
        sp.coo_matrix(
            (self.data(xp), (self.row(xp), self.col(xp)[None])),
            shape=self.shape)

    @testing.numpy_cupy_raises(sp_name='sp')
    def test_data_different_length(self, xp, sp):
        data = xp.arange(5, dtype=self.dtype)
        sp.coo_matrix(
            (data(xp), (self.row(xp), self.col(xp))), shape=self.shape)

    @testing.numpy_cupy_raises(sp_name='sp')
    def test_row_different_length(self, xp, sp):
        row = xp.arange(5, dtype=self.dtype)
        sp.coo_matrix(
            (self.data(xp), (row(xp), self.col(xp))), shape=self.shape)

    @testing.numpy_cupy_raises(sp_name='sp')
    def test_col_different_length(self, xp, sp):
        col = xp.arange(5, dtype=self.dtype)
        sp.coo_matrix(
            (self.data(xp), (self.row(xp), col(xp))), shape=self.shape)

    @testing.numpy_cupy_raises(sp_name='sp')
    def test_fail_to_infer_shape(self, xp, sp):
        data = xp.array([], dtype=self.dtype)
        row = xp.array([], dtype='i')
        col = xp.array([], dtype='i')
        sp.coo_matrix((data, (row, col)), shape=None)

    @testing.numpy_cupy_raises(sp_name='sp')
    def test_row_too_large(self, xp, sp):
        row = xp.array([0, 0, 1, 3], 'i')
        sp.coo_matrix(
            (self.data(xp), (row, self.col(xp))), shape=self.shape)

    @testing.numpy_cupy_raises(sp_name='sp')
    def test_row_too_small(self, xp, sp):
        row = xp.array([0, -1, 1, 2], 'i')
        sp.coo_matrix(
            (self.data(xp), (row, self.col(xp))), shape=self.shape)

    @testing.numpy_cupy_raises(sp_name='sp')
    def test_col_too_large(self, xp, sp):
        col = xp.array([0, 1, 4, 2], 'i')
        sp.coo_matrix(
            (self.data(xp), (self.row(xp), col)), shape=self.shape)

    @testing.numpy_cupy_raises(sp_name='sp')
    def test_col_too_small(self, xp, sp):
        col = xp.array([0, -1, 3, 2], 'i')
        sp.coo_matrix(
            (self.data(xp), (self.row(xp), col)), shape=self.shape)

    def test_unsupported_dtype(self):
        with self.assertRaises(ValueError):
            cupy.sparse.coo_matrix(
                (self.data(cupy), (self.row(cupy), self.col(cupy))),
                shape=self.shape, dtype='i')


@testing.parameterize(*testing.product({
    'dtype': [numpy.float32, numpy.float64],
}))
@unittest.skipUnless(scipy_available, 'requires scipy')
class TestCooMatrixScipyComparison(unittest.TestCase):

    @testing.numpy_cupy_allclose(sp_name='sp')
    def test_toarray(self, xp, sp):
        m = _make(xp, sp, self.dtype)
        return m.toarray()

    @testing.numpy_cupy_allclose(sp_name='sp')
    def test_tocsc(self, xp, sp):
        m = _make(xp, sp, self.dtype)
        return m.tocsc().toarray()

    @testing.numpy_cupy_allclose(sp_name='sp')
    def test_tocsr(self, xp, sp):
        m = _make(xp, sp, self.dtype)
        return m.tocsr().toarray()

    @testing.numpy_cupy_allclose(sp_name='sp')
    def test_tocsr_unordered(self, xp, sp):
        m = _make_unordered(xp, sp, self.dtype)
        return m.tocsr().toarray()

    @testing.numpy_cupy_allclose(sp_name='sp')
    def test_transpose(self, xp, sp):
        m = _make(xp, sp, self.dtype)
        return m.transpose().toarray()


@testing.parameterize(*testing.product({
    'dtype': [numpy.float32, numpy.float64],
    'ufunc': [
        'arcsin', 'arcsinh', 'arctan', 'arctanh', 'ceil', 'deg2rad', 'expm1',
        'floor', 'log1p', 'rad2deg', 'rint', 'sign', 'sin', 'sinh', 'sqrt',
        'tan', 'tanh', 'trunc',
    ],
}))
@unittest.skipUnless(scipy_available, 'requires scipy')
class TestUfunc(unittest.TestCase):

    @testing.numpy_cupy_allclose(sp_name='sp', atol=1e-5)
    def test_ufun(self, xp, sp):
        x = _make(xp, sp, self.dtype)
        x.data *= 0.1
        return getattr(x, self.ufunc)().toarray()


class TestIsspmatrixCoo(unittest.TestCase):

    def test_coo(self):
        x = cupy.sparse.coo_matrix(
            (cupy.array([0], 'f'),
             (cupy.array([0], 'i'), cupy.array([0], 'i'))),
            shape=(1, 1), dtype='f')
        self.assertTrue(cupy.sparse.isspmatrix_coo(x))

    def test_csr(self):
        x = cupy.sparse.csr_matrix(
            (cupy.array([], 'f'),
             cupy.array([], 'i'),
             cupy.array([0], 'i')),
            shape=(0, 0), dtype='f')
        self.assertFalse(cupy.sparse.isspmatrix_coo(x))
