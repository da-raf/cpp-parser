# printing C++ code
# (conversion of the data-structures back to code)

from cpp_lang import *

class CppPrinter:

    def declaration_str(self, declaration):
        return self.type_expr_str(declaration.data_type) + ' ' + self.identifier_str(declaration.identifier)

    def constructor_str(self, constructor):
        c = constructor
        return self.type_expr_str(c.name) + ' ' + self.parameter_list_str(c.params)

    def function_decl_str(self, function_decl):
        #print('Debug: ' + str(function_decl))
        res = []

        if function_decl.isInline():
            res.append('inline')
        if function_decl.isVirtual():
            res.append('virtual')

        rts = self.type_expr_str(function_decl.return_type)
        res.append( rts if not function_decl.isDestructor() else ('~' + rts) )

        if function_decl.name is not None:
            res.append(function_decl.name)

        res.append(self.parameter_list_str(function_decl.params))

        if function_decl.isConstant():
            res.append('const')

        if function_decl.isAbstract():
            res.append('= 0')

        return ' '.join(res)

    def identifier_str(self, identifier):
        return identifier

    def inheritance_str(self, inheritance):
        vs = self.visibility_str(inheritance.vis)
        return (vs + ' ' if vs else '') + inheritance.base_id

    def parameter_list_str(self, pl):
        return '(' + ', '.join(map(self.declaration_str, pl)) + ')'

    def type_expr_str(self, type_id):
        if type(type_id) == CppPointerTypeExpression:
            ref_str = '*' if type_id.ref_type == CppPointerTypeExpression.POINTER_VAR   else \
                      '&' if type_id.ref_type == CppPointerTypeExpression.REFERENCE_VAR else \
                      ''
            it = type_id.inner_type
            return self.type_expr_str(it) + (' ' if type(it) != CppPointerTypeExpression else '') + ref_str \
                 + self.volatility_str(type_id.ref_volatility)
        elif type(type_id) == CppTypeExpression:
            #print('DEBUG: %s - %s' % (type_id.type_name, str(type_id.template_args)))
            res = []
            if type_id.type_args & TypeArgs.STATIC_TYPE:
                res.append('static')
            if type_id.type_args & TypeArgs.CONST_TYPE:
                res.append('const')
            if type_id.type_args & TypeArgs.VOLATILE_TYPE:
                res.append('volatile')

            # format template args
            template_str = ''
            if type_id.template_args:
                template_str = '<' + ', '.join(map(self.type_expr_str, type_id.template_args)) + '>'

            res.append(type_id.type_name + template_str)

            return ' '.join(res)
        else:
            raise ValueError(str(type(type_id)) + ' is not a c++ type object!')

    def typedef_str(self, typedef):
        return 'typedef' + ' ' + self.type_expr_str(typedef.type_expr) + ' ' + typedef.type_name

    def visibility_str(self, visibility):
        return 'private'   if visibility == CppHierarchicalTypeDefinition.VISIBILITY_PRIVATE   else \
               'public'    if visibility == CppHierarchicalTypeDefinition.VISIBILITY_PUBLIC    else \
               'protected' if visibility == CppHierarchicalTypeDefinition.VISIBILITY_PROTECTED else \
               ''

    def volatility_str(self, volatility):
        return 'const'    if volatility == TypeArgs.CONST_TYPE    else \
               'volatile' if volatility == TypeArgs.VOLATILE_TYPE else \
               ''

    def hierarchical_type_prefix_str(self, hierarchical_type_prefix):
        return 'struct' if hierarchical_type_prefix == CppHierarchicalTypeDefinition.STRUCT else \
               'class'  if hierarchical_type_prefix == CppHierarchicalTypeDefinition.CLASS  else \
               'union'  if hierarchical_type_prefix == CppHierarchicalTypeDefinition.UNION  else \
               ''

    def hierarchical_type_str(self, hierarchical_type):
        prefix_str = self.hierarchical_type_prefix_str(hierarchical_type.hierarchical_type)
        name_str = hierarchical_type.name
        
        if hierarchical_type.base_types:
            inherits = [self.inheritance_str(i) for i in hierarchical_type.base_types[0]]
        else:
            inherits = []

        default_vars   = ['\t' + self.declaration_str(m.member_decl) + ';' for m in hierarchical_type.member_variables if m.vis == CppHierarchicalTypeDefinition.VISIBILITY_DEFAULT]
        public_vars    = ['\t' + self.declaration_str(m.member_decl) + ';' for m in hierarchical_type.member_variables if m.vis == CppHierarchicalTypeDefinition.VISIBILITY_PUBLIC]
        protected_vars = ['\t' + self.declaration_str(m.member_decl) + ';' for m in hierarchical_type.member_variables if m.vis == CppHierarchicalTypeDefinition.VISIBILITY_PROTECTED]
        private_vars   = ['\t' + self.declaration_str(m.member_decl) + ';' for m in hierarchical_type.member_variables if m.vis == CppHierarchicalTypeDefinition.VISIBILITY_PRIVATE]

        default_meths   = ['\t' + self.function_decl_str(m.member_decl) + ';' for m in hierarchical_type.member_functions if m.vis == CppHierarchicalTypeDefinition.VISIBILITY_DEFAULT]
        public_meths    = ['\t' + self.function_decl_str(m.member_decl) + ';' for m in hierarchical_type.member_functions if m.vis == CppHierarchicalTypeDefinition.VISIBILITY_PUBLIC]
        protected_meths = ['\t' + self.function_decl_str(m.member_decl) + ';' for m in hierarchical_type.member_functions if m.vis == CppHierarchicalTypeDefinition.VISIBILITY_PROTECTED]
        private_meths   = ['\t' + self.function_decl_str(m.member_decl) + ';' for m in hierarchical_type.member_functions if m.vis == CppHierarchicalTypeDefinition.VISIBILITY_PRIVATE]

        defaults   = default_vars   + default_meths
        publics    = public_vars    + public_meths
        protecteds = protected_vars + protected_meths
        privates   = private_vars   + private_meths

        return prefix_str + ' ' + name_str + ' ' + \
                (': ' + ', '.join(inherits) + ' ' if inherits else '') + \
                '{' + \
                ('\n'             + '\n'.join(defaults)   if defaults   else '') + \
                ('\npublic:\n'    + '\n'.join(publics)    if publics    else '') + \
                ('\nprotected:\n' + '\n'.join(protecteds) if protecteds else '') + \
                ('\nprivate:\n'   + '\n'.join(privates)   if privates   else '') + \
                '\n}'

