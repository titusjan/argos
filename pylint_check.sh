#! /bin/bash

# Performs pylint check on the given files. If no files are given it will search in the project for all relevant source files.

if [[ -z "$*" ]] ; then
    input_files=$(find . -type f \( -iname "*.py" ! -iname "__init__.py" ! -iname "setup.py" ! -iname "conf.py" ! -wholename "./tests/*" \) )
else
    input_files="$*"
fi

#echo ${input_files}
pylint-3.4 --rcfile=.pylintrc '--msg-template={path}:{line}: [{msg_id} ({symbol}), {obj}] {msg}' ${input_files}

