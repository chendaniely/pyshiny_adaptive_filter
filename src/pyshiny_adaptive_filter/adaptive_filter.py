from __future__ import annotations
from abc import ABC
from typing import Callable, TypeVar, Generic, List, Iterable, Dict, Any, Union
from typing import cast, Protocol

from htmltools import Tag
import pandas as pd
from shiny import Session, ui
from shiny.session import require_active_session, session_context


def return_index(df: pd.DataFrame) -> "pd.Index[Any]":
    """This function exists to make pyright errors go away
    when trying to pull the .index of a dataframe
    """
    return cast("pd.Index[Any]", df.index)


T = TypeVar("T")


class BaseFilter(ABC, Generic[T]):
    def __init__(self, *, label: str | None = None):
        self.label = label

    def finish_init(
        self,
        data: Callable[[], pd.DataFrame] | pd.DataFrame,
        id: str,
        column_name: str,
        *,
        session: Session | None = None,
    ):
        self.filter_id = id
        self.column_name = column_name
        self.data = data
        self.session = require_active_session(session)

        if self.label is None:
            # self.label = self.column_name.title()
            self.label = self.column_name

        return self

    def ui(self) -> ui.Tag: ...

    def matching_rows(self) -> Union["pd.Index[Any]", None]: ...

    # This is a side-effect function
    def narrow_options(self, valid_rows: "pd.Index[Any]") -> None: ...

    def reset(self) -> None:
        print(f"resetting placeholder for {self.column_name}")

    def _get_input_value(
        self,
    ) -> Iterable[T] | None:
        input = self.session.input

        # Check if the filter_id is in input and retrieve its value,
        # otherwise return None
        if self.filter_id not in input or not input[self.filter_id]():
            return None
        return input[self.filter_id]()


class FilterCatStringSelect(BaseFilter[str]):
    def ui(self) -> Tag:
        col_val_unique = cast(
            "pd.Series[str]",
            self.data()[self.column_name].unique(),  # type: ignore
        )
        choices: List[str] = sorted(col_val_unique.tolist())
        return ui.input_selectize(
            id=self.filter_id,
            label=self.label,
            choices=choices,
            multiple=True,
            remove_button=True,
            options={"plugins": ["clear_button"]},
        )

    def matching_rows(self) -> Union["pd.Index[Any]", None]:
        """Calculates the rows that match the current filter
        and returns an Index of the .matching rows
        """
        input_value = self._get_input_value()

        # If input_value is None, return all rows
        if input_value is None:
            return None

        # Otherwise, filter rows based on the input_value
        rtn: "pd.Index[Any]" = return_index(
            self.data().loc[self.data()[self.column_name].isin(input_value)]
        )

        return rtn

    def narrow_options(self, valid_rows: "pd.Index[Any]") -> None:
        """Updates the current filter values based on the values from other filters.
        This only does the component update,
        it does not perform the calculations needed to figure out what
        """
        input = self.session.input
        col_val_unique: pd.Series[str] = (
            self.data().loc[valid_rows, self.column_name].unique()
        )
        choices: List[str] = sorted(col_val_unique.tolist())

        ui.update_selectize(
            id=self.filter_id,
            choices=choices,
            selected=input[self.filter_id](),
        )

    def reset(self) -> None:
        with session_context(self.session):
            col_val_unique = cast(
                "pd.Series[str]",
                self.data()[self.column_name].unique(),  # pyright: ignore [reportUnknownMemberType]
            )
            choices: List[str] = sorted(col_val_unique.tolist())

            ui.update_selectize(
                id=self.filter_id,
                choices=choices,
                selected=None,
            )


class FilterCatNumericSelect(BaseFilter[str]):
    """Creates a selectize filter on a numeric column

    Dealing with numeric categorical data means that we need to do a few things:
    1. convert the selectize values into a numeric
    2. then use the numeric to sort the options

    As a selectize component, we can use the .isin() method to test for values
    """

    def ui(self) -> Tag:
        col_val_unique: pd.Series[str] = self.data()[self.column_name].unique()
        choices: List[str] = pd.to_numeric(col_val_unique).tolist()

        return ui.input_selectize(
            id=self.filter_id,
            label=self.label,
            choices=choices,  # TODO: see temp.py
            multiple=True,
            remove_button=True,
            options={"plugins": ["clear_button"]},
        )

    def matching_rows(self) -> "pd.Index[Any]":
        # pd.to_numeric(None) returns np.float64(nan)
        input_value: pd.Series[str] | None = self._get_input_value()

        # If input_value is None, return all rows
        if input_value is None:
            return None

        input_value: "pd.Index[Any]" = pd.to_numeric(input_value)
        return (
            self.data()
            .loc[self.data()[self.column_name].isin(input_value)]
            .index
        )

    def narrow_options(self, valid_rows: "pd.Index[Any]"):
        input = self.session.input

        col_val_unique: pd.Series[int] = pd.to_numeric(
            self.data().loc[valid_rows, self.column_name].unique()
        )
        choices: List[int] = sorted(col_val_unique.tolist())

        ui.update_selectize(
            id=self.filter_id,
            choices=choices,
            selected=input[self.filter_id](),
        )

    def reset(self) -> None:
        with session_context(self.session):
            col_val_unique: pd.Series[str] = self.data()[
                self.column_name
            ].unique()
            choices: List[int] = pd.to_numeric(col_val_unique).tolist()

            ui.update_selectize(
                id=self.filter_id,
                choices=choices,
                selected=None,
            )


