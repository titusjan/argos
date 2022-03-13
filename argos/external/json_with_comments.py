"""This module provides functions to parse JSON-with-comments.

Standard JSON is a human-readable data interchange format that is popular due to its simplicity
and wide support across programming languages. Unfortunately, it does not support comments,
making it less suitable for some applications like configuration files.

This module implements several functions that add support for comments to JSON, resulting in a
JSON dialect that we refer to as "JSON-with-comments"; elsewhere, this format has been referred
to as "jsonc".

Two types of comments are supported, mirroring the two types of comments available in the
JavaScript language from which JSON originates:

* Line comments start with "//" and continue to the next newline character;
* Block comments start with "/*" and end with the next "*/".

The core functionality of this module is provided by the erase_json_comments() function. It
takes an input string argument, replaces comments with whitespace, and returns an output string
that is 'pure' JSON. Inside comments, carriage returns and newlines are passed through as-is;
all other characters are replaced by spaces. This preserves the structure of the original input,
allowing a subsequently run JSON parser to report any issues in the output with line numbers and
column offsets that correspond to the original JSON-with-comments input.

Two convenience functions are provided that run erase_json_comments() on input, then pass the
resulting 'purified' JSON-string to the JSON parser that is provided by the 'json' module in the
Python standard library. For most programs, one of these two functions will provide the easiest
way to use JSON-with-comments:

* parse_json_with_comments_string() parses JSON-with comments from a string;
* parse_json_with_comments_file() parses JSON-with comments from a file.
"""

import json
from enum import Enum


class JSONWithCommentsError(ValueError):
    """An error occurred while scanning JSON-with-comments."""


class FsmState(Enum):
    """Finite State Machine states for scanning JSON-with-comments."""
    DEFAULT            = 1  # default state ; not scanning a string or comment.
    COMMENT_INTRO      = 2  # accepted '/'  ; the start of a line or block comment.
    LINE_COMMENT       = 3  # accepted '//' ; scanning a line comment.
    BLOCK_COMMENT      = 4  # accepted '/*' ; scanning a block comment.
    BLOCK_COMMENT_STAR = 5  # accepted '/*' ; scanning a block comment, and just scanned a '*'.
    STRING             = 6  # accepted '"'  ; scanning a string.
    STRING_BACKSLASH   = 7  # accepted '"'  ; scanning a string, and just scanned a backslash.


class FsmAction(Enum):
    """Finite State Machine actions for scanning JSON-with-comments."""
    EMIT_NOTHING             = 1  # emit nothing
    EMIT_CURRENT             = 2  # emit the current character
    EMIT_FSLASH_THEN_CURRENT = 3  # emit forward slash followed by current character
    EMIT_ONE_SPACE           = 4  # emit one space character
    EMIT_TWO_SPACES          = 5  # emit two space characters


class CharacterClass(Enum):
    """Character classes to be distinguished while scanning JSON-with-comments."""
    FSLASH = 1  # forward slash
    BSLASH = 2  # back slash
    QUOTE  = 3  # string quote
    CR     = 4  # carriage return
    NL     = 5  # newline
    STAR   = 6  # star (asterisk)
    OTHER  = 7  # any other character


# Define the transition table of (state, character_class) -> (action, next_state).
#
# Note that not all possible combinations of (state, character_class) are explicitly specified.
# If a (state, character_class) combination is encountered while scanning that is not present
# in the transition table, the key (state, CharacterClass.OTHER) key will be used instead.
#
# This makes the transition table both smaller (only 22 out of 49 entries need to be specified)
# and easier to understand.

