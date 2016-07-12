
# builder functions for the more complex types

from cpp_lang import *

def build_type_expression(tokens):
    name = tokens.name[0]
    args = tokens.args
    templates = [tokens.template[0]] if tokens.template else []

    return CppTypeExpression(name, args, templates)

def build_pointer_type_expression(inner_type, refs_list):

    if not refs_list:
        return inner_type
    el = refs_list.pop(0)

    ref_type = el[0]
    if len(el) > 1:
        ref_vol = el[1]
    else:
        ref_vol = 0

    return build_pointer_type_expression(
        CppPointerTypeExpression(inner_type, ref_type, ref_vol),
        refs_list
    )

def build_declaration_list(res):
    return [
        CppVarDeclaration(
            build_pointer_type_expression( res.type_id[0], elem.refs ),
            elem.name
        ) for elem in res.ids
    ]

def build_function( parse_result ):
    # build args bitmap
    args = 0
    if parse_result.abstract:
        # we need to dereference here, as 'abstract_functions' is a combination of expressions
        # pyparsing is not context free here
        args += parse_result.abstract[0]
    if parse_result.const:
        args += parse_result.const
    if parse_result.constructor:
        args += FunctionArgs.CONSTRUCTOR_FUNCTION
    if parse_result.destructor:
        args += parse_result.destructor
    if parse_result.virtual:
        args += parse_result.virtual
    if parse_result.inline:
        args += parse_result.inline

    if parse_result.constructor:
        tp = parse_result.constructor[0]
    else:
        tp = parse_result.decl.data_type

    if not parse_result.decl:
        parse_result.name = None
    else:
        parse_result.name = parse_result.decl.identifier
    return CppFunctionDeclaration(parse_result.name, tp, parse_result.parameters, args)

def build_function_definition(res):
    return CppFunctionDefinition(res.fdecl)

def build_complex_type(res):
    member_vars = []
    methods = []

    for dec in res.default_vis_space:
        if type(dec) == CppVarDeclaration:
            member_vars.append(CppMember(CppComplexTypeDefinition.VISIBILITY_DEFAULT, dec))
        elif type(dec) == CppFunctionDeclaration or type(dec) == CppFunctionDefinition:
            methods.append(CppMember(CppComplexTypeDefinition.VISIBILITY_DEFAULT, dec))

    for vs in res.vis_spaces:
        visib = vs[0]
        for dec in vs[1:]:
            if type(dec) == CppVarDeclaration:
                member_vars.append(CppMember(dec, visib))
            elif type(dec) == CppFunctionDeclaration or type(dec) == CppFunctionDefinition:
                methods.append(CppMember(dec, visib))


    return CppComplexTypeDefinition(res.decl.struct_type, res.decl.name, base_types=res.base_classes, member_variables=member_vars, member_functions=methods)

