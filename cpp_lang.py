# datastructures for C++ syntax

import pyparsing as pp

class TypeArgs:
    CONST_TYPE = 1
    VOLATILE_TYPE = 2
    STATIC_TYPE = 4

class CppComplexTypeDefinition:
    DEFAULT = 0
    CLASS   = 1
    STRUCT  = 2
    UNION   = 3

    VISIBILITY_DEFAULT = 0
    VISIBILITY_PRIVATE = 1
    VISIBILITY_PROTECTED = 2
    VISIBILITY_PUBLIC = 3

    def __init__(self, complex_type, name, base_types=[], member_variables=[], member_functions=[]):
        self.complex_type = complex_type
        self.name = name
        self.base_types = base_types
        self.member_variables = member_variables
        self.member_functions = member_functions


class FunctionArgs:
    CONST_FUNCTION = 1
    VIRTUAL_FUNCTION = 2
    CONSTRUCTOR_FUNCTION = 4
    DESTRUCTOR_FUNCTION = 8
    ABSTRACT_FUNCTION = 16
    INLINE_FUNCTION = 32

class CppTypeExpression:
    def __init__(self, type_name, type_args=0, template_args=[], refs=[]):
        self.type_args = type_args
        self.type_name = type_name
        # if this type is a template type, this will contain the template argument values
        self.template_args = template_args

    def content_name(self):
        return self.type_name

class CppPointerTypeExpression:
    POINTER_VAR   = 1
    REFERENCE_VAR = 2

    def __init__(self, inner_type, ref_type, ref_volatility):
        self.inner_type = inner_type
        self.ref_type = ref_type
        self.ref_volatility = ref_volatility

    def content_name(self):
        return self.inner_type.content_name()

class CppTypeDefinition:
    def __init__(self, type_expr, type_name):
        self.type_expr = type_expr
        self.type_name = type_name

class CppVarDeclaration:
    def __init__(self, data_type, identifier):
        self.data_type = data_type
        self.identifier = identifier

class CppInheritance:
    def __init__(self, base_class_id, visibility=0):
        self.vis = visibility
        self.base_id = base_class_id

class CppMember:
    def __init__(self, member_decl, visibility=CppComplexTypeDefinition.VISIBILITY_DEFAULT):
        self.member_decl = member_decl
        self.vis = visibility

class CppFunctionDeclaration:
    def __init__(self, name, return_type, params, args):
        self.name = name
        self.return_type = return_type
        self.params = params
        self.args = args

    def isAbstract(self):
        return bool(self.args & FunctionArgs.ABSTRACT_FUNCTION)

    def isConstant(self):
        return bool(self.args & FunctionArgs.CONST_FUNCTION)

    def isConstructor(self):
        return bool(self.args & FunctionArgs.CONSTRUCTOR_FUNCTION)

    def isDestructor(self):
        return bool(self.args & FunctionArgs.DESTRUCTOR_FUNCTION)

    def isInline(self):
        return bool(self.args & FunctionArgs.INLINE_FUNCTION)

    def isVirtual(self):
        return bool(self.args & FunctionArgs.VIRTUAL_FUNCTION)

class CppFunctionDefinition(CppFunctionDeclaration):
    def __init__(self, decl):
        CppFunctionDeclaration.__init__(self, decl.name, decl.return_type, decl.params, decl.args)

class CppClass:
    def __init__(self, name, fields=[], member_functions=[], inheritances=[]):
        self.name = name
        self.fields = fields
        self.member_functions = member_functions
        self.inheritances = inheritances