_fsm_definition = {

    ( FsmState.DEFAULT            , CharacterClass.FSLASH ) : ( FsmAction.EMIT_NOTHING             , FsmState.COMMENT_INTRO      ),
    ( FsmState.DEFAULT            , CharacterClass.QUOTE  ) : ( FsmAction.EMIT_CURRENT             , FsmState.STRING             ),
    ( FsmState.DEFAULT            , CharacterClass.OTHER  ) : ( FsmAction.EMIT_CURRENT             , FsmState.DEFAULT            ),

    ( FsmState.COMMENT_INTRO      , CharacterClass.FSLASH ) : ( FsmAction.EMIT_TWO_SPACES          , FsmState.LINE_COMMENT       ),
    ( FsmState.COMMENT_INTRO      , CharacterClass.STAR   ) : ( FsmAction.EMIT_TWO_SPACES          , FsmState.BLOCK_COMMENT      ),
    ( FsmState.COMMENT_INTRO      , CharacterClass.OTHER  ) : ( FsmAction.EMIT_FSLASH_THEN_CURRENT , FsmState.DEFAULT            ),

    ( FsmState.LINE_COMMENT       , CharacterClass.CR     ) : ( FsmAction.EMIT_CURRENT             , FsmState.LINE_COMMENT       ),
    ( FsmState.LINE_COMMENT       , CharacterClass.NL     ) : ( FsmAction.EMIT_CURRENT             , FsmState.DEFAULT            ),
    ( FsmState.LINE_COMMENT       , CharacterClass.OTHER  ) : ( FsmAction.EMIT_ONE_SPACE           , FsmState.LINE_COMMENT       ),

    ( FsmState.BLOCK_COMMENT      , CharacterClass.CR     ) : ( FsmAction.EMIT_CURRENT             , FsmState.BLOCK_COMMENT      ),
    ( FsmState.BLOCK_COMMENT      , CharacterClass.NL     ) : ( FsmAction.EMIT_CURRENT             , FsmState.BLOCK_COMMENT      ),
    ( FsmState.BLOCK_COMMENT      , CharacterClass.STAR   ) : ( FsmAction.EMIT_ONE_SPACE           , FsmState.BLOCK_COMMENT_STAR ),
    ( FsmState.BLOCK_COMMENT      , CharacterClass.OTHER  ) : ( FsmAction.EMIT_ONE_SPACE           , FsmState.BLOCK_COMMENT      ),

    ( FsmState.BLOCK_COMMENT_STAR , CharacterClass.FSLASH ) : ( FsmAction.EMIT_ONE_SPACE           , FsmState.DEFAULT            ),
    ( FsmState.BLOCK_COMMENT_STAR , CharacterClass.CR     ) : ( FsmAction.EMIT_CURRENT             , FsmState.BLOCK_COMMENT      ),
    ( FsmState.BLOCK_COMMENT_STAR , CharacterClass.NL     ) : ( FsmAction.EMIT_CURRENT             , FsmState.BLOCK_COMMENT      ),
    ( FsmState.BLOCK_COMMENT_STAR , CharacterClass.STAR   ) : ( FsmAction.EMIT_ONE_SPACE           , FsmState.BLOCK_COMMENT_STAR ),
    ( FsmState.BLOCK_COMMENT_STAR , CharacterClass.OTHER  ) : ( FsmAction.EMIT_ONE_SPACE           , FsmState.BLOCK_COMMENT      ),

    ( FsmState.STRING             , CharacterClass.BSLASH ) : ( FsmAction.EMIT_CURRENT             , FsmState.STRING_BACKSLASH   ),
    ( FsmState.STRING             , CharacterClass.QUOTE  ) : ( FsmAction.EMIT_CURRENT             , FsmState.DEFAULT            ),
    ( FsmState.STRING             , CharacterClass.OTHER  ) : ( FsmAction.EMIT_CURRENT             , FsmState.STRING             ),

    ( FsmState.STRING_BACKSLASH   , CharacterClass.OTHER  ) : ( FsmAction.EMIT_CURRENT             , FsmState.STRING             )
}

# Characters are classified according to this table.
# All characters that are not explicitly specified belong to CharacterClass.OTHER.

_character_classifications = {
    '/'  : CharacterClass.FSLASH,
    '\\' : CharacterClass.BSLASH,
    '\"' : CharacterClass.QUOTE,
    '\r' : CharacterClass.CR,
    '\n' : CharacterClass.NL,
    '*'  : CharacterClass.STAR
}


