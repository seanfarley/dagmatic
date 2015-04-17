import nose.tools as nt

import dagmatic


def test_readme_1_simple():
    input = r'''
   a-b-c
      \
       d-e
'''
    dags = _parse(input)
    nt.assert_equal(len(dags), 1)
    dag = dags[0]
    nodes = {node.name: node for node in dag.nodes}
    nt.assert_items_equal(nodes, ['a', 'b', 'c', 'd', 'e'])
    _assert_parents(nodes['a'], [])
    _assert_parents(nodes['b'], ['a'])
    _assert_parents(nodes['c'], ['b'])
    _assert_parents(nodes['d'], ['b'])
    _assert_parents(nodes['e'], ['d'])


def test_readme_2_obsolescence():
    input = r'''
  a-b-c
   \: :
    d-e
'''
    dags = _parse(input)
    nt.assert_equal(len(dags), 1)
    dag = dags[0]
    nodes = {node.name: node for node in dag.nodes}
    nt.assert_items_equal(nodes, ['a', 'b', 'c', 'd', 'e'])
    _assert_parents(nodes['d'], ['a'])
    _assert_precursors(nodes['a'], [])
    _assert_precursors(nodes['b'], [])
    _assert_precursors(nodes['c'], [])
    _assert_precursors(nodes['d'], ['b'])
    _assert_precursors(nodes['e'], ['c'])


def _parse(input):
    return dagmatic.parse(input.splitlines())


def _assert_parents(node, expect):
    actual = map(str, node.parents)
    nt.assert_items_equal(actual, expect)


def _assert_precursors(node, expect):
    actual = map(str, node.precursors)
    nt.assert_items_equal(actual, expect)
