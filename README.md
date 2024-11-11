# candidate-surveys

## Usage

Before using the project, either install it by following instructions in [Installation](#installation) section, or configure a development environment by following instructions in [Development](#development) section.

### Commands

- Output project version

    ```sh
    candidate-surveys version
    ```

- Output PDFs for candidate responses

    ```sh
     candidate-surveys generate-pdfs \
      --responses campaign/responses.csv \
      --config campaign/config.json \
      --logos campaign/logos \
      --output campaign/output

    ```

### Config

| Field                | Description                                                                    | Example Value                                                                             |
|----------------------|--------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| `name`               | The name of the questionnaire campaign.                                        | `"City Election 2000"`                                                                    |
| `subname`            | A subname or subtitle for the questionnaire questionnaire.                     | `"November 5th, 2000 City Election"`                                                      |
| `footer`             | Footer text for the questionnaire questionnaire.                               | `"Questionnaire created by the Coalition of Question Makers"`                             |
| `logo_columns`       | Number of columns for logos.                                                   | `2`                                                                                       |
| `file_structure`     | Fields to use for directory structure                                          | `["County", "Name"]`                                                                      |
| `candidate_details`  | Fields to use at the top of the candidate                                      | `["Name", "County"]`                                                                      |
| `question_overrides` | Override the question text                                                     | `{ "4": "Which office are you running for?" }`                                            |
| `conditional_sections` | Sections that are conditionally included based on the candidate's response.  | `{ "Location:": [ { "value": "North Side", "fields": ["Do you support Polar Bears?"] } }` |
| `ignored_fields`     | Fields to be ignored in the questionnaire.                                     | `["Timestamp", "Email Address", "Location:"]`                                             |
| `pdf_author`         | Author of the PDF.                                                             | `"Coalition of Question Makers"`                                                          |
| `pdf_keyphrases`     | Key phrases to be included in the PDF metadata.                                | `["Name", "2020", "November 5th Election", "City Election Questionnaire"]`                |
| `pdf_creator`        | Creator of the PDF, including contact information.                             | `"Bryan Culbertson (bryan.culbertson@gmail.com)"`                                         |

#### Example Config

```json
{
    "name": "City Election 2000",
    "subname": "November 5th, 2000 City Election",
    "footer": "Questionnaire created by the Coalition of Question Makers",
    "logo_columns": 2,
    "file_structure": ["County", "Name"],
    "candidate_details": ["Name", "County"],
    "question_overrides": {
        "4": "Which office are you running for?"
    },
    "conditional_sections": {
        "Location:": [{ "value": "North Side", "fields": ["Do you support Polar Bears?"] }]
    },
    "ignored_fields": ["Timestamp", "Email Address", "Location:"],
    "pdf_author": "Coalition of Question Makers",
    "pdf_keyphrases": ["November 5th Election", "City Election Questionnaire"],
    "pdf_creator": "Bryan Culbertson (bryan.culbertson@gmail.com)"
}
```

## Installation

If not developing, then no need to clone this repo. You can use [pipx](https://github.com/pypa/pipx) to install the project directly. If you don't have `pipx` then first [install it](https://pypa.github.io/pipx/installation/).

1. Install the project:

    ```sh
    pipx install git+https://github.com/bryanculbertson/candidate-surveys
    ```

1. Test your installation!

    ```sh
    candidate-surveys --help
    ```

## Development

If developing, then clone this repo, setup a development environment, and run the project from there.

### Setup System Environment

This project uses [pyenv](https://github.com/pyenv/pyenv) and [poetry](https://github.com/python-poetry/poetry) to manage python virtual environment and dependencies. If you have a working `python` system with those tools installed then you can skip system environment setup and go straight to [Setup Project Environment](#setup-project-environment).

If you know what you are doing, then you can skip using `pyenv` as long as you have the version of python installed that is specified in `.python-version`.

#### VSCode Devcontainer/Github Codespace

1. Create a Codespace or open in VS Code locally

    Follow Github instructions to [Create a Codespace](https://docs.github.com/en/codespaces/developing-in-codespaces/creating-a-codespace) for this project, or VS Code instructions to [open repo in container](https://code.visualstudio.com/docs/remote/containers-tutorial)

1. Choose the local `.venv` python if given a choice.

#### Ubuntu/Debian

You can run the following setup steps with:

```sh
./scripts/setup-ubuntu.sh
```

1. Install python build dependencies:

    ```sh
    sudo apt-get update
    sudo apt-get -y install --no-install-recommends \
        bash \
        build-essential \
        curl \
        expat \
        fontconfig \
        gcc \
        git \
        libbz2-dev \
        libffi-dev \
        liblzma-dev \
        libmpfr-dev \
        libncurses-dev \
        libpq-dev \
        libreadline-dev \
        libsqlite3-dev \
        libssl-dev \
        libxml2-dev \
        libxmlsec1-dev \
        llvm \
        locales \
        make \
        openssl \
        pipx \
        python2-dev \
        python3-dev \
        python3-pip \
        sudo \
        tk-dev \
        unzip \
        vim \
        wget \
        wget \
        xz-utils \
        zip \
        zlib1g \
        zlib1g-dev
    ```

1. Install project dependencies:

    ```sh
    sudo apt-get update
    sudo apt-get -y install --no-install-recommends \
        shellcheck
    ```

1. Install [pyenv](https://github.com/pyenv/pyenv) (if you haven't already):

    ```sh
    PYENV_GIT_TAG=v2.4.17 curl https://pyenv.run | bash
    ```

    Add `pyenv` paths for `bash`:

    ```sh
    {
        echo ''
        echo 'export PYENV_ROOT="$HOME/.pyenv"'
        echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"'
        echo 'eval "$(pyenv init -)"'
        echo 'eval "$(pyenv virtualenv-init -)"'
    } >> ~/.bashrc
    ```

    Refresh current shell with updated paths:

    ```sh
    source ~/.bashrc
    ```

    Check `pyenv` was installed correctly by verifying `python` points to `~/.pyenv/shims/python`:

    ```sh
    which python
    ```

    If you have an issue, see pyenv's [instructions](https://github.com/pyenv/pyenv#basic-github-checkout).

1. Install project python version specified in `.python-version`:

    ```sh
    pyenv install
    ```

    Check correct `python`  version was installed by verifying it matches `.python-version`:

    ```sh
    python --version
    cat .python-version
    ```

1. Install [poetry](https://github.com/python-poetry/poetry) (if you haven't already):

    ```sh
    pipx install poetry==1.8.4
    ```

#### Mac

1. Install homebrew (if you haven't already):

    ```sh
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    ```

1. Install python build dependencies:

    ```sh
    brew install openssl readline sqlite3 xz zlib
    ```

1. Install project dependencies:

    ```sh
    brew install shellcheck
    ```

1. Install [pyenv](https://github.com/pyenv/pyenv) (if you haven't already):

    ```sh
    brew install pyenv
    ```

    Add `pyenv` path for `zsh` (or `~/.bashrc` if using `bash`):

    ```sh
    {
        echo ''
        echo 'export PYENV_ROOT="$HOME/.pyenv"'
        echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"'
        echo 'eval "$(pyenv init -)"'
        echo 'eval "$(pyenv virtualenv-init -)"'
    } >> ~/.zshrc
    ```

    Refresh current shell with updated paths:

    ```sh
    source ~/.zshrc
    ```

    Check `pyenv` was installed correctly by verifying `python` points to `~/.pyenv/shims/python`:

    ```sh
    which python
    ```

    If you have an issue, see pyenv's [instructions](https://github.com/pyenv/pyenv#basic-github-checkout).

1. Install project python version specified in `.python-version`:

    ```sh
    pyenv install
    ```

    Check correct `python`  version was installed by verifying it matches `.python-version`:

    ```sh
    python --version
    cat .python-version
    ```

1. Install [poetry](https://github.com/python-poetry/poetry) (if you haven't already):

    ```sh
    pipx install poetry==1.8.4
    ```

### Setup Project Environment

After setting up system environment with `pyenv` and `poetry`, then you can install the project and its depedancies.

1. Install project python version specified in `.python-version`:

    ```sh
    pyenv install
    ```

    Check correct `python`  version was installed by verifying it matches `.python-version`:

    ```sh
    python --version
    cat .python-version
    ```

1. Install project and dependancies into local poetry managed `.venv`:

    ```sh
    poetry install
    ```

1. Test your installation!

    ```sh
    poetry run candidate-surveys --help
    ```

    *or*

    ```sh
    poetry shell
    candidate-surveys --help
    ```

### Testing

After setting up system and project environments you can run tests, formatting, linting, etc. with [tox](https://github.com/tox-dev/tox).

`tox` is installed and managed within the local venv so either activate the `venv` with `poetry shell`, or prefix each command with `poetry run`.

1. Run tests and linting

    ```sh
    poetry run tox
    ```

1. Run tests

    ```sh
    poetry run tox -qe test
    ```

1. Run linting

    ```sh
    poetry run tox -qe lint
    ```

1. Enable pre-commit hooks:

    ```sh
    poetry run tox -e install-hooks
    ```
