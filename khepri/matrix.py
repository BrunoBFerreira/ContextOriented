#Copyright Billyoyo

import math


class InvalidMatrixDimensions(Exception):
    """Matrix was created with invalid matrix compared to its raw list"""
    pass


class MismatchedMatrixDimensions(Exception):
    """Arithmetic was attempted on one or more matrix with invalid or incompatible dimensions"""
    pass


class UninvertibleMatrix(Exception):
    """Matrix is uninvertible (cannot be inverted)"""
    pass


class CombinedMatrix:
    """Class for performing gaussian elimination operations"""

    def __init__(self, left, right):
        self.left = left
        self.right = right
        if not (left.width == right.width and left.height == right.height and left.width == left.height):
            raise MismatchedMatrixDimensions

    def add(self, row_origin, row_dest, coef):
        """Add one row to another, multiplied by a coefficient

        Arguments:
        row_origin -- the y value of the row you're adding (integer)
        row_dest -- the y value of the row you're adding to (integer)
        coef -- the coefficient you're multiplying row_origin by (float)"""
        for y in range(self.left.width):
            self.left[y, row_dest] = self.left[y, row_dest] + (self.left[y, row_origin] * coef)
            self.right[y, row_dest] = self.right[y, row_dest] + (self.right[y, row_origin] * coef)

    def mult(self, row, coef):
        """Multiply the row by a coefficient

        Arguments:
        row -- the y value of the row you're multiplying (integer)
        coef -- the coefficient you're multiplying the row by (float) """
        for y in range(self.left.width):
            self.left[y, row] = self.left[y, row] * coef
            self.right[y, row] = self.right[y, row] * coef

    def swap(self, row1, row2):
        """Swap two rows

        Arguments:
        row1 -- the y value of the first row you want to swap
        row2 -- the y value of the second row you want to swap"""
        for y in range(self.left.width):
            temp = self.left[y, row2]
            self.left[y, row2] = self.left[y, row1]
            self.left[y, row1] = temp

            temp = self.right[y, row2]
            self.right[y, row2] = self.right[y, row1]
            self.right[y, row1] = temp

    def sort_pivot(self, row):
        """Move down the matrix, looking for the first pivot found in the correct column
        if none found matrix is uninvertible (as there must be a zero column)

        Arguments:
        row -- the y value of the row you want to find the pivot for (pivot must be at (row, row))"""
        i = row
        while i < self.left.height and self.left.get_pivot(i) != row:
            i += 1
        if i == self.left.height:
            raise UninvertibleMatrix
        else:
            self.swap(i, row)


