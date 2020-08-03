# -*- coding: utf-8 -*-
"""
Cinespace .csp LUT Format Input / Output Utilities
==================================================

Defines *Cinespace* *.csp* *LUT* Format related input / output utilities
objects.

-   :func:`colour.io.read_LUT_Cinespace`
-   :func:`colour.io.write_LUT_Cinespace`

References
----------
-   :cite:`RisingSunResearch` : Rising Sun Research. (n.d.). cineSpace LUT
    Library. Retrieved November 30, 2018, from
    https://sourceforge.net/projects/cinespacelutlib/
"""

from __future__ import division, unicode_literals

import colour.ndarray as np

from colour.io.luts import LUT1D, LUT3x1D, LUT3D, LUTSequence
from colour.utilities import tsplit, tstack, as_float_array, as_int_array

__author__ = 'Colour Developers'
__copyright__ = 'Copyright (C) 2013-2020 - Colour Developers'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Colour Developers'
__email__ = 'colour-developers@colour-science.org'
__status__ = 'Production'

__all__ = ['read_LUT_Cinespace', 'write_LUT_Cinespace']


def read_LUT_Cinespace(path):
    """
    Reads given *Cinespace* *.csp* *LUT* file.

    Parameters
    ----------
    path : unicode
        *LUT* path.

    Returns
    -------
    LUT3x1D or LUT3D or LUTSequence
        :class:`LUT3x1D` or :class:`LUT3D` or :class:`LUTSequence` class
        instance.

    References
    ----------
    :cite:`RisingSunResearch`

    Examples
    --------
    Reading a 3x1D *Cinespace* *.csp* *LUT*:

    >>> import os
    >>> path = os.path.join(
    ...     os.path.dirname(__file__), 'tests', 'resources', 'cinespace',
    ...     'ACES_Proxy_10_to_ACES.csp')
    >>> print(read_LUT_Cinespace(path))
    LUT3x1D - ACES Proxy 10 to ACES
    -------------------------------
    <BLANKLINE>
    Dimensions : 2
    Domain     : [[ 0.  0.  0.]
                  [ 1.  1.  1.]]
    Size       : (32, 3)

    Reading a 3D *Cinespace* *.csp* *LUT*:

    >>> path = os.path.join(
    ...     os.path.dirname(__file__), 'tests', 'resources', 'cinespace',
    ...     'Colour_Correct.csp')
    >>> print(read_LUT_Cinespace(path))
    LUT3D - Generated by Foundry::LUT
    ---------------------------------
    <BLANKLINE>
    Dimensions : 3
    Domain     : [[ 0.  0.  0.]
                  [ 1.  1.  1.]]
    Size       : (4, 4, 4, 3)
    """

    unity_range = np.array([[0., 0., 0.], [1., 1., 1.]])

    def _parse_metadata_section(metadata):
        """
        Parses the metadata at given lines.
        """

        return (metadata[0], metadata[1:]) if len(metadata) > 0 else ('', [])

    def _parse_domain_section(lines):
        """
        Parses the domain at given lines.
        """

        pre_LUT_size = max([int(lines[i]) for i in [0, 3, 6]])
        pre_LUT = [
            as_float_array(lines[i].split()) for i in [1, 2, 4, 5, 7, 8]
        ]
        pre_LUT_padded = []

        for row in pre_LUT:
            if len(row) != pre_LUT_size:
                pre_LUT_padded.append(
                    np.pad(
                        row, (0, pre_LUT_size - row.shape[0]),
                        mode='constant',
                        constant_values=np.nan))
            else:
                pre_LUT_padded.append(row)
        pre_LUT = np.asarray(pre_LUT_padded)

        return pre_LUT

    def _parse_table_section(lines):
        """
        Parses the table at given lines.
        """

        size = as_int_array(lines[0].split())
        table = as_float_array([line.split() for line in lines[1:]])

        return size, table

    with open(path) as csp_file:
        lines = csp_file.readlines()
        assert len(lines) > 0, 'LUT file empty!'
        lines = [line.strip() for line in lines if line.strip()]

        header = lines[0]
        assert header == 'CSPLUTV100', 'Invalid header!'

        kind = lines[1]
        assert kind in ('1D', '3D'), 'Invalid kind!'

        is_3D = kind == '3D'

        seek = 2
        metadata = []
        is_metadata = False
        for i, line in enumerate(lines[2:]):
            line = line.strip()
            if line == 'BEGIN METADATA':
                is_metadata = True
                continue
            elif line == 'END METADATA':
                seek += i
                break

            if is_metadata:
                metadata.append(line)

        title, comments = _parse_metadata_section(metadata)

        seek += 1
        pre_LUT = _parse_domain_section(lines[seek:seek + 9])

        seek += 9
        size, table = _parse_table_section(lines[seek:])

        assert np.product(size) == len(table), 'Invalid table size!'

        if (is_3D and pre_LUT.shape == (6, 2) and np.array_equal(
                pre_LUT.reshape(3, 4).transpose()[2:4], unity_range)):
            if np.__name__ == 'cupy':
                table = table.reshape(
                    [size[0].item(), size[1].item(), size[2].item(), 3],
                    order='F')
            else:
                table = table.reshape(
                    [size[0], size[1], size[2], 3], order='F')
            LUT = LUT3D(
                domain=pre_LUT.reshape(3, 4).transpose()[0:2],
                name=title,
                comments=comments,
                table=table)
            return LUT

        if (not is_3D and pre_LUT.shape == (6, 2) and np.array_equal(
                pre_LUT.reshape(3, 4).transpose()[2:4], unity_range)):
            LUT = LUT3x1D(
                domain=pre_LUT.reshape(3, 4).transpose()[0:2],
                name=title,
                comments=comments,
                table=table)

            return LUT

        if is_3D:
            pre_domain = tstack((pre_LUT[0], pre_LUT[2], pre_LUT[4]))
            pre_table = tstack((pre_LUT[1], pre_LUT[3], pre_LUT[5]))
            shaper_name = '{0} - Shaper'.format(title)
            cube_name = '{0} - Cube'.format(title)
            if np.__name__ == 'cupy':
                table = table.reshape(
                    [size[0].item(), size[1].item(), size[2].item(), 3],
                    order='F')
            else:
                table = table.reshape(
                    [size[0], size[1], size[2], 3], order='F')
            LUT_A = LUT3x1D(pre_table, shaper_name, pre_domain)
            LUT_B = LUT3D(table, cube_name, comments=comments)

            return LUTSequence(LUT_A, LUT_B)

        if not is_3D:
            pre_domain = tstack((pre_LUT[0], pre_LUT[2], pre_LUT[4]))
            pre_table = tstack((pre_LUT[1], pre_LUT[3], pre_LUT[5]))

            if table.shape == (2, 3):
                table_max = table[1]
                table_min = table[0]
                pre_table *= (table_max - table_min)
                pre_table += table_min

                return LUT3x1D(pre_table, title, pre_domain, comments=comments)
            else:
                pre_name = '{0} - PreLUT'.format(title)
                table_name = '{0} - Table'.format(title)
                LUT_A = LUT3x1D(pre_table, pre_name, pre_domain)
                LUT_B = LUT3x1D(table, table_name, comments=comments)

                return LUTSequence(LUT_A, LUT_B)


