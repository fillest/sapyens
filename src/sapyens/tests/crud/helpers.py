# _*_ coding: utf-8 _*_

from unittest import TestCase
from webob.multidict import MultiDict
from collections import OrderedDict

from badman.helpers import SortQueryGenerator,  FilterQueryGenerator


class SortQueryGeneratorTest(TestCase): 
    
    def equality_test(self): 
        n = SortQueryGenerator()
        self.assertEqual(n.get_params(), '')

        # be careful !
        n = SortQueryGenerator((('a',  'asc'),  ('a',  'desc'),  ('b',  'asc')))        
        self.assertEqual(n.get_params(), 'a:desc,b:asc')

        n = SortQueryGenerator.from_getlist('a:asc,b:desc')
        self.assertEqual(OrderedDict((('a', 'asc'), ('b', 'desc'))), OrderedDict(n))

    def test_copy(self): 
        n = SortQueryGenerator((('a',  'asc'),  ('a',  'desc'),  ('b',  'asc')))        
        m =  n.copy()

    def test_mutation(self): 
        n = SortQueryGenerator((('a',  'asc'),  ('a',  'desc'),  ('b',  'asc')))        
        self.assertEqual(n.get_params(), 'a:desc,b:asc')
        n._mutate('a',  'asc')
        self.assertEqual(n.get_params(), 'a:asc,b:asc')
        n._mutate('b',  None)
        self.assertEqual(n.get_params(), 'a:asc')

    def test_mutation_new(self): 
        n = SortQueryGenerator((('a',  'asc'),  ('a',  'desc'),  ('b',  'asc')))        
        self.assertEqual(n.get_params(), 'a:desc,b:asc')
        n['a'] = 'asc'
        self.assertEqual(n.get_params(), 'a:asc,b:asc')

        m1 = n.copy()        
        m2 = n.copy()

        del m1['b']
        self.assertEqual(m1.get_params(), 'a:asc')

        m2['b'] = None
        self.assertEqual(m2.get_params(), 'a:asc')

    # TODO: can_sort



class FilterQueryGeneratorTest(TestCase): 
    
    def simple_test(self): 
        n =  FilterQueryGenerator()
        n.append(('name', 'like', 'trololo'))
        self.assertEqual(
            n.get_params(), 
            [('filter', 'name'), ('op[name]', 'like'), ('v[name]', 'trololo')]
        )
        params =  MultiDict([('filter', 'name'), ('op[name]', 'like'), ('v[name]', 'trololo')])
        m = FilterQueryGenerator.from_params(params)
        self.assertEqual(n, m)


