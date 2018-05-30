import sys; sys.path.append('..')

import pyparsing as pp

import cpp_parser
import cpp_lang

import os


# in DSO eigen-macros tend to break things
eigen_macro = 'EIGEN_' + pp.Word(pp.srange('[A-Z_]'))


c_base_types = ['char', 'unsigned char', 'short', 'int', 'long', 'float', 'double', 'size_t']
cpp_base_types = ['bool'] + c_base_types
vector_type = ['std::vector']

# TODO: detect template names
def is_basetype(type_name):
    return type_name in cpp_base_types or type_name.startswith('std::') or type_name == 'T'

def is_vector(type_name):
    return type_name in vector_type

c_file_extensions = ['h', 'c']
cpp_file_extensions = ['hxx', 'hpp', 'cxx', 'cpp', 'C'] + c_file_extensions
def is_source_file(file_name):
    for extns in cpp_file_extensions:
        if file_name.endswith('.' + extns):
            return True
    return False


class Node:
    def __init__(self, path):
        self.path = path

    @staticmethod
    def load_from_disk(path):
        if os.path.isfile(path):
            return File.load_from_disk(path)
        elif os.path.isdir(path):
            return Directory.load_from_disk(path)


class Directory(Node):
    def __init__(self, path, nodes):
        super(Directory, self).__init__(path)
        self.nodes = nodes

    def internals(self):
        return ( internal for node in self.nodes for internal in node.internals() )

    def render(self, keep_only=None):
        class_dot = [
                'subgraph "cluster_%s" {' % self.path,
                '\tlabel = "%s";'         % self.path
        ]
        link_dot = []

        for n in self.nodes:
            (node_class_dot, node_link_dot) = n.render(keep_only)

            class_dot += ['\t'+l for l in node_class_dot]
            link_dot  += node_link_dot

        class_dot += [ '}' ]

        return (class_dot, link_dot)

    @staticmethod
    def load_from_disk(path):
        return Directory(path, [Node.load_from_disk(os.path.join(path, name))
                                    for name in os.listdir(path)
                                    if is_source_file(os.path.join(path,name))
                                    or  os.path.isdir(os.path.join(path,name))])


class File(Node):
    def __init__(self, path, class_defs, type_defs):
        super(File, self).__init__(path)
        self.class_defs = class_defs
        self.type_defs  = type_defs

    def internals(self):
        return ( internal for obj_def in (self.class_defs + self.type_defs) for internal in obj_def.internals() )

    def render(self, keep_only=None):
        # open file's subgraph
        class_dot = [
                'subgraph "cluster_%s" {' % os.path.basename(self.path),
                '\tlabel = "%s";'         % os.path.basename(self.path)
        ]
        link_dot = []

        for obj_def in self.class_defs + self.type_defs:
            (obj_class_dot, obj_link_dot) = obj_def.render(keep_only)

            class_dot += ['\t'+l for l in obj_class_dot]
            link_dot  += obj_link_dot

        class_dot += ['}']

        return (class_dot, link_dot)

    @staticmethod
    def load_from_disk(path):
        source_code = ''.join( open(path) )

        # remove comments and preprocessor directives from the code
        stripped_source = (cpp_parser.comment | cpp_parser.preprocessor | eigen_macro).suppress().transformString(source_code)

        # extract class/struct/union definitions and typedefs from the source code
        class_finds = cpp_parser.hierarchical_type_def.searchString(stripped_source)
        typedef_finds = cpp_parser.type_def.searchString(stripped_source)

        return File(
                path,
                [ Class.from_class  (cf[0]) for cf in   class_finds ],
                [ Class.from_typedef(tf[0]) for tf in typedef_finds ]
        )


