#! /bin/bash
export PYTHONPATH=$PYTHONPATH:./tools:./ocal/lib/examples
find . -type f \( -iname "*.py" ! -iname "__init__.py" ! -iname "setup.py" ! -iname "conf.py" ! -wholename "./tests/*" \) | xargs pylint-3.4 --rcfile=.pylintrc '--msg-template={path}:{line}: [{msg_id} ({symbol}), {obj}] {msg}' $* | tee pylint.out

