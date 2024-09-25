from __future__ import annotations
from typing import NamedTuple, List, Dict, Callable, Union, TypeVar, Any, cast

import pandas as pd
from pandas.api.types import is_numeric_dtype, is_string_dtype  # pyright: ignore [reportUnknownVariableType]
from shiny import Session

import pyshiny_adaptive_filter.adaptive_filter as adaptive_filter

T = TypeVar("T")


class PdIndexAny(pd.Index): ...


class OtherColumnFilterIndexData(NamedTuple):
    """For a given column, store the current filter index values,
    but also store the intersection of all the other filter index values
    except for the current column.
    that is, other_idx stores the intersection of all the values
    except for the current column
    """

    col: str
    filter_idx: PdIndexAny[Any]
    other_idx: "pd.Index[Any]"


# we want to call this such that when index_intersection_all is called,
# we always pass in the full list of index values to be intersected
# NOTE: we are now able to pass in None values to be intersected,
# this is different from user selecting everything
# this None means the filter itself is empty
def index_intersection_all(
    to_intersect: List["pd.Index[Any] | None"],
    default: "pd.Index[Any]",
) -> "pd.Index[Any]":
    """Returns the intersection (all common values)
    across a list of pandas index values.

    Parameters
    ----------
    to_intersect : list
        List containing pandas index objects. List item can be None.
    default: pd.Index
        Pandas index to use if all values in `to_intersect` is all None.
        This is typically the index of the full dataset.


    Returns
    -------
    pd.Index
        A pandas Index object.
    """
    intersect: List["pd.Index[Any]"] = [
        x for x in to_intersect if x is not None
    ]

    if len(intersect) == 0:
        return default

    if len(intersect) == 1:
        return intersect[0]

    intersection = intersect[0]
    for index in intersect:
        intersection = intersection.intersection(index)

    return intersection


def create_other_column_filter_index_data(
    col_filter_idx: Dict[str, "pd.Index[Any]"],
    default: "pd.Index[Any]",
) -> List[OtherColumnFilterIndexData]:
    """
    tracking each column, the filter indices, and all the other filter indices
    this does not calculate the other filter indices yet.
    other index is set to empty Index

    this way every column has some consistent results/value

    col_filter_idx: dict of column name,
        and the indices that match the corresponding filter
    """
    other_column_filter_index: List[OtherColumnFilterIndexData] = []

    for col, filter_index in col_filter_idx.items():
        other_indices = [idx for c, idx in col_filter_idx.items() if c != col]

        other_column_filter_index.append(
            OtherColumnFilterIndexData(
                col=col,
                filter_idx=filter_index,
                other_idx=index_intersection_all(
                    other_indices,
                    default=default,
                ),
            )
        )
    return other_column_filter_index


def filters_by_colname(
    df: Callable[[], pd.DataFrame],
    session: Session,
) -> Dict[str, adaptive_filter.BaseFilter]:
    filters_by_colname_dict: Dict[str, adaptive_filter.BaseFilter] = dict()

    for col in df().columns:
        filters_by_colname_dict[col] = calc_col_type(
            df=df,
            id=f"filter_{col}",
            col_str=col,
            label=f"{col}",
            session=session,
        )

    return filters_by_colname_dict


def calc_col_type(
    df: Callable[[], pd.DataFrame] | pd.DataFrame,
    id: str,
    col_str: str,
    label: str,
    session: Session,
) -> Union[
    adaptive_filter.FilterCatStringSelect,
    adaptive_filter.FilterCatNumericSelect,
    adaptive_filter.FilterNumNumericRange,
    adaptive_filter.FilterCatStringCheckbox,
]:
    col_value: "pd.Series[Any]" = df()[col_str]
    num_unique = col_value.nunique()

    if is_string_dtype(col_value):
        if num_unique < 3:
            return adaptive_filter.FilterCatStringCheckbox(
                label=label
            ).finish_init(df, id, col_str, session=session)
        else:
            return adaptive_filter.FilterCatStringSelect(
                label=label
            ).finish_init(df, id, col_str, session=session)
    elif is_numeric_dtype(col_value):
        # TODO: add checkbox for numeric < 3
        if num_unique <= 10:
            return adaptive_filter.FilterCatNumericSelect(
                label=label
            ).finish_init(df, id, col_str, session=session)
        else:
            return adaptive_filter.FilterNumNumericRange(
                label=label
            ).finish_init(df, id, col_str, session=session)
    else:
        raise ValueError
