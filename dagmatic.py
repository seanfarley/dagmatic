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
    style = ''
    for line in infile:
        grid.append([])
        currow = grid[-1]
        if line.lstrip().startswith('||'):
            ws, text = line.split('||')
            currow += [ws, '||', TransitionText(text.strip())]
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
                    currow += list(chunk)
    return grid


def _make_daglist(grid):
    row = col = None

    def err(msg):
        return DAGSyntaxError(row, col, msg)

    dag = []

    for (row, line) in enumerate(grid):
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
            elif isinstance(ch, Node):
                # set the grid location into the node
                ch.row = row
                ch.col = col
                ch.name += str(row * 10 + col)
                if (isinstance(ch, TransitionText)):
                    prevrow = grid[row - 1]
                    if (col < len(prevrow) and
                        isinstance(grid[row - 1][col], TransitionText)):
                        grid[row - 1][col].append(ch)
                        continue

                dag.append(ch)
            elif isinstance(ch, Style):
                if 'node' not in ch:
                    raise err('style found but no node specified')

                def match(n1, n2):
                    if n2 == 'global':
                        return True
                    return n1 == n2

                for n in dag:
                    if match(n.name, ch['node']):
                        n.style = ch

    return DAG(dag)


class DAGSyntaxError(Exception):
    def __init__(self, row, col, msg):
        self.row = row
        self.col = col
        self.msg = msg


class Node(object):
    def __init__(self, name):
        self.name = name
        self.text = name
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


class TransitionText(Node):
    def __init__(self, text):
        super(TransitionText, self).__init__('t')
        self.text = text

    def __repr__(self):
        return '<TransitionText: %s>' % (self.text,)

    def append(self, tnode):
        self.text += '\n' + tnode.text


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

            cls = node.style.get('class') or obs + 'changeset'
            text = node.text
            if 'text' in node.style:
                # need to check this way because 'text' could be empty
                text = node.style['text']

            if not isinstance(node, TransitionText):
                print(r'\node[%s] at (%d,%d) (%s) {%s};' % (cls, node.col,
                                                            -node.row, node,
                                                            text))
            else:
                lines = text.splitlines()
                h = len(lines) + 1
                print('\\draw[double, double equal sign distance, -Implies]'
                      '(%d,%d) -- node[anchor=west, align=left] (%s) {%s}'
                      '++(0,%d);' % (node.col + 1, -(node.row - 1), node,
                                     '\\\\'.join(lines), -h))
        for node in self.nodes:
            # output the edges
            for p in node.parents:
                print(r'\draw[edge] (%s) -- (%s);' % (p, node))

            # output the obsolete edges
            for p in node.precursors:
                print(r'\draw[markeredge] (%s) -- (%s);' % (p, node))


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
        dag = parse(i.splitlines())
        print('dag:')
        dag.dump(sys.stdout)
        dag.tikz(sys.stdout)


main()
