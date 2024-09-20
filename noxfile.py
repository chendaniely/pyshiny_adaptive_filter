import nox

# For this to run you will need to have python3.9, python3.10 and python3.11 installed on your computer. Otherwise nox will skip running tests for whatever versions are missing


@nox.session(python=["3.9", "3.10", "3.11", "3.12"])
def test(session):
    # install
    session.install(".[tests]")

    # Run tests
    session.run("pytest")
