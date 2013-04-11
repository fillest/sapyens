from functools import partial 
from webhelpers import paginate
from sapyens.crud.helpers import get_fields_from_model,  Query

class Grid(object): 

    template_helpers =  'sapyens.crud:templates/grid.mako'

    def __init__(self,  model,  fields_to_display): 
        super(Grid,  self).__init__(model, fields_to_display)
        self.mapping = get_fields_from_model(self._model)

    def get_template(self): 
        assert self.template_helpers
        return self.template_helpers

    def render_field(self,  name,  obj): 
        field = self.mapping.get(name)
        if field is not None: 
            return getattr(obj, name) # TODO: more fun there
        else: 
            return 'nan'

    def __call__(self,  request):
        params = Query(request.GET)
        true_query =  params.get_alchemy_query(self._model.query,  self.mapping)
        query = self.as_page(true_query, request, params = params, pagenum = params.page)        

        return {
            'items'  : query, 
            'grid'   : self, 
            'params' : params, 
        }

    # Helpers to paginator.  
    def page_generator(self, request, params, page): 
        """ This is for lambda """
        url = params.get_page(request, page)
        return url

    def as_page(self, query, request,  pagenum,  params): 
        url_generator =  partial(self.page_generator, request = request,  params = params)
        page = paginate.Page(query, page = pagenum,  url = url_generator)
        return page
