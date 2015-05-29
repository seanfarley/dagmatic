#!/usr/bin/env python

from __future__ import print_function

import sys
import re

# We're looking for node labels (runs of alphanumeric chars) and the edges
# between them. E.g. given a line like "  \ a-b  :", the tokens of interest
# are \, a, -, b, :. This regex is a good place to start (but now we have
# two problems).
nodefind_re = re.compile(r'([a-zA-Z0-9\'^]+)')


def parse(infile):
    '''Read a sequence of lines. Return a DAGList.
    '''
    # First step: turn input lines into a "grid" of character cells.
    # grid[i][j] tells us what is occupying cell (i,j): either a node
    # or a single non-node character.
    grid = _read_grid(infile)
    print('grid:')
    for line in grid:
        print(line)

    # Now turn the grid into an AST-like thing: the DAGList.
    return _make_daglist(grid)


def _read_grid(infile):
    grid = []
    for line in infile:
        grid.append([])
        currow = grid[-1]
        if line.lstrip().startswith('||'):
            ws, text = line.split('||')
            currow += [ws, '||', TransitionText(text.strip())]
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
                    currow += list(chunk)
    return grid


def _make_daglist(grid):
    row = col = None

    def err(msg):
        return DAGSyntaxError(row, col, msg)

    ret = []                    # list of dags and transitions
    dag = []                    # of Nodes

    in_text = False

    for (row, line) in enumerate(grid):
        if in_text and line and not contains_text(line):
            ret.append(Annotation(dag))
            dag = []
            in_text = False
        for (col, ch) in enumerate(line):
            if ch == '-':
                if col == 0:
                    raise err('horizontal edge at start of line')
                elif col == len(line) - 1:
                    raise err('horizontal edge at end of line')

                parent = line[col - 1]
                child = line[col + 1]
                if not (isinstance(parent, Node) and isinstance(child, Node)):
                    raise err('horizontal edge connected to garbage')
                child.parents.append(parent)
            elif ch == '|':
                if row == 0:
                    raise err('vertical edge on first line')
                elif row == len(grid) - 1:
                    raise err('vertical edge on last line')

                parent = grid[row + 1][col]
                child = grid[row - 1][col]
                if not (isinstance(parent, Node) and isinstance(child, Node)):
                    raise err('vertical edge connected to garbage')
                child.parents.append(parent)
            elif ch == '.':
                if col == 0:
                    raise err('horizontal obs edge at start of line')
                elif col == len(line) - 1:
                    raise err('horizontal obs edge at end of line')

                precursor = line[col - 1]
                successor = line[col + 1]
                if not (isinstance(precursor, Node) and
                        isinstance(successor, Node)):
                    raise err('horizontal obs edge connected to garbage')
                successor.precursors.append(precursor)
                precursor.obsolete = True
            elif ch == '\\':
                if row == 0:
                    raise err('diagonal edge on first line')
                elif row == len(grid) - 1:
                    raise err('diagonal edge on last line')
                elif col == 0:
                    raise err('diagonal edge at start of line')
                elif col >= len(grid[row + 1]):
                    raise err('diagonal edge points past end of next line')

                parent = grid[row - 1][col - 1]
                child = grid[row + 1][col + 1]
                if not (isinstance(parent, Node) and isinstance(child, Node)):
                    raise err('diagonal edge connected to garbage')
                child.parents.append(parent)
            elif ch == '/':
                if row == 0:
                    raise err('diagonal edge on first line')
                elif row == len(grid) - 1:
                    raise err('diagonal edge on last line')
                elif col == 0:
                    raise err('diagonal edge at start of line')
                elif col >= len(grid[row + 1]):
                    raise err('diagonal edge points past end of next line')

                parent = grid[row + 1][col - 1]
                child = grid[row - 1][col + 1]
                if not (isinstance(parent, Node) and isinstance(child, Node)):
                    raise err('diagonal edge connected to garbage')
                child.parents.append(parent)
            elif ch == '<':
                if row == 0:
                    raise err('obsolescence marker on first line')
                elif row == len(grid) - 1:
                    raise err('obsolescence marker on last line')
                elif col == 0:
                    raise err('obsolescence marker at start of line')
                elif col >= len(grid[row + 1]):
                    raise err('obsolescence marker points past '
                              'end of next line')

                precursor = grid[row - 1][col - 1]
                successor = grid[row + 1][col + 1]
                if not (isinstance(parent, Node) and isinstance(child, Node)):
                    raise err('obsolescence marker connected to garbage')
                successor.precursors.append(precursor)
                precursor.obsolete = True
            elif ch == ':':
                if row == 0:
                    raise err('obsolescence marker on first line')
                elif row == len(grid) - 1:
                    raise err('obsolescence marker on last line')
                elif col >= len(grid[row + 1]):
                    raise err('obsolescence marker points past '
                              'end of next line')

                precursor = grid[row - 1][col]
                successor = grid[row + 1][col]
                if not (isinstance(precursor, Node) and
                        isinstance(successor, Node)):
                    raise err('obsolescence marker connected to garbage')
                successor.precursors.append(precursor)
                precursor.obsolete = True
            elif ch == '>':
                if row == 0:
                    raise err('obsolescence marker on first line')
                elif row == len(grid) - 1:
                    raise err('obsolescence marker on last line')
                elif col == 0:
                    raise err('obsolescence edge at start of line')
                elif col >= len(grid[row - 1]):
                    raise err('obsolescence marker points past '
                              'end of next line')

                precursor = grid[row - 1][col + 1]
                successor = grid[row + 1][col - 1]
                if not (isinstance(precursor, Node) and
                        isinstance(successor, Node)):
                    raise err('obsolescence marker connected to garbage')
                successor.precursors.append(precursor)
                precursor.obsolete = True
            elif ch == '||' and not in_text:
                # an ugly hack until we implement the state pattern
                ret.append(DAG(dag))
                dag = []
                in_text = True
            elif isinstance(ch, Node) or isinstance(ch, TransitionText):
                if ch not in dag:
                    if isinstance(ch, Node):
                        # set the grid location into the node
                        ch.row = row
                        ch.col = col

                    dag.append(ch)

    if dag:
        if in_text:
            dag = Annotation(dag)
        else:
            dag = DAG(dag)
        ret.append(dag)

    return ret


