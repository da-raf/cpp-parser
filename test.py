import cpp_printer
import cpp_parser
import cpp_lang

# load source file
source_code = '\n'.join(
    open('/home/farad/Programmieren/fg/flightgear/src/Input/FGEventInput.hxx')
)

# remove comments and preprocessor directives from the code
stripped_source = (cpp_parser.comment | cpp_parser.preprocessor).suppress().transformString(source_code)

printer = cpp_printer.CppPrinter()
classes = (cpp_parser.complex_type_def | cpp_parser.complex_type_decl).searchString(stripped_source)

print('found %d classes:' % len(classes))

for cl in classes:
    print()
    if type(cl[0]) == cpp_lang.CppComplexTypeDefinition:
        print(printer.complex_type_str(cl[0]))