def write_LUT_Cinespace(LUT, path, decimals=7):
    """
    Writes given *LUT* to given  *Cinespace* *.csp* *LUT* file.

    Parameters
    ----------
    LUT : LUT1D or LUT3x1D or LUT3D or LUTSequence
        :class:`LUT1D`, :class:`LUT3x1D` or :class:`LUT3D` or
        :class:`LUTSequence` class instance to write at given path.
    path : unicode
        *LUT* path.
    decimals : int, optional
        Formatting decimals.

    Returns
    -------
    bool
        Definition success.

    References
    ----------
    :cite:`RisingSunResearch`

    Examples
    --------
    Writing a 3x1D *Cinespace* *.csp* *LUT*:

    >>> from colour.algebra import spow
    >>> domain = np.array([[-0.1, -0.2, -0.4], [1.5, 3.0, 6.0]])
    >>> LUT = LUT3x1D(
    ...     spow(LUT3x1D.linear_table(16, domain), 1 / 2.2),
    ...     'My LUT',
    ...     domain,
    ...     comments=['A first comment.', 'A second comment.'])
    >>> write_LUT_Cinespace(LUT, 'My_LUT.cube')  # doctest: +SKIP

    Writing a 3D *Cinespace* *.csp* *LUT*:

    >>> domain = np.array([[-0.1, -0.2, -0.4], [1.5, 3.0, 6.0]])
    >>> LUT = LUT3D(
    ...     spow(LUT3D.linear_table(16, domain), 1 / 2.2),
    ...     'My LUT',
    ...     domain,
    ...     comments=['A first comment.', 'A second comment.'])
    >>> write_LUT_Cinespace(LUT, 'My_LUT.cube')  # doctest: +SKIP
    """

    has_3D, has_3x1D, non_uniform = False, False, False

    if isinstance(LUT, LUTSequence):
        assert (len(LUT) == 2 and
                (isinstance(LUT[0], LUT1D) or isinstance(LUT[0], LUT3x1D)) and
                isinstance(LUT[1],
                           LUT3D)), 'LUTSequence must be 1D+3D or 3x1D+3D!'
        has_3x1D = True
        has_3D = True
        name = LUT[1].name
        if isinstance(LUT[0], LUT1D):
            non_uniform = LUT[0].is_domain_explicit()
            LUT[0] = LUT[0].as_LUT(LUT3x1D)

    elif isinstance(LUT, LUT1D):
        non_uniform = LUT.is_domain_explicit()
        name = LUT.name
        LUT = LUTSequence(LUT.as_LUT(LUT3x1D), LUT3D())
        has_3x1D = True

    elif isinstance(LUT, LUT3x1D):
        non_uniform = LUT.is_domain_explicit()
        name = LUT.name
        LUT = LUTSequence(LUT, LUT3D())
        has_3x1D = True

    elif isinstance(LUT, LUT3D):
        name = LUT.name
        LUT = LUTSequence(LUT3x1D(), LUT)
        has_3D = True

    else:
        raise ValueError('LUT must be 1D, 3x1D, 3D, 1D + 3D or 3x1D + 3D!')

    if has_3x1D:
        assert 2 <= LUT[0].size <= 65536, (
            'Shaper size must be in domain [2, 65536]!')
    if has_3D:
        assert 2 <= LUT[1].size <= 256, 'Cube size must be in domain [2, 256]!'

    def _ragged_size(table):
        """
        Return the ragged size of given table.
        """

        R, G, B = tsplit(table)

        R_len = R.shape[-1] - np.sum(np.isnan(R))
        G_len = G.shape[-1] - np.sum(np.isnan(G))
        B_len = B.shape[-1] - np.sum(np.isnan(B))

        return [R_len, G_len, B_len]

    def _format_array(array):
        """
        Formats given array as a *Cinespace* *.cube* data row.
        """

        return '{1:0.{0}f} {2:0.{0}f} {3:0.{0}f}'.format(decimals, *array)

    def _format_tuple(array):
        """
        Formats given array as 2 space separated values to *decimals*
        precision.
        """

        return '{1:0.{0}f} {2:0.{0}f}'.format(decimals, *array)

    with open(path, 'w') as csp_file:
        csp_file.write('CSPLUTV100\n')

        if has_3D:
            csp_file.write('3D\n\n')
        else:
            csp_file.write('1D\n\n')

        csp_file.write('BEGIN METADATA\n')
        csp_file.write('{0}\n'.format(name))

        if LUT[0].comments:
            for comment in LUT[0].comments:
                csp_file.write('{0}\n'.format(comment))

        if LUT[1].comments:
            for comment in LUT[1].comments:
                csp_file.write('{0}\n'.format(comment))

        csp_file.write('END METADATA\n\n')

        if has_3D or non_uniform:
            if has_3x1D:
                for i in range(3):
                    if LUT[0].is_domain_explicit():
                        size = _ragged_size(LUT[0].domain)[i]
                        table_min = np.nanmin(LUT[0].table)
                        table_max = np.nanmax(LUT[0].table)
                    else:
                        size = LUT[0].size

                    csp_file.write('{0}\n'.format(size))

                    for j in range(size):
                        if LUT[0].is_domain_explicit():
                            entry = LUT[0].domain[j][i]
                        else:
                            entry = (
                                LUT[0].domain[0][i] + j *
                                (LUT[0].domain[1][i] - LUT[0].domain[0][i]) /
                                (LUT[0].size - 1))
                        csp_file.write('{0:.{1}f} '.format(entry, decimals))

                    csp_file.write('\n')

                    for j in range(size):
                        entry = LUT[0].table[j][i]
                        if non_uniform:
                            entry -= table_min
                            entry /= (table_max - table_min)
                        csp_file.write('{0:.{1}f} '.format(entry, decimals))

                    csp_file.write('\n')
            else:
                for i in range(3):
                    csp_file.write('2\n')
                    csp_file.write('{0}\n'.format(
                        _format_tuple(
                            [LUT[1].domain[0][i], LUT[1].domain[1][i]])))
                    csp_file.write('{0:.{2}f} {1:.{2}f}\n'.format(
                        0, 1, decimals))
            if non_uniform:
                csp_file.write('\n{0}\n'.format(2))
                row = [table_min, table_min, table_min]
                csp_file.write('{0}\n'.format(_format_array(row)))
                row = [table_max, table_max, table_max]
                csp_file.write('{0}\n'.format(_format_array(row)))
            else:
                csp_file.write('\n{0} {1} {2}\n'.format(
                    LUT[1].table.shape[0], LUT[1].table.shape[1],
                    LUT[1].table.shape[2]))
                table = LUT[1].table.reshape([-1, 3], order='F')

                for row in table:
                    csp_file.write('{0}\n'.format(_format_array(row)))

        else:
            for i in range(3):
                csp_file.write('2\n')
                csp_file.write('{0}\n'.format(
                    _format_tuple([LUT[0].domain[0][i], LUT[0].domain[1][i]])))
                csp_file.write('0.0 1.0\n')
            csp_file.write('\n{0}\n'.format(LUT[0].size))
            table = LUT[0].table

            for row in table:
                csp_file.write('{0}\n'.format(_format_array(row)))

    return True
