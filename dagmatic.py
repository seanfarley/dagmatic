#!/usr/bin/python

from __future__ import print_function

import sys
import re

# We're looking for node labels (runs of alphanumeric chars) and the edges
# between them. E.g. given a line like "  \ a-b  :", the tokens of interest
# are \, a, -, b, :. This regex is a good place to start (but now we have
# two problems).
nodefind_re = re.compile(r'([a-zA-Z0-9\']+)')


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
        chunks = nodefind_re.split(line.rstrip())
        for (idx, chunk) in enumerate(chunks):
            if idx % 2 == 1:            # must be a node (run of alphanumeric)
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

    nodes = set()

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
            elif ch == ':':
                if row == 0:
                    raise err('obsolescence marker on first line')
                elif row == len(grid) - 1:
                    raise err('obsolescence marker on last line')
                elif col >= len(grid[row + 1]):
                    raise err('obsolescence marker points past end of next line')

                precursor = grid[row - 1][col]
                successor = grid[row + 1][col]
                if not (isinstance(precursor, Node) and
                        isinstance(successor, Node)):
                    raise err('obsolescence marker connected to garbage')
                successor.precursors.append(precursor)
            elif isinstance(ch, Node):
                nodes.add(ch)

    nodemap = {node.name: node for node in nodes}
    return [DAG(nodemap)]


class DAGSyntaxError(Exception):
    def __init__(self, row, col, msg):
        self.row = row
        self.col = col
        super(DAGSyntaxError, self).__init__(msg)


class Node(object):
    def __init__(self, name):
        self.name = name
        self.parents = []               # list of Node
        self.precursors = []            # list of Node

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Node: %s>' % (self.name,)


class DAG(object):
    '''A graph of nodes. Actually this is two overlaid graphs: the traditional
    DAG of parent/child relationships, and the newfangled directed cyclic
    graph of obsolescence markers.
    '''
    def __init__(self, nodemap):
        self.nodemap = nodemap              # map node name to Node

    def get_parent_names(self, name):
        '''return parents of specified node as str (node names)'''
        return [parent.name for parent in self.nodemap.get(name).parents]

    def get_precursor_names(self, name):
        '''return precursors of specified node as str (node names)'''
        return [precursor.name for precursor in self.nodemap.get(name).precursors]

    def dump(self, outfile):
        for node in self.nodemap.values():
            parents = ','.join(str(p) for p in node.parents)
            obs = ''
            if node.precursors:
                precursors = ','.join(str(p) for p in node.precursors)
                obs = ' (obsoletes %s)' % (precursors,)
            print('%s -> %s%s' % (node, parents, obs), file=outfile)


def main():
    daglist = parse(sys.stdin)
    for dag in daglist:
        print('dag:')
        dag.dump(sys.stdout)


if __name__ == '__main__':
    main()
