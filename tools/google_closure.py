#! /usr/bin/env python
# encoding: utf-8

import os, sys
from waflib import Task, TaskGen

def configure(conf):

    conf.load('python')
    conf.find_program('java', var='JAVA')

    conf.find_program('gjslint.py',
            path_list=os.path.join(conf.path.abspath(), 'lib', 'closure_linter'),
            var='CLOSURE_LINTER')

    conf.find_program('fixjsstyle.py',
            path_list=os.path.join(conf.path.abspath(), 'lib', 'closure_linter'),
            var='CLOSURE_LINTER_FIX')

    conf.find_program('compiler.jar',
            path_list=os.path.join(conf.path.abspath(), 'tools','closure-compiler'),
            var='CLOSURE_COMPILER_JAR')

    conf.find_program('SoyToJsSrcCompiler.jar',
            path_list=os.path.join(conf.path.abspath(), 'lib','closure-templates'),
            var='CLOSURE_TEMPLATES')

    conf.find_program('closure-stylesheets.jar',
            path_list=os.path.join(conf.path.abspath(), 'lib','closure-stylesheets'),
            var='CLOSURE_STYLESHEETS')

    conf.find_program('closurebuilder.py',
            path_list=os.path.join(conf.path.abspath(), 'lib','closure-library','closure','bin','build'),
            var='CLOSURE_BUILDER')

    conf.env.CLOSURE_LIBRARY  = os.path.join(conf.path.abspath(), 'lib', 'closure-library')
    conf.env.CLOSURE_SCRIPTS  = os.path.join(conf.env.CLOSURE_LIBRARY, 'closure/bin/build')

    sys.path.append(conf.env.CLOSURE_SCRIPTS)


class closure_compiler_task(Task.Task):

    vars = ['PYTHON', 'CLOSURE_BUILDER', 'CLOSURE_LIBRARY', 'CLOSURE_COMPILER']

    def __init__(self, namespaces, roots, target, compiler_flags=[], *k, **kw):
        Task.Task.__init__(self, *k, **kw)

        self.namespaces = namespaces
        self.target = target
        self.compiler_flags = compiler_flags

        self.paths = None

        self.set_outputs(target)

        self.roots = [
            os.path.join(self.env.CLOSURE_LIBRARY, 'closure/goog'),
            os.path.join(self.env.CLOSURE_LIBRARY, 'third_party/closure/goog')
        ]
        self.roots += roots

    def run(self):
        jscompiler = __import__('jscompiler')

        compiled_source = jscompiler.Compile(
                self.env.CLOSURE_COMPILER_JAR,
                [s.abspath() for s in self.inputs],
                self.compiler_flags)

        if compiled_source is None:
            self.fatal('JavaScript compilation failed.')

        self.outputs[0].write(compiled_source)
        return 0

    def scan(self):
        treescan = __import__('treescan')
        depstree = __import__('depstree')
        closurebuilder = __import__('closurebuilder')

        sources = set()

        for path in self.roots:
            for js_path in treescan.ScanTreeForJsFiles(path):
                sources.add(closurebuilder._PathSource(js_path))

        tree = depstree.DepsTree(sources)

        input_namespaces = set()
        for ns in self.namespaces:
            input_namespaces.add(ns)

        # The Closure Library base file must go first.
        base = closurebuilder._GetClosureBaseFile(sources)
        deps = [base] + tree.GetDependencies(input_namespaces)

        dep_paths = (os.path.relpath(s.GetPath(), self.bld.path.srcpath()) for s in deps)
        dep_nodes = [self.bld.path.find_resource(p) for p in dep_paths]
        
        self.set_inputs(dep_nodes)

        return (dep_nodes, [])

from waflib.Configure import conf

@conf
def closure_compiler(self, *k, **kw):
    kw['env'] = self.env
    tsk = closure_compiler_task(*k, **kw)
    self.add_to_group(tsk)
    return tsk


@TaskGen.feature('gjslint')
def gjslint(self):

    command = [self.env.PYTHON, self.env.CLOSURE_LINTER, '--strict', '-r']

    if isinstance(self.roots, str):
        self.roots = self.roots.split()
    command += self.roots

    return self.bld.exec_command(command)

@TaskGen.feature('fixjsstyle')
def fixjsstyle(self):

    command = [self.env.PYTHON, self.env.CLOSURE_LINTER_FIX, '--strict', '-r']

    if isinstance(self.roots, str):
        self.roots = self.roots.split()
    command += self.roots

    return self.bld.exec_command(command)

from waflib import TaskGen
TaskGen.declare_chain(name='template',
        rule='${JAVA} -jar ${CLOSURE_TEMPLATES} \
                --shouldProvideRequireSoyNamespaces \
                --cssHandlingScheme GOOG \
                --outputPathFormat ${TGT} \
                ${SRC}',
        ext_in='.soy', ext_out='.soy.js',
        before='closure_compiler_task',
        after='stylesheet')

'''
        --pretty-print \
        --output-renameing-map ${TGT[0].parent.abspath()}/renaming_map.js \
        --output-renameing-map-format CLOSURE_UNCOMPILED \
        --rename CLOSURE \
'''

TaskGen.declare_chain(name='stylesheet',
        rule='${JAVA} -jar ${CLOSURE_STYLESHEETS} \
                --output-file ${TGT} \
                ${SRC}',
        ext_in='.gss', ext_out='.css',
        before='closure_compiler_task',
        reentrant = False)
