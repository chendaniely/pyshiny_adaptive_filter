from shiny.playwright import controller
from shiny.run import ShinyAppProc
from playwright.sync_api import Page
from shiny.pytest import create_app_fixture

app = create_app_fixture("app.py")


def test_basic_app(page: Page, app: ShinyAppProc):
    page.goto(app.url)

    day = controller.InputCheckboxGroup(page, "adaptive-filter_day")
    time = controller.InputCheckboxGroup(page, "adaptive-filter_time")

    day.expect_choice_labels(["Sun", "Fri"])
    day.expect_choices(["Sun", "Fri"])
    day.expect_selected([])
    day.set(["Fri"])
    time.expect_choices(["Dinner"])
