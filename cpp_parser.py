# C++ Syntax Description

import pyparsing as pp

from cpp_lang import *
from cpp_builders import *
from pp_utils import *

# comments need to be removed
comment = (pp.cStyleComment | pp.cppStyleComment)
preprocessor = pp.lineStart() + pp.Word('#', pp.alphas) + pp.SkipTo( pp.lineEnd() )
preprocessor.setWhitespaceChars(' \r\t')

identifier  = pp.Word( pp.alphas + '_', pp.alphanums + '_' )
persistency = pp.Keyword('static'  ).setParseAction( pp.replaceWith(TypeArgs.STATIC_TYPE)   )
volatility  = pp.Keyword('const'   ).setParseAction( pp.replaceWith(TypeArgs.CONST_TYPE )   ) \
            | pp.Keyword('volatile').setParseAction( pp.replaceWith(TypeArgs.VOLATILE_TYPE) )

reference = pp.Literal('*').setParseAction( pp.replaceWith(CppPointerTypeExpression.POINTER_VAR  ) ) \
          | pp.Literal('&').setParseAction( pp.replaceWith(CppPointerTypeExpression.REFERENCE_VAR) )

# member function on const object
const_function    = pp.Keyword('const'  ).setParseAction( pp.replaceWith(FunctionArgs.CONST_FUNCTION     ) )
virtual_function  = pp.Keyword('virtual').setParseAction( pp.replaceWith(FunctionArgs.VIRTUAL_FUNCTION   ) )
destructor_tag    = pp.Literal('~'      ).setParseAction( pp.replaceWith(FunctionArgs.DESTRUCTOR_FUNCTION) )
abstract_function = (pp.Literal('=') + pp.Literal('0')).setParseAction( pp.replaceWith(FunctionArgs.ABSTRACT_FUNCTION))
inline_function   = pp.Keyword('inline').setParseAction( pp.replaceWith(FunctionArgs.INLINE_FUNCTION) )

hierarchical_type = pp.Keyword('class' ).setParseAction(pp.replaceWith(CppHierarchicalTypeDefinition.CLASS )) \
             | pp.Keyword('struct').setParseAction(pp.replaceWith(CppHierarchicalTypeDefinition.STRUCT)) \
             | pp.Keyword('union' ).setParseAction(pp.replaceWith(CppHierarchicalTypeDefinition.UNION ))
enum_type = pp.Keyword('enum')

int_value = pp.Optional(pp.Literal('+') | pp.Literal('-'))('sign') + pp.Word(pp.nums)('value')
int_value.setParseAction(lambda res: int(res.value) * ((-1) if res.sign == '-' else 1))
long_value = int_value + pp.Literal('L').suppress()

ref = reference + pp.Optional(volatility)

value_expression = pp.Forward()
#value_expression <<= identifier | 

# all type names
#
# type expressions can be recursive due to templates
# TODO: do not suppress struct, union and class keywords
type_expression = pp.Forward()
type_expression <<= (pp.ZeroOrMore(persistency | volatility).setParseAction(
                    lambda tokens: sum(tokens) # collapse all bitmasks into a single one
                )('args') \
                + pp.Group(
                    (pp.Optional(pp.Keyword('unsigned') | pp.Keyword('signed')) \
                        + (pp.Keyword('double') | pp.Keyword('int') | pp.Keyword('float') \
                        |  pp.Keyword('char') | pp.Keyword('unsigned') | pp.Keyword('signed') | pp.Keyword('void'))).setParseAction( lambda tokens: ' '.join(tokens) ) \
                | (pp.Optional(hierarchical_type).suppress() + identifier + pp.ZeroOrMore(pp.Literal('::') + identifier)).setParseAction( lambda tokens: ''.join(tokens) ))('name') \
                + pp.Optional(
                      pp.Literal('<').suppress() \
                    + csl(type_expression + pp.ZeroOrMore(ref), 1) \
                    + pp.Literal('>').suppress()
                )('template')
).setParseAction( build_type_expression )

