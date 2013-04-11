# _*_ coding: utf-8 _*_
from collections import OrderedDict
from sqlalchemy import desc,  asc
from webob.multidict import MultiDict

class SortQueryGenerator(OrderedDict): 
    
    @classmethod
    def from_getlist(cls,  field_list): 
        # assert isinstance(field_list,  unicode)
        return cls(cls._convert_from_getlist(field_list))

    @classmethod
    def _convert_from_getlist(cls,  raw_field_names): 
        if not raw_field_names: 
            return
        for field in raw_field_names.split(','): 
            name,  order = field.split(':')
            assert order in ('asc',  'desc')
            yield (name, order)

    def __setitem__(self, name,  order): 
        superobj = super(SortQueryGenerator, self)

        assert order in ('desc',  'asc',  None)
        if order in ('asc',  'desc'): 
            superobj.__setitem__(name,  order)
        elif order is None: 
            superobj.__delitem__(name)

    _mutate = __setitem__
            
    def get_params(self): 
        res = []
        for field, order in self.items(): 
            res.append('{name}:{order}'.  format(name = field,  order = order))
            
        return ",".  join(res)

    def get_query(self, query,  mapping): 
        for field, order in self.items(): 
            field = mapping.get(field)
            if field is not None: 
                if order == 'asc': 
                    query = query.order_by(asc(field))
                else: 
                    query = query.order_by(desc(field))
        return query

    def can_sort(self,  name,  order): 
        my_order = self.get(name)
        if my_order is None and order == None:
            return False
        elif order == my_order:
            return False
        else: 
            return True



class FilterQueryGenerator(list): 
    
    @classmethod
    def from_params(cls, params): 
        obj = cls()
        filters_names = params.getall('filter')
        for f in filters_names: 
            op = params.get('op[{0}]'.format(f))
            v = params.get('v[{0}]'.  format(f))
            obj.append((f, op, v))
        return obj

    def get_params(self): 
        res = []
        for name, op, v in self: 
            res.append(('filter', name))
            res.append(('op[{0}]'.format(name), op))
            res.append(('v[{0}]'.format(name), v))
        return res # TODO: to MultiDict

    def get_query(self, query,  mapping): 
        for field_name, op, v in self: 
            if op != 'equal': 
                continue
            field = mapping.get(field_name)
            if field is not None: 
                query = query.filter(field == v)
        return query


class Query(object): 

    # TODO: configurability.  If someone dislike pagination

    def __init__(self, params): 
        self.sorter =  SortQueryGenerator.from_getlist(params.get('sort'))
        self.filter =  FilterQueryGenerator.from_params(params)
        self.page = params.get('page', 0)

    def copy(self): 
        return self.__class__(self.get_params())

    def get_alchemy_query(self, query, mapping): 
        query = self.sorter.get_query(query,  mapping)
        query = self.filter.get_query(query,  mapping)
        return query

    def get_params(self): 
        params =  []
        
        # TODO: it wants to be prettier

        filters = self.filter.get_params()
        if filters: 
            params += filters

        sort =  self.sorter.get_params()
        if sort: 
            params.append(('sort', sort))

        page = self.page
        if page: 
            params.append(('page',  self.page))

        return MultiDict(params)


    # helpers for template.  Must be in mixin
    # anyway we should use request there. cos this is only params
    def get_sort_url(self, request, name, order):
        params =  self.copy()
        params.sorter._mutate(name, order)
        return request.current_route_url(_query=params.get_params())

    def get_filter_url(self, request, field_name, op,  v):
        params =  self.copy()
        params.filter = params.filter.__class__([(field_name, op,  v)])
        return request.current_route_url(_query=params.get_params())
        
    def clear_sort(self, request): 
        params =  self.copy()
        params.sorter =  params.sorter.__class__()
        return request.current_route_url(_query=params.get_params())

    def clear_filter(self, request): 
        params =  self.copy()
        params.filter =  params.filter.__class__()
        return request.current_route_url(_query=params.get_params())

    def get_page(self, request, page_num): 
        params =  self.copy()
        params.page =  page_num
        return request.current_route_url(_query=params.get_params())



def get_fields_from_model(model): 
    fields = {column.name: column for column in model.__table__.columns}
    return fields