def erase_json_comments(input_string: str) -> str:
    """Erase the comments in a JSON-with-comments string and return valid JSON.

    All characters in a comment are replaced by spaces, except that carriage return and newline
    characters are passed through.

    This ensures that the structure of the output is identical to the structure of the input,
    allowing a subsequently run JSON parser to report any issues with meaningful line numbers
    and column offsets.
    """

    output = []

    state = FsmState.DEFAULT

    for current_character in input_string:

        character_class = _character_classifications.get(current_character, CharacterClass.OTHER)

        # If a (state, character_class) tuple is not explicitly handled in the FSM definition,
        # the behavior of CharacterClass.OTHER will be used.

        if (state, character_class) not in _fsm_definition:
            character_class = CharacterClass.OTHER

        # Look up action and next state.

        (action, next_state) = _fsm_definition[(state, character_class)]

        # Perform the specified action.

        if action in (FsmAction.EMIT_CURRENT, FsmAction.EMIT_FSLASH_THEN_CURRENT):
            if action == FsmAction.EMIT_FSLASH_THEN_CURRENT:
                output.append("/")
            output.append(current_character)
        elif action in (FsmAction.EMIT_ONE_SPACE, FsmAction.EMIT_TWO_SPACES):
            if action == FsmAction.EMIT_TWO_SPACES:
                output.append(" ")
            output.append(" ")

        # Proceed to the next state.

        state = next_state

    # We're at the end of the character scan loop.

    # The usual end state for a successful scan will be DEFAULT. We also permit LINE_COMMENT,
    # meaning that line comments that are not terminated by a newline are acceptable.
    #
    # If we find ourselves in one of the five other states at the end of the scan, something is
    # wrong.
    #
    # If we're in either the STRING or STRING_BACKSLASH state, the input ended while scanning a
    # string, and this will also be true in the output we produce. A JSON parser that consumes
    # our output will detect this error, so no action is needed here to handle this case.
    #
    # The three remaining erroneous states do require action from our side:

    if state == FsmState.COMMENT_INTRO:
        # If we're in the COMMENT_INTRO state, the input ended in a forward slash. This forward
        # slash was not yet emitted when we entered the COMMENT_INTRO state, so we emit it now.
        # Since no valid JSON file can end with a forward slash, this slash will be caught when
        # a JSON parser processes our output, causing a parsing error.
        output.append("/")
    elif state in (FsmState.BLOCK_COMMENT, FsmState.BLOCK_COMMENT_STAR):
        # If we're in either the BLOCK_COMMENT or BLOCK_COMMENT_STAR state, the input ended while
        # scanning an unterminated block comment. This issue would not be noticed by a JSON parser
        # that processes our output, as our output will just end with the spaces that replaced the
        # partial block comment. So for both these end states, we will raise an exception here.
        raise JSONWithCommentsError("Unterminated block comment.")

    # Concatenate the output characters and return the result.

    output_string = "".join(output)

    return output_string


def parse_json_with_comments_string(json_with_comments: str, **kw):
    """Parse a JSON-with-comments string by erasing comments and parsing the result as JSON.

    Any keyword arguments are passed on to the json.loads() function that is used to parse
    the input string from which the comments have been erased.
    """
    json_without_comments = erase_json_comments(json_with_comments)
    try:
        return json.loads(json_without_comments, **kw)
    except json.JSONDecodeError as json_exception:
        # Wrap the JSONDecodeError in a JSONWithCommentsError exception.
        raise JSONWithCommentsError("Invalid JSON after erasing comments.") from json_exception


def parse_json_with_comments_file(filename: str, **kw):
    """Parse a JSON-with-comments file by erasing comments and parsing the result as JSON.

    Any keyword arguments are passed on to the json.loads() function that is used to parse
    the input string as read from the file from which the comments have been erased.
    """
    with open(filename, "r") as input_file:
        json_with_comments = input_file.read()
    return parse_json_with_comments_string(json_with_comments, **kw)
