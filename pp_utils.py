import pyparsing as pp

# match unparsed scopes
def get_scope(start, end):
    scope = pp.Forward()
    scope <<= pp.Literal(start) \
            + pp.ZeroOrMore(pp.Word(pp.printables.replace(start,'').replace(end,'')) | scope) \
            + pp.Literal(end)
    return scope

def get_separated_list(sep, expr, min_len=0):
    if min_len == 0:
        return pp.Optional(expr + pp.ZeroOrMore(sep + expr))
    elif min_len == 1:
        return expr + pp.ZeroOrMore(sep + expr)
    else:
        return expr + (sep + expr) * (min_len-1) + pp.ZeroOrMore(sep + expr)

def csl(expr, min_len=0):
    return get_separated_list(pp.Literal(',').suppress(), expr, min_len=min_len)
