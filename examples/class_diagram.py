import sys; sys.path.append('..')

import cpp_parser
import cpp_lang

import os


def is_basetype(type_name):
    c_base_types = ['int', 'float', 'double', 'long', 'char', 'bool']

    return type_name in c_base_types or type_name.startswith('std::')

def filecontent2dot(source_file):
    res = []

    source_code = '\n'.join(open(source_file))

    # remove comments and preprocessor directives from the code
    stripped_source = (cpp_parser.comment | cpp_parser.preprocessor).suppress().transformString(source_code)

    classes = (cpp_parser.hierarchical_type_def | cpp_parser.hierarchical_type_decl).searchString(stripped_source)

    for cl in classes:
        if len(cl) == 1:
            c = cl[0]
        else:
            c = cl

        if not c.name:
            print('WARNING: no class name! file: %s: %s' % (source_file, repr(c)))
            continue

        res.append('"%s" [shape=box];' % c.name)

        for deriv in c.base_types:
            if not deriv.base_id:
                print('WARNING: no class name of base class! %s:%s' % (source_file, c.name))
            else:
                res.append('"%s" -> "%s" [arrowhead=onormal];' % (c.name, deriv.base_id))
        for member in c.member_variables:
            if not member.member_decl:
                print('WARNING: missing member declaration! %s:%s' % (source_file, c.name))
            else:
                member_type_name = member.member_decl.data_type.content_name()
                if not is_basetype(member_type_name):
                    res.append('"%s" -> "%s";' % (c.name, member_type_name))

    return res

def do_file(file_path, out_stream):
    ls = filecontent2dot( file_path )

    if len(ls) == 0:
        return

    # open file's subgraph
    out_stream.write('\tsubgraph "cluster_%s" {\n' % os.path.basename(file_path))
    out_stream.write('\t\tlabel = "%s";\n'         % os.path.basename(file_path))

    for l in ls:
        out_stream.write('\t\t%s\n' % l)

    # close file's subgraph
    out_stream.write('\t}\n')


def do_dir(dir_root, out_stream):
    for (dir_path, dir_names, file_names) in os.walk(dir_root):
        # open directory subgraph
        out_stream.write('\tsubgraph "cluster_%s" {\n' % dir_path)
        out_stream.write('\tlabel = "%s";\n' % dir_path)

        for file_name in file_names:
            do_file( os.path.join(dir_path, file_name), out_stream )

        # close directory subgraph
        out_stream.write('\t}\n')

def source_to_diagram(root_path, dot_diagram_path):

    with open(dot_diagram_path, 'w') as out_file:
        # open whole graph
        out_file.write('digraph G {\n')

        if os.path.isdir(root_path):
            do_dir(root_path, out_file)
        elif os.path.isfile(root_path):
            do_file(root_path, out_file)

        # close whole graph
        out_file.write('}\n')

    return


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(
            description='construct a class diagram in dot-format from C++ source'
    )
    parser.add_argument(
            'source_tree_root',
            help='single file or directory in which the source is stored'
    )
    parser.add_argument(
            'output_file',
            default='out.dot',
            help='the file to which the dot-graph will be written'
    )
    args = parser.parse_args()

    source_to_diagram(args.source_tree_root, args.output_file)

