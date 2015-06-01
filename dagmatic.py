#!/usr/bin/env python

from __future__ import print_function

import sys
import re

from nodes import TransitionText, Node, Style
from edges import types

# We're looking for node labels (runs of alphanumeric chars) and the edges
# between them. E.g. given a line like "  \ a-b  :", the tokens of interest
# are \, a, -, b, :. This regex is a good place to start (but now we have
# two problems).
nodefind_re = re.compile(r'([a-zA-Z0-9\'^]+)')


def parse(text):
    '''Read a sequence of lines. Return a DAGList.
    '''
    # First step: turn input lines into a "grid" of character cells.
    # grid[i][j] tells us what is occupying cell (i,j): either a node
    # or a single non-node character.
    text = text.splitlines()
    grid = _read_grid(text)

    # Now turn the grid into an AST-like thing: the DAGList.
    return _make_daglist(grid)


def _read_grid(infile):
    grid = []
    style = ''
    for line in infile:
        grid.append([])
        currow = grid[-1]
        if line.lstrip().startswith('||'):
            ws, text = line.split('||')
            currow += [types[c] for c in ws]
            currow += [types['||'], TransitionText(text.strip())]
        elif line.lstrip().startswith('{') or style:
            style += line.strip()
            if line.rstrip().endswith('}'):
                nodestyle = Style()
                # parse the dictionary
                style = style.strip('{')
                style = style.strip('}')
                for kv in style.split(','):
                    if not kv.strip():
                        continue
                    key, val = kv.split(':', 1)
                    nodestyle[key.strip()] = val.strip()
                currow += [nodestyle]

                style = ''
        else:
            chunks = nodefind_re.split(line.rstrip())

            for (idx, chunk) in enumerate(chunks):
                if idx % 2 == 1:  # must be a node (run of alphanumeric)
                    node = Node(chunk)
                    currow += [node] * len(chunk)
                else:
                    # Must preserve every input char because of the visual
                    # nature of the input language -- need grid[i][j] to be
                    # useful!
                    currow += [types[c] for c in chunk]
    return grid


def _make_daglist(grid):
    dag = []

    for (row, line) in enumerate(grid):
        for (col, ch) in enumerate(line):
            ch.parse(dag, grid, row, col)

    return DAG(dag)


class DAG(object):
    '''A graph of nodes. Actually this is two overlaid graphs: the traditional
    DAG of parent/child relationships, and the newfangled directed cyclic
    graph of obsolescence markers.
    '''
    def __init__(self, nodes):
        self.nodes = nodes

    def dump(self, outfile):
        for node in self.nodes:
            parents = ','.join(str(p) for p in node.parents)
            obs = ''
            if node.precursors:
                precursors = ','.join(str(p) for p in node.precursors)
                obs = ' (obsoletes %s)' % (precursors,)
            print('%s[%d, %d] -> %s%s' % (node, node.row, node.col, parents,
                                          obs), file=outfile)

    def tikz(self, outfile):
        # need to do two passes so that all nodes are defined first
        for node in self.nodes:
            node.tikz(outfile)

        for node in self.nodes:
            # output the edges
            for p in node.parents:
                print(r'\draw[edge] (%s) -- (%s);' % (p, node), file=outfile)

            # output the obsolete edges
            for p in node.precursors:
                print(r'\draw[markeredge] (%s) -- (%s);' % (p, node),
                      file=outfile)


if __name__ == '__main__':
    # nice little test case: has a merge, one obsolescence marker, 2 roots
    inputs = [
        r'''
a-b-3-x
 \ \
  a-1-f-5
        :
        6-7-8
''',
        r'''
  a-b-c
   \: :
    d-e
''',
        r'''
  a-b.c
   \:
    b'
''',
        r'''
  a-b

  || hg commit --amend
  || (safe, using evolve)

  a-b.c
   \:
    d
''',
        r'''
      f
      |
    d-e
   /
  a-b-c^T
   <:>
    q

{
        node: e,
        text: ,
        class: test
}
{
        node: global,
        text: ,
}
{
        node: f,
        text: bug fix 1,
        class: nodenote
}
{node: q, text: master, class: nodenote}
''',
    ]

    for i in inputs:
        print('input:')
        print(i.lstrip('\n'))
        dag = parse(i)
        print('dag:')
        dag.dump(sys.stdout)