# declaration: <type> <address-stars> <var-name> <array-brackets>
var_decl = type_expression('type_id') \
     + pp.ZeroOrMore( pp.Group(ref) )('refs') + identifier('name') \
     + pp.ZeroOrMore( get_scope('[',']') ).suppress() \
     + pp.Optional(pp.Literal('=').suppress() + pp.SkipTo(pp.Literal(';')))
var_decl.setParseAction(lambda res: CppVarDeclaration(build_pointer_type_expression(res.type_id[0], res.refs), res.name))

var_decl_list = type_expression('type_id') \
          + csl(
                pp.Group(
                    pp.ZeroOrMore( pp.Group(ref) )('refs') + identifier('name') \
                  + pp.ZeroOrMore( get_scope('[',']') ).suppress() \
                  + pp.Optional(pp.Literal('=') + pp.SkipTo(pp.Literal(',') | pp.Literal(';')))
                )
          )('ids')
var_decl_list.setParseAction( build_declaration_list )

# parameter list: '(' <list of parameter declarations> or 'void' ')'
# important: '+' has precedence over '|' -> brackets after the '(' literals are semantically needed!
parameter_list = pp.Literal('(').suppress() \
               + pp.Optional( csl(var_decl) | pp.Keyword('void').suppress()) \
               + pp.Literal(')').suppress()

#+ type_expression('ret_type') \
#+ pp.Optional(
#    pp.Group(
#        pp.ZeroOrMore( ref )
#    )('refs') + identifier('name')
#) \

fun_decl = pp.ZeroOrMore(virtual_function('virtual') | inline_function('inline')) \
         + (var_decl('decl') | (pp.Optional(destructor_tag('destructor')) + type_expression('constructor'))) \
         + pp.Group(parameter_list)('parameters') \
         + pp.Optional(const_function('const')) \
         + pp.Optional(abstract_function('abstract'))

fun_decl.setParseAction( build_function )

# TODO: quick and dirty hack to catch function calls
fun_call = identifier + get_scope('(', ')')

fun_def = fun_decl('fdecl') \
        + pp.Optional(pp.Literal(':') + fun_call + pp.ZeroOrMore(pp.Literal(',').suppress() + fun_call)) \
        + get_scope('{', '}')
fun_def.setParseAction( build_function_definition )

hierarchical_type_decl = hierarchical_type('struct_type') + identifier('name')
enum_type_decl = enum_type.suppress() + identifier('name')

friend_decl = pp.Keyword('friend') + csl(fun_def | fun_decl | hierarchical_type_decl | identifier)

decl = fun_decl | var_decl_list | friend_decl

visibility = pp.Keyword('private'  ).setParseAction( pp.replaceWith( CppHierarchicalTypeDefinition.VISIBILITY_PRIVATE   ) ) \
           | pp.Keyword('public'   ).setParseAction( pp.replaceWith( CppHierarchicalTypeDefinition.VISIBILITY_PUBLIC    ) ) \
           | pp.Keyword('protected').setParseAction( pp.replaceWith( CppHierarchicalTypeDefinition.VISIBILITY_PROTECTED ) )

visibility_space = pp.Group(visibility + pp.Literal(':').suppress() + pp.ZeroOrMore(fun_def | (decl + pp.Literal(';').suppress()) | (identifier + pp.Literal(';'))))

inheritance = pp.Optional(visibility)('visibility') + identifier('base_class_name')
inheritance.setParseAction(lambda res: CppInheritance(res.base_class_name, res.visibility if len(res) != 0 else CppHierarchicalTypeDefinition.VISIBILITY_DEFAULT))

type_def = pp.Keyword('typedef') + type_expression('expr') + identifier('name')
type_def.setParseAction(lambda res: CppTypeDefinition(res.expr[0], res.name))

hierarchical_type_def   = pp.Forward()
hierarchical_type_def <<= pp.Optional(visibility) + hierarchical_type_decl('decl') + \
              pp.Optional(pp.Group(pp.Literal(':').suppress() + csl(inheritance)))('base_classes') \
            + pp.Literal('{') \
                + pp.Group(pp.ZeroOrMore(fun_def | (decl + pp.Literal(';').suppress())))('default_vis_space') \
                + pp.ZeroOrMore(visibility_space)('vis_spaces') \
            + pp.Literal('}')
hierarchical_type_def.setParseAction(build_hierarchical_type)

