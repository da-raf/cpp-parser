import sys; sys.path.append('..')

import pyparsing as pp

import cpp_parser
import cpp_lang

import os


# in DSO eigen-macros tend to break things
eigen_macro = 'EIGEN_' + pp.Word(pp.srange("[A-Z_]"))


c_base_types = ['char', 'unsigned char', 'short', 'int', 'long', 'float', 'double', 'size_t']
cpp_base_types = ['bool'] + c_base_types
# TODO: detect template names
def is_basetype(type_name):
    return type_name in cpp_base_types or type_name.startswith('std::') or type_name == 'T'

c_file_extensions = ['h', 'c']
cpp_file_extensions = ['hxx', 'hpp', 'cxx', 'cpp', 'C'] + c_file_extensions
def is_source_file(file_name):
    for extns in cpp_file_extensions:
        if file_name.endswith('.' + extns):
            return True
    return False

def filecontent(source_file):
    class_list = []
    deriv_list = []
    links_list = []

    source_code = ''.join(open(source_file))

    # remove comments and preprocessor directives from the code
    stripped_source = (cpp_parser.comment | cpp_parser.preprocessor | eigen_macro).suppress().transformString(source_code)
    classes = (cpp_parser.hierarchical_type_def | cpp_parser.hierarchical_type_decl).searchString(stripped_source)
    typedefs = cpp_parser.type_def.searchString(stripped_source)

    for cl in classes:
        if len(cl) == 1:
            c = cl[0]
        else:
            print('WARNING: received raw parsing result in %s' % source_file)
            continue
            #c = cl

        if not c.name:
            print('WARNING: no class name! file: %s: %s' % (source_file, repr(c)))
            continue

        class_list.append(c.name)

        for deriv in c.base_types:
            if not deriv.base_id:
                print('WARNING: no class name of base class! %s:%s' % (source_file, c.name))
            else:
                if not is_basetype(deriv.base_id):
                    deriv_list.append( (c.name, deriv.base_id) )

        for member in c.member_variables:
            if not member.member_decl:
                print('WARNING: missing member declaration! %s:%s' % (source_file, c.name))
            else:
                member_type_name = member.member_decl.data_type.content_name()
                if not is_basetype(member_type_name):
                    links_list.append( (c.name, member_type_name) )

    for td in typedefs:
        # unpack
        td = td[0]

        class_list.append( td.type_name )
        try:
            base_id = td.type_expr.content_name()
            if not is_basetype(base_id):
                deriv_list.append( (td.type_name, base_id) )
        except AttributeError:
            print('WARNING: received raw parsing data in typedef expression "%s"->"%s" in file "%s"' % (td.type_expr, td.type_name, source_file))
            pass
    
    return (class_list, deriv_list, links_list)

def filecontent2dot(source_file):
    (class_list, deriv_list, assoc_list) = filecontent(source_file)

    class_dot = ['"%s" [shape=box];' % cn for cn in class_list]
    deriv_dot = ['"%s" -> "%s" [arrowhead=onormal];' % (bn, bcn) for (bn, bcn) in deriv_list]
    assoc_dot = ['"%s" -> "%s";' % (cn, acn) for (cn, acn) in assoc_list]

    # concatenate list of dot links
    # we can treat them identically from now on, since we already did the formatting
    return (class_dot, deriv_dot + assoc_dot)

def do_file(file_path):
    (classes_dot, links_dot) = filecontent2dot( file_path )

    if len(classes_dot) == 0:
        return ([], [])

    # open file's subgraph
    file_dot = [
            'subgraph "cluster_%s" {' % os.path.basename(file_path),
            '\tlabel = "%s";'         % os.path.basename(file_path)
    ] + ['\t'+class_dot for class_dot in classes_dot] + ['}']

    return (file_dot, links_dot)


def do_dir(dir_root):
    links_dot = []

    dir_dot = [
            'subgraph "cluster_%s" {' % dir_root,
            '\tlabel = "%s";'         % dir_root
    ]

    for node_name in os.listdir(dir_root):
        node_path = os.path.join(dir_root, node_name)

        if os.path.isdir(node_path):
            (node_dot, inner_links_dot) = do_dir(node_path)
        if os.path.isfile(node_path) and is_source_file(node_path):
            (node_dot, inner_links_dot) = do_file(node_path)

        dir_dot   += ['\t'+l for l in node_dot]
        links_dot += inner_links_dot

    dir_dot += ['}']

    return (dir_dot, links_dot)


def source_to_diagram(root_path, dot_diagram_path):

    # open whole graph
    graph_dot = [ 'digraph class_diagram {' ]

    if os.path.isdir(root_path):
        (blocks_dot, links_dot) = do_dir(root_path)
    elif os.path.isfile(root_path):
        (blocks_dot, links_dot) = do_file(root_path)

    # generate content
    graph_dot += [ ('\t' + l) for l in (blocks_dot + links_dot) ]
    # close graph
    graph_dot += ['}']

    with open(dot_diagram_path, 'w') as out_file:
        for l in graph_dot:
            out_file.write(l + '\n')

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