class Class:
    def __init__(self, identifier, base_classes, members):
        self.identifier = identifier
        self.base_classes = base_classes
        self.members = members

    def internals(self):
        return [ self.identifier ]

    def render(self, keep_only=None):
        if keep_only is not None and self.identifier not in keep_only:
            return ([], [])

        class_dot = ['"%s" [shape=box];' % self.identifier]
        link_dot  = []

        # draw arrows to base classes
        for base_class in self.base_classes:
            if keep_only is not None and base_class not in keep_only:
                continue

            # suppress inheritances into the standard library
            if not is_basetype(base_class):
                link_dot.append(
                    '"%s" -> "%s" [arrowhead=onormal];' % (self.identifier, base_class)
                )

        for member in self.members:
            (member_class_dot, member_link_dot) = member.render(keep_only)
            class_dot += member_class_dot
            link_dot  += member_link_dot

        return (class_dot, link_dot)

    @staticmethod
    def from_class(class_obj):
        identifier = class_obj.name
        base_classes = []
        member_associations = []

        # collect base class identifiers
        for deriv in class_obj.base_types:
            if not deriv.base_id:
                print('BUG: %s - base class name empty!' % identifier)
                continue
            else:
                base_classes.append( deriv.base_id )

        # collect member type identifiers
        for member in class_obj.member_variables:
            if not member.member_decl:
                print('BUG: %s - missing member declaration!' % identifier)
                continue
            member_associations.append(
                    DirectedAssociation.from_decl(identifier, member.member_decl)
            )

        return Class(identifier, base_classes, member_associations)

    @staticmethod
    def from_typedef(typedef_obj):
        identifier = typedef_obj.type_name

        try:
            base_classes = [ typedef_obj.type_expr.content_name() ]
        except AttributeError:
            print('BUG: received raw parsing data in typedef expression "%s"->"%s"' % (typedef_obj.type_expr, identifier))
            return None

        return Class(identifier, base_classes, [])


class DirectedAssociation:
    def __init__(self, orig_class_name, target_class_name, assoc_name):
        self.orig_class_name = orig_class_name
        self.target_class_name = target_class_name
        self.assoc_name = assoc_name

    def render(self, keep_only=None):
        if keep_only is not None and self.target_class_name not in keep_only:
            return ([], [])
        if not is_basetype(self.target_class_name):
            link_dot = ['"%s" -> "%s";' % (self.orig_class_name, self.target_class_name)]
        else:
            link_dot = []
        return ([], link_dot)

    @staticmethod
    def from_decl(orig_class_name, member_decl):
        member_type  = member_decl.data_type
        member_ident = member_decl.identifier
        member_type_name = member_type.content_name()

        if is_vector(member_type_name):
            try:
                # use first template element
                template_type_name = member_type.template_args[0].content_name()
                # TODO: mark multiplicity
                return DirectedAssociation(orig_class_name, template_type_name, member_ident)
            except IndexError:
                print('BUG/WARNING: %s - member %s has vector type %s with empty template!' % (orig_class_name, member_ident, member_type_name))
                return None

        else:
            return DirectedAssociation(orig_class_name, member_type_name, member_ident)


class Diagram:

    # methods of Diagram class
    def __init__(self):
        self.roots = []

    def add_path(self, path):
        self.roots.append( Node.load_from_disk(path) )

    def internals(self):
        return (internal for root in self.roots for internal in root.internals())

    def render(self, keep_only=None):
        class_dot = []
        link_dot = []

        for node in self.roots:
            (node_class_dot, node_link_dot) = node.render(keep_only)
            class_dot += node_class_dot
            link_dot  += node_link_dot

        graph_dot  = [ 'digraph class_diagram {' ]
        graph_dot += [ ('\t' + l) for l in class_dot ]
        graph_dot += [ ('\t' + l) for l in  link_dot ]
        graph_dot += [ '}' ]

        return graph_dot

    def render_file(self, file_path, with_externals=False):
        with open(file_path, 'w') as f:
            if with_externals:
                for l in self.render():
                    f.write(l)
            else:
                ints = list(self.internals())
                for l in self.render(keep_only=ints):
                    f.write(l)
        return

    @staticmethod
    def from_pathlist(paths):
        d = Diagram()

        for path in paths:
            d.add_path(path)

        return d


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(
            description='construct a class diagram in dot-format from C++ source'
    )
    parser.add_argument(
            'output_file',
            default='out.dot',
            help='the file to which the dot-graph will be written'
    )
    parser.add_argument(
            'source_files',
            nargs='+',
            help='files or directories in which contain the source code to render'
    )
    args = parser.parse_args()

    diag = Diagram.from_pathlist(args.source_files)
    diag.render_file(args.output_file)

