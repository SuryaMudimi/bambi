from typing import Sequence

import ast
import textwrap

from formulae.terms.call import Call

from bambi.transformations import HSGP


def listify(obj):
    """Wrap all non-list or tuple objects in a list.

    Provides a simple way to accept flexible arguments.
    """
    if obj is None:
        return []
    else:
        return obj if isinstance(obj, (list, tuple, type(None))) else [obj]


def indentify(string: str, n: int = 2) -> str:
    """Add spaces to the beginning of each line in a multi-line string."""
    space = n * " "
    return space + space.join(string.splitlines(True))


def multilinify(sequence: Sequence[str], sep: str = ",") -> str:
    """Make a multi-line string out of a sequence of strings."""
    sep += "\n"
    return "\n" + sep.join(sequence)


def wrapify(string, width=100, indentation=2):
    lines = string.splitlines(True)
    wrapper = textwrap.TextWrapper(width=width)
    for idx, line in enumerate(lines):
        if len(line) > width:
            leading_spaces = len(line) - len(line.lstrip(" "))
            wrapper.subsequent_indent = " " * (leading_spaces + indentation)
            wrapped = wrapper.wrap(line)
            lines[idx] = "\n".join(wrapped) + "\n"
    return "".join(lines)


def extract_argument_names(expr, accepted_funcs):
    """Extract the names of the arguments passed to a function.

    This is used to extract the labels from function calls such as `c(y1, y2, y3, y3)`.

    Parameters
    ----------
    expr : str
        An expression that is parsed to extract the components of the call.
    accepted_funcs : list
        A list with the names of the functions that we accept to parse.

    Returns
    -------
    list
        If all criteria are met, the names of the arguments. Otherwise it returns None.
    """
    # Extract the first thing in the body
    parsed_expr = ast.parse(expr).body[0]
    if not isinstance(parsed_expr, ast.Expr):
        return None

    # Check the value is a call
    value = parsed_expr.value
    if not isinstance(value, ast.Call):
        return None

    # Check call name is the name of an exepcted function
    if value.func.id not in accepted_funcs:
        return None

    # Check all arguments are either names or constants
    args = value.args
    if not all(isinstance(arg, ast.Name) for arg in args):
        return None

    # We can safely build labels now
    labels = [arg.id for arg in args]

    if labels:
        return labels
    return None


def clean_formula_lhs(x):
    """Remove the left hand side of a model formula and the tilde.

    Parameters
    ----------
    x : str
        A model formula that has '~' in it.

    Returns
    -------
    str
        The right hand side of the model formula
    """
    assert "~" in x
    position = x.find("~")
    return x[position + 1 :]


def get_auxiliary_parameters(family):
    """Get names of auxiliary parameters

    Obtains the difference between all the parameters and the parent parameter of a family.
    These parameters are known as auxiliary or nuisance parameters.

    Parameters
    ----------
    family : bambi.families.Family
        The family

    Returns
    -------
    set
        Names of auxiliary parameters in the family
    """
    return set(family.likelihood.params) - {family.likelihood.parent}


def get_aliased_name(term):
    """Get the aliased name of a model term

    Model terms have a name and, optionally, an alias. The alias is used as the "name" if it's
    available. This is a helper that returns the right "name".

    Parameters
    ----------
    term : BaseTerm
        The term

    Returns
    -------
    str
        The aliased name
    """
    if term.alias:
        return term.alias
    return term.name


def is_single_component(term):
    return hasattr(term, "components") and len(term.components) == 1


def is_call_component(component):
    return isinstance(component, Call)


def has_stateful_transform(component):
    return component.call.stateful_transform is not None


def is_hsgp_term(term):
    if not is_single_component(term):
        return False
    component = term.components[0]
    if not is_call_component(component):
        return False
    if not has_stateful_transform(component):
        return False
    return isinstance(component.call.stateful_transform, HSGP)