class FilterNumNumericRange(BaseFilter[int]):
    """Creates a range filter on a numeric column

    Dealing with numeric ranges data means that we need to do a few things:
    1. find the start and and of the range
    2. use the .between() method to check for values between the ranges
    3. we are using inclusive = both as a hard-coded default

    As a range component, we can use the .between() method to test for values.

    a range or value slider both use ui.input_slider(), the only difference
    is input slider ranges are given 2 values for the value parameter
    """

    def ui(self) -> Tag:
        col_value: pd.Series[float] = self.data()[self.column_name]
        return ui.input_slider(
            id=self.filter_id,
            label=self.label,
            min=col_value.min(),
            max=col_value.max(),
            value=(col_value.min(), col_value.max()),
        )

    def matching_rows(self) -> "pd.Index[Any]":
        input = self.session.input

        if self.filter_id not in input or not input[self.filter_id]():
            return self.data().index

        input_value: List[float] = input[self.filter_id]()
        input_value_min: float = input_value[0]
        input_value_max: float = input_value[1]
        return (
            self.data()
            .loc[
                self.data()[self.column_name].between(
                    left=input_value_min,
                    right=input_value_max,
                    inclusive="both",
                )
            ]
            .index
        )

    def narrow_options(self, valid_rows: "pd.Index[Any]") -> None:
        # input = self.session.input
        # TODO: type is any numeric
        valid_data: pd.Series[float] = self.data().loc[
            valid_rows, self.column_name
        ]
        valid_min = valid_data.min()
        valid_max = valid_data.max()
        ui.update_slider(
            id=self.filter_id,  # TODO: make sure these are not missing/NAN
            min=valid_min,  # TODO: these 2 lines were the older behavior
            max=valid_max,
            # value=(valid_min, valid_max),
            session=self.session,
        )

    def reset(self) -> None:
        with session_context(self.session):
            col_value: pd.Series[float] = self.data()[self.column_name]
            ui.update_slider(
                id=self.filter_id,
                min=col_value.min(),
                max=col_value.max(),
                value=(col_value.min(), col_value.max()),
            )


class FilterCatStringCheckbox(BaseFilter[str]):
    """Creates a checkbox filter on a categorical string

    This is really similar to the FilterCatStringSelect
    except it returns a checkbox instead of a selectize UI.
    Useful for columns with not as many options to pick from
    """

    def ui(self) -> Tag:
        choices: Dict[str, str] = {
            option.title(): option
            for option in self.data()[self.column_name].unique()
        }

        return ui.input_checkbox_group(
            id=self.filter_id,
            label=self.label,
            choices=choices,
        )

    def matching_rows(self) -> Union["pd.Index[Any]", None]:
        input_value: Iterable[str] | None = self._get_input_value()

        if input_value is None:
            return None

        return return_index(
            self.data().loc[self.data()[self.column_name].isin(input_value)]
        )

    def narrow_options(self, valid_rows: "pd.Index[Any]"):
        input = self.session.input

        choices: Dict[str, str] = {
            option.title(): option
            for option in self.data()
            .loc[valid_rows, self.column_name]
            .unique()  # type: ignore
        }

        ui.update_checkbox_group(
            id=self.filter_id,
            choices=choices,
            selected=input[self.filter_id](),
        )

    def reset(self) -> None:
        with session_context(self.session):
            choices: Dict[str, str] = {
                option.title(): option
                for option in self.data()[self.column_name].unique()
            }
            ui.update_checkbox_group(
                id=self.filter_id,
                choices=choices,
                selected=None,
            )


class FilterCatNumericCheckbox(BaseFilter[str]):
    """Creates a checkbox filter on a categorical numeric value

    This is really similar to the FilterCatStringCheckbox,
    it returns a checkbox, but works when we need to do comparisons
    as if the values are both numeric
    """

    def ui(self) -> Tag:
        choices: Dict[str, str] = {
            str(option): str(option)
            for option in sorted(self.data()[self.column_name].unique())
        }

        return ui.input_checkbox_group(
            id=self.filter_id,
            label=self.label,
            choices=choices,
        )

    def matching_rows(self) -> Union["pd.Index[Any]", None]:
        input_value: Iterable[str] | None = self._get_input_value()

        if input_value is None:
            return None

        input_value: Iterable[float] = [float(x) for x in input_value]

        return return_index(
            self.data().loc[self.data()[self.column_name].isin(input_value)]
        )

    def narrow_options(self, valid_rows: "pd.Index[Any]"):
        input = self.session.input

        choices: Dict[str, str] = {
            str(option): str(option)
            for option in sorted(
                self.data().loc[valid_rows, self.column_name].unique()
            )  # type: ignore
        }

        ui.update_checkbox_group(
            id=self.filter_id,
            choices=choices,
            selected=input[self.filter_id](),
        )

    def reset(self) -> None:
        with session_context(self.session):
            choices: Dict[str, str] = {
                option.title(): option
                for option in self.data()[self.column_name].unique()
            }
            ui.update_checkbox_group(
                id=self.filter_id,
                choices=choices,
                selected=None,
            )