class DAGSyntaxError(Exception):
    def __init__(self, row, col, msg):
        self.row = row
        self.col = col
        self.msg = msg


class Node(object):
    def __init__(self, name):
        self.name = name
        self.parents = []               # list of Node
        self.precursors = []            # list of Node
        self.annotation = ''
        self.row = -1
        self.col = -1
        self.obsolete = False
        self.style = {}

        if '^' in name:
            self.name, self.annotation = name.split('^', 1)

        if self.annotation in ('O', 'T'):
            self.obsolete = True

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Node: %s>' % (self.name,)

class Style(dict):
    def __repr__(self):
        return '<Style: %s>' % (dict.__repr__(self),)


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
            obs = ''
            if node.obsolete:
                obs = 'obs'
            if node.annotation == 'T':
                obs = 'tmp'

            # first output the changeset node
            print(r'\node[%s] at (%d,%d) (%s) {%s};' % (obs + 'changeset',
                                                        node.col, -node.row,
                                                        node, node))
        for node in self.nodes:
            # output the edges
            for p in node.parents:
                print(r'\draw[edge] (%s) -- (%s);' % (p, node))

            # output the obsolete edges
            for p in node.precursors:
                print(r'\draw[markeredge] (%s) -- (%s);' % (p, node))

class Annotation(object):
    '''A collection of text objects.
    '''
    def __init__(self, text):
        self.text = text

    def dump(self, outfile):
        for text in self.text:
            print('TEXT: %s' % (text), file=outfile)


class TransitionText(object):
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text

    def __repr__(self):
        return '<TransitionText: %s>' % (self.text,)


def contains_text(dag):
    for i in dag:
        if isinstance(i, TransitionText):
            return True
    return False

def main():
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

  || (safe again)

  a-b.c
   \:
    d
'''
    ]

    for i in inputs:
        print('input:')
        print(i.lstrip('\n'))
        daglist = parse(i.splitlines())
        for dag in daglist:
            print('dag:')
            dag.dump(sys.stdout)


main()
