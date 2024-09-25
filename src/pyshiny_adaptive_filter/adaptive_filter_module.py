from __future__ import annotations
from typing import Dict, Union, List, Callable, Any, cast, TypedDict
from pprint import pprint

from htmltools import Tag
import pandas as pd
from shiny import reactive, render, Inputs, Outputs, Session
from shiny import module, ui

import pyshiny_adaptive_filter.helpers as helpers
import pyshiny_adaptive_filter.adaptive_filter as adaptive_filter


class FilterServerResults(TypedDict):
    filter_idx: "pd.Index[Any]"
    filters: Dict[str, adaptive_filter.BaseFilter]
    reset_all: Callable[[], None]


@module.ui
def filter_ui():
    return ui.output_ui("render_all_filters")


@module.server
def filter_server(
    input: Inputs,
    output: Outputs,
    session: Session,
    df: Callable[[], pd.DataFrame] | pd.DataFrame,
    reset_id: str | None = None,
    override: Dict[str, Union[adaptive_filter.BaseFilter, str, None]] = {},
) -> FilterServerResults:
    #
    # begin server functions
    #

    @render.ui
    def render_all_filters() -> List[Tag]:  # type: ignore # unusedFunction
        """Render UI that creates all the filters for the module output
        This is the first part of the reactive chain
        """
        ui_elements = [
            filter_type_component.ui()
            for filter_type_component in cast(
                Dict, filters_by_colname()
            ).values()
        ]

        return ui_elements

    @reactive.calc
    def filters_by_colname() -> Dict[str, adaptive_filter.BaseFilter]:
        """Creates the individual UI elements.
        This is where we can handle the override inputs
        """

        def make_filter_obj(
            colname: str,
            filter: adaptive_filter.BaseFilter | str | None,
        ) -> adaptive_filter.BaseFilter:
            """Little hack to finish the initialization.
            To avoid dealing with the session within the module and
            from the app calling the module,
            we are passing in the constructor for each override
            """
            if isinstance(filter, adaptive_filter.BaseFilter):
                filter.finish_init(
                    data=df,
                    id=f"filter_{colname}",
                    column_name=colname,
                    session=session,
                )
                return filter

        # make all the filters
        filters_by_colname = helpers.filters_by_colname(df, session)

        # if a user passes in a basefilter, override the output
        valid_override = {
            key: make_filter_obj(key, val)
            for key, val in override.items()
            if key in df().columns
            and isinstance(val, adaptive_filter.BaseFilter)
        }
        filters_by_colname.update(valid_override)

        # remove filter if user passed in None
        none_override = [
            key
            for key, val in override.items()
            if key in df().columns and val is None
        ]
        filters_by_colname = {
            key: val
            for key, val in filters_by_colname.items()
            if key not in none_override
        }

        return filters_by_colname

    @reactive.calc
    def col_idx_intersection_others() -> (
        List[helpers.OtherColumnFilterIndexData]
    ):
        # these create a OtherColumnFilterIndexData data object
        col_fi_oi_data = helpers.create_other_column_filter_index_data(
            col_filter_idx(),
            default=df().index,
        )

        pprint(col_fi_oi_data)
        print()
        return col_fi_oi_data

    @reactive.effect
    def update_filters() -> None:
        for col, filter_idx, other_idx in col_idx_intersection_others():
            filters_by_colname()[col].narrow_options(
                other_idx.union(filter_idx)
                if filter_idx is not None
                else other_idx
            )

    @reactive.calc
    def col_filter_idx() -> Dict[str, "pd.Index[Any]"]:
        # keys are all columns
        # values are matching index
        # returns all index values if filter not used
        col_filter_idx: Dict[str, "pd.Index[Any]"] = dict()

        for col in filters_by_colname().keys():
            current_idx = filters_by_colname()[col].matching_rows()

            # collecting all the index values
            col_filter_idx[col] = current_idx

        return col_filter_idx

    @reactive.calc
    def filter_idx() -> "pd.Index[Any]":
        current_filters: List["pd.Index[Any]"] = [
            x.filter_idx for x in col_idx_intersection_others()
        ]
        intersection: "pd.Index[Any]" = helpers.index_intersection_all(
            current_filters,
            default=df().index,
        )

        return intersection

    def reset_all() -> None:
        for fltr in filters_by_colname().values():
            fltr.reset()

    return {
        "filter_idx": filter_idx,
        "filters": filters_by_colname,
        "reset_all": reset_all,
    }
