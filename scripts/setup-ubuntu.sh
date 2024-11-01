#!/usr/bin/env bash

# exit when a command fails instead of blindly blundering forward
set -e
# treat unset variables as an error and exit immediately
set -u
# don't hide exit codes when pipeline output to another command
set -o pipefail

echo "Installing system dependencies"
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
    zlib1g-dev \
    zsh

echo "Installing project dependencies"
sudo apt-get -y install --no-install-recommends \
    shellcheck

if ! command -v pyenv &> /dev/null; then
    echo "Installing pyenv"
    PYENV_GIT_TAG=v2.4.17 curl https://pyenv.run | bash

    # shellcheck disable=SC2016
    {
        echo ''
        echo 'export PYENV_ROOT="$HOME/.pyenv"'
        echo 'export PATH="$PYENV_ROOT/bin:$PATH"'
        echo 'eval "$(pyenv init -)"'
        echo 'eval "$(pyenv virtualenv-init -)"'
    } >> ~/.bashrc

    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
    eval "$(pyenv virtualenv-init -)"
fi

echo "Installing project python version"
"$PYENV_ROOT"/bin/pyenv install --skip-existing

if ! command -v pyenv &> /dev/null; then
    echo "Installing poetry"
    pipx ensurepath
    pipx install poetry==1.8.4
fi

echo "Installing python dependencies using Poetry into local venv"
"$HOME"/.local/bin/poetry install

echo "Enabling pre-commit hooks"
"$HOME"/.local/bin/poetry run tox -e install-hooks

echo "Install done."
