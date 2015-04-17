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
    nt.assert_items_equal(dag.nodemap, ['a', 'b', 'c', 'd', 'e'])
    _assert_parents(dag, 'a', [])
    _assert_parents(dag, 'b', ['a'])
    _assert_parents(dag, 'c', ['b'])
    _assert_parents(dag, 'd', ['b'])
    _assert_parents(dag, 'e', ['d'])


def test_readme_2_obsolescence():
    input = r'''
  a-b-c
   \: :
    d-e
'''
    dags = _parse(input)
    nt.assert_equal(len(dags), 1)
    dag = dags[0]
    nt.assert_items_equal(dag.nodemap, ['a', 'b', 'c', 'd', 'e'])
    _assert_parents(dag, 'd', ['a'])
    _assert_precursors(dag, 'a', [])
    _assert_precursors(dag, 'b', [])
    _assert_precursors(dag, 'c', [])
    _assert_precursors(dag, 'd', ['b'])
    _assert_precursors(dag, 'e', ['c'])


def _parse(input):
    return dagmatic.parse(input.splitlines())


def _assert_parents(dag, name, expect):
    actual = dag.get_parent_names(name)
    nt.assert_items_equal(actual, expect)


def _assert_precursors(dag, name, expect):
    actual = dag.get_precursor_names(name)
    nt.assert_items_equal(actual, expect)
