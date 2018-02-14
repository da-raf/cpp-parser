import sys; sys.path.append('..')

import os

import cpp_printer
import cpp_parser
import cpp_lang

import argparse

parser = argparse.ArgumentParser(
        description='list class definitions in a source file'
)
parser.add_argument('source_file')
args = parser.parse_args()

# load source file
source_code = '\n'.join( open(args.source_file) )

# remove comments and preprocessor directives from the code
stripped_source = (cpp_parser.comment | cpp_parser.preprocessor).suppress().transformString(source_code)

printer = cpp_printer.CppPrinter()
classes = (cpp_parser.hierarchical_type_def).searchString(stripped_source)

print('found %d classes:' % len(classes))

for (i, cl) in enumerate(classes):
    print('-------------------')
    print('--- %2d ------------' % i)
    print('-------------------')
    if type(cl[0]) == cpp_lang.CppHierarchicalTypeDefinition:
        print(printer.hierarchical_type_str(cl[0]))

