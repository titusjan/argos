#! /bin/bash
export PYTHONPATH=$PYTHONPATH:./tools:./ocal/lib/examples
find . -type f \( -iname "*.py" ! -iname "__init__.py" ! -iname "conf.py"  \) | xargs pylint --rcfile=.pylintrc '--msg-template={path}:{line}: [{msg_id}({symbol}), {obj}] {msg}' -f parseable $* | tee pylint.out

