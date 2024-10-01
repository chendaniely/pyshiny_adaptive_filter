import pandas as pd

from shiny_adaptive_filter import helpers


idx1 = pd.Index([1, 2, 3, 4, 5])
idx2 = pd.Index([2, 3, 4, 5, 6])
idx3 = pd.Index([3, 4, 5, 6, 7])
default = pd.Index([1, 2, 3, 4, 5, 6, 7])


def test_index_intersection_all():
    """Test intersecting a list of pandas index"""
    # NOTE: an input index cannot be empty

    to_intersect = [idx1, idx2, idx3]
    expected = pd.Index([3, 4, 5])
    calculated = helpers.index_intersection_all(
        to_intersect,
        default=default,
    )
    assert (calculated == expected).all()
    assert calculated.equals(expected)

    to_intersect = [idx1, idx1, idx1]
    expected = idx1
    calculated = helpers.index_intersection_all(
        to_intersect,
        default=default,
    )
    assert (calculated == expected).all()
    assert calculated.equals(expected)


def test_index_intersection_all_none():
    to_intersect = [idx1, None]
    expected = idx1
    calculated = helpers.index_intersection_all(
        to_intersect,
        default=default,
    )
    assert (calculated == expected).all()
    assert calculated.equals(expected)


def test_index_intersection_all_default():
    """Test intersecting a list of pandas index with default"""
    to_intersect = [None, None, None]
    expected = pd.Index([1, 2, 3, 4, 5, 6, 7])
    calculated = helpers.index_intersection_all(
        to_intersect,
        default=pd.Index([1, 2, 3, 4, 5, 6, 7]),
    )

    assert (calculated == expected).all()
    assert calculated.equals(expected)
