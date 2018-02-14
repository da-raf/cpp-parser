import sys; sys.path.append('..')

import os.path

import cpp_printer
import cpp_parser
import cpp_lang

fg_dir = '/home/farad/Ohjelmoiminen/fg/flightgear'

# load source file
source_code = '\n'.join(
    open(os.path.join(fg_dir, 'src/Input/FGEventInput.hxx'))
)

# remove comments and preprocessor directives from the code
stripped_source = (cpp_parser.comment | cpp_parser.preprocessor).suppress().transformString(source_code)

printer = cpp_printer.CppPrinter()
classes = (cpp_parser.hierarchical_type_def | cpp_parser.hierarchical_type_decl).searchString(stripped_source)

print('found %d classes:' % len(classes))

for cl in classes:
    print()
    if type(cl[0]) == cpp_lang.CppHierarchicalTypeDefinition:
        print(printer.hierarchical_type_str(cl[0]))