class Matrix:
    """Matrix class allows for indexing"""

    @staticmethod
    def identity(size):
        """Get an identity matrix with dimensions (size x size)

        Arguments:
        size -- the dimension of the square matrix (integer)"""
        matrix = Matrix(size, size)
        for i in range(size):
            matrix[i, i] = 1
        return matrix

    def __init__(self, width, height=None, oheight=None):
        """Create a matrix,

        Can be called in the following ways:
        Matrix(raw_2d_list)                - calculates the width and height of the matrix
        Matrix(raw_2d_list, width, height) - if width and height are known, the speeds up the initialization.
        Matrix(width, height)              - creates a zero matrix of the given dimensions

        Arguments:
        raw_2d_list -- a two dimensional array
        width -- integer describing the amount of columns in the matrix
        height -- integer describing the amount of rows in the matrix"""
        if type(width) is int:
            self.width = width
            self.height = height
            if self.width > 0 and self.height > 0:
                self._raw = [[0] * height for x in range(width)]
            else:
                raise InvalidMatrixDimensions
        else:
            self._raw = width
            if oheight is not None:
                self.width = height
                self.height = oheight
            else:
                self.width = len(self._raw)
                if self.width > 0:
                    self.height = len(self._raw[0])
                    if self.height > 0:
                        for row in self._raw:
                            if len(row) != self.height:
                                raise InvalidMatrixDimensions
                    else:
                        raise InvalidMatrixDimensions
                else:
                    raise InvalidMatrixDimensions

    def get_pivot(self, row):
        """Find the pivot for that row

        Arguments:
        row -- the row you want to find the pivot for"""
        y = 0
        while y < self.height and self[y, row] == 0:
            y += 1
        if y == self.height:
            return None
        else:
            return y

    def ref(self):
        """Converts the matrix to row echelon form"""
        if self.width == self.height:
            if self.width == 1:
                return self.copy()
            else:
                template = Matrix.identity(self.width)
                comb = CombinedMatrix(self.copy(), template)
                for i in range(comb.left.height):
                    comb.sort_pivot(i)
                    for j in range(i+1, comb.left.height):
                        comb.add(i, j, -comb.left[i, j]/comb.left[i, i])
                return comb.left
        else:
            raise UninvertibleMatrix

    def det(self):
        """Finds the determinant of the matrix"""
        ref = self.ref()
        total = 1
        for i in range(self.width):
            total *= ref[i, i]
        return total

    def inverse(self):
        """Find the inverse of a matrix"""
        if self.width == self.height:
            if self.width == 1:
                return Matrix([[1/self[0, 0]]], 1, 1)
            else:
                template = Matrix.identity(self.width)
                comb = CombinedMatrix(self.copy(), template)
                for i in range(comb.left.height):
                    comb.sort_pivot(i)
                    comb.mult(i, 1.0/comb.left[i, i])
                    for j in range(comb.left.height):
                        if i != j:
                            comb.add(i, j, -comb.left[i, j])
                return comb.right
        else:
            raise UninvertibleMatrix

    def copy(self):
        """Return an exact copy of the matrix (none-deep, individual values will NOT be copied)"""
        return Matrix([[v for v in row] for row in self._raw], self.width, self.height)

    def __add__(self, other):
        if type(other) is Matrix:
            if self.width != other.width or self.height != other.height:
                raise MismatchedMatrixDimensions
            return Matrix([[other[x, y] + self[x, y] for x in range(self.height)] for y in range(self.width)], self.width, self.height)
        else:
            return Matrix([[self[x, y] + other for x in range(self.height)] for y in range(self.width)], self.width, self.height)

    def __sub__(self, other):
        if type(other) is Matrix:
            if self.width != other.width or self.height != other.height:
                raise MismatchedMatrixDimensions
            return Matrix([[self[x, y] - other[x, y] for x in range(self.height)] for y in range(self.width)],
                          self.width, self.height)
        else:
            return Matrix([[self[x, y] - other for x in range(self.height)] for y in range(self.width)], self.width,
                          self.height)

    def __mul__(self, other):
        if type(other) is Matrix:
            if self.width != other.height:
                raise MismatchedMatrixDimensions
            return Matrix([[ sum(self[i, y] * other[x, i] for i in range(self.width)) for x in range(self.height)] for y in range(other.width)], other.width, self.height)
        else:
            return Matrix([[self[x, y] * other for x in range(self.height)] for y in range(self.width)], self.width,
                          self.height)

    def __truediv__(self, other):
        if type(other) is Matrix:
            return self * other.inverse()
        else:
            return Matrix([[self[x, y] / other for x in range(self.height)] for y in range(self.width)], self.width,
                          self.height)

    def __invert__(self):
        return self.inverse()

    def __abs__(self):
        return Matrix([[abs(self[x, y]) for x in range(self.height)] for y in range(self.width)], self.width,
                      self.height)

    def __mod__(self, other):
        return Matrix([[self[x, y] % other for x in range(self.height)] for y in range(self.width)], self.width,
                      self.height)

    def __neg__(self):
        return Matrix([[-self[x, y] for x in range(self.height)] for y in range(self.width)], self.width,
                      self.height)

    def __int__(self):
        return Matrix([[int(self[x, y]) for x in range(self.height)] for y in range(self.width)], self.width,
                      self.height)

    def __float__(self):
        return Matrix([[float(self[x, y]) for x in range(self.height)] for y in range(self.width)], self.width,
                      self.height)

    def __pow__(self, power, modulo=None):
        """Raise a matrix to a power,
        matrix must be square and power must be an integer"""
        if type(power) is int:
            if power < 1:
                matrix = self.inverse()
                power *= -1
            else:
                matrix = self.copy()
            cpow = 1
            powers = [None] * (power+1)
            powers[1] = matrix
            while cpow < power:
                remaining = power - cpow
                if remaining >= cpow:
                    matrix = matrix * matrix
                    cpow *= 2
                    powers[cpow] = matrix
                elif powers[remaining] is not None:
                    matrix = matrix * powers[remaining]
                    cpow += remaining
                elif remaining % 2 == 1:
                    matrix = matrix * powers[1]
                    cpow += 1
                    powers[cpow] = matrix
                else:
                    nextpow = math.floor(remaining/4) * 4
                    if powers[nextpow] is not None:
                        matrix = matrix * powers[nextpow]
                        cpow += nextpow
                        powers[cpow] = matrix
                    else:
                        matrix = matrix * powers[2]
                        cpow += 2
                        powers[cpow] = matrix
            del powers
            return matrix
        else:
            raise TypeError

    def __call__(self, *filters):
        """Apply some filters to every element in the matrix

        Arguments:
        *filters - any amount of callables with arguments x, y, v (v is the element)"""
        def applyAll(x, y, v):
            for filter in filters:
                v = filter(x, y, v)
            return v
        return Matrix([[applyAll(x, y, self[x, y]) for x in range(self.height)] for y in range(self.width)], self.width,
                      self.height)

    def __eq__(self, other):
        if type(other) is Matrix:
            if self.width == other.width and self.height == other.height:
                for x in range(self.width):
                    for y in range(self.height):
                        if self[x, y] != other[x, y]:
                            return False
            else:
                return False
        else:
            for x in range(self.width):
                for y in range(self.height):
                    if self[x, y] != other:
                        return False
        return True

    def __ne__(self, other):
        if type(other) is Matrix:
            if self.width == other.width and self.height == other.height:
                for x in range(self.width):
                    for y in range(self.height):
                        if self[x, y] == other[x, y]:
                            return True
            else:
                return True
        else:
            for x in range(self.width):
                for y in range(self.height):
                    if self[x, y] == other:
                        return True
        return False

    def __gt__(self, other):
        if type(other) is Matrix:
            if self.width == other.width and self.height == other.height:
                for x in range(self.width):
                    for y in range(self.height):
                        if self[x, y] <= other[x, y]:
                            return False
            else:
                return False
        else:
            for x in range(self.width):
                for y in range(self.height):
                    if self[x, y] <= other:
                        return False
        return True

    def __ge__(self, other):
        if type(other) is Matrix:
            if self.width == other.width and self.height == other.height:
                for x in range(self.width):
                    for y in range(self.height):
                        if self[x, y] < other[x, y]:
                            return False
            else:
                return False
        else:
            for x in range(self.width):
                for y in range(self.height):
                    if self[x, y] < other:
                        return False
        return True

    def __lt__(self, other):
        if type(other) is Matrix:
            if self.width == other.width and self.height == other.height:
                for x in range(self.width):
                    for y in range(self.height):
                        if self[x, y] >= other[x, y]:
                            return False
            else:
                return False
        else:
            for x in range(self.width):
                for y in range(self.height):
                    if self[x, y] >= other:
                        return False
        return True

    def __le__(self, other):
        if type(other) is Matrix:
            if self.width == other.width and self.height == other.height:
                for x in range(self.width):
                    for y in range(self.height):
                        if self[x, y] > other[x, y]:
                            return False
            else:
                return False
        else:
            for x in range(self.width):
                for y in range(self.height):
                    if self[x, y] > other:
                        return False
        return True

    def __contains__(self, item):
        for x in range(self.width):
            for y in range(self.height):
                if self[x, y] == item:
                    return True
        return False

    def __getitem__(self, item):
        x, y = item
        if type(x) is slice or type(y) is slice:
            subset = self._raw[y]
            if type(subset[0]) is not list:
                subset = [subset]
            yisslice = type(x) is slice
            for cx in range(len(subset)):
                subset[cx] = subset[cx][x]
                if not yisslice:
                    subset[cx] = [subset[cx]]
            return Matrix(subset)
        else:
            return self._raw[y][x]

    def __setitem__(self, item, value):
        x, y = item
        if type(x) is slice or type(y) is slice:
            start_x, end_x = x, x
            if type(x) is slice:
                start_x = x.start
                if start_x is None:
                    start_x = 0
                end_x = x.stop
                if end_x is None:
                    end_x = self.width
            else:
                end_x += 1
            start_y, end_y = y, y
            if type(y) is slice:
                start_y = y.start
                if start_y is None:
                    start_y = 0
                end_y = y.stop
                if end_y is None:
                    end_y = self.height
            else:
                end_y += 1
            if type(value) is Matrix:
                if end_x - start_x == value.width and end_y - start_y == value.height:
                    for x in range(start_x, end_x):
                        for y in range(start_y, end_y):
                            self._raw[y][x] = value._raw[y-start_y][x-start_x]
                else:
                    raise MismatchedMatrixDimensions
            else:
                for x in range(start_x, end_x):
                    for y in range(start_y, end_y):
                        self[x, y] = value
        else:
            self._raw[y][x] = value

    def __str__(self):
        return str("(" + ")\n(".join(" ".join(str(i) for i in row) for row in self._raw) + ")")
