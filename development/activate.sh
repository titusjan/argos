# Adds the parent argos directory to beginning of the PYTHONPATH so that the tests can be executed
# and the current directory to the PATH so that the argos.py script can be found from everywhere.


CURRENT_DIR="$(dirname "${BASH_SOURCE[0]}")"

SRC_DIR=$(realpath $CURRENT_DIR/..)

echo ${SRC_DIR}

export PATH="${CURRENT_DIR}:$PATH"
export PYTHONPATH="${SRC_DIR}:$PYTHONPATH"
