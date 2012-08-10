from pyramid.httpexceptions import HTTPFound, HTTPForbidden
from sapyens.helpers import get_by_id, raise_not_found
from wtforms.ext import csrf
import wtforms.widgets
import wtforms


def make_relation_field (model, *args):
	class ItemWidget (unicode):
		def all_objects (self):
			return model.query.all()

	class RelationField (wtforms.IntegerField):
		widget = wtforms.widgets.HiddenInput()

		def process_formdata (self, valuelist):
			[id] = valuelist
			self.data = model.query.get(id)

	return wtforms.FieldList(RelationField(), *args, widget = ItemWidget('sapyens.crud:templates/relation.mako'))


class SecureForm (csrf.SecureForm):
	def generate_csrf_token (self, request):
		return request.session.get_csrf_token()

	def validate_csrf_token (self, field):
		if field.current_token != field.data:
			raise HTTPForbidden()


class CrudView (object):
	renderer = None
	route_name = None
	route_path = None

	def __init__ (self, model_class, form_class):
		self._model = model_class
		self._form_class = form_class

	def include_to_config (self, config):
		raise NotImplementedError()


class SubmitView (CrudView):
	redirect_route = None
	db_session = None
	list_route = None
	page_title = None

	def _fetch_model (self, request):
		raise NotImplementedError()

	def __call__ (self, request):
		model = self._fetch_model(request)
		form = self._form_class(request.POST, csrf_context = request)
		if form.validate():
			#TODO remove old csrf token?

			form.populate_obj(model)

			self.db_session.add(model)
			self.db_session.flush()

			request.session.flash('successfully updated')

			return HTTPFound(location = request.route_url(self.redirect_route, id = model.id))
		else:
			return {
				'model': model,
				'form': form,
				'submit_path': request.current_route_path(),
				'list_route': self.list_route,
				'page_title': self._page_title(model),
			}

	def _page_title (self, model):
		raise NotImplementedError()

class CreateView (SubmitView):
	def _fetch_model (self, _request):
		return self._model()

	def include_to_config (self, config):
		config.add_route(self.route_name, self.route_path)
		config.add_view(self, route_name = self.route_name, renderer = self.renderer, request_method = 'POST', permission = self.permission)

		config.add_view(lambda req: HTTPFound(
			location = self._make_GET_redirect_route(req)
		), route_name = self.route_name, request_method = 'GET', permission = self.permission)

	def _make_GET_redirect_route (self, request): #TODO shit
		return req.route_url(self.redirect_route)

	def _page_title (self, _model):
		return self.page_title or (u"create %s" % unicode(self._model.__name__)) #TODO copypaste

class UpdateView (CreateView):
	def _fetch_model (self, request):
		return get_by_id(self._model, int(request.matchdict['id'])) or raise_not_found()

	def _page_title (self, model):
		return (self.page_title or (u"edit %s #{id}" % unicode(self._model.__name__))).format(id = model.id) #TODO copypaste

class EditView (CrudView):
	submit_path_route = None
	list_route = None
	page_title = None

	def __call__ (self, request):
		model = get_by_id(self._model, int(request.matchdict['id'])) or raise_not_found()
		return {
			'model': model,
			'form': self._form_class(obj = model, csrf_context = request),
			'submit_path': request.route_path(self.submit_path_route, id = model.id),
			'list_route': self.list_route,
			'page_title': (self.page_title or (u"edit %s #{id}" % unicode(self._model.__name__))).format(id = model.id)
		}

	def include_to_config (self, config):
		config.add_route(self.route_name, self.route_path)
		config.add_view(self, route_name = self.route_name, renderer = self.renderer, permission = self.permission)

class NewView (EditView):
	def __call__ (self, request):
		return {
			'model': self._model(),
			'form': self._form_class(csrf_context = request),
			'submit_path': request.route_path(self.submit_path_route),
			'list_route': self.list_route,
			'page_title': self.page_title or (u"create %s" % unicode(self._model.__name__))
		}

class ListView (CrudView):
	edit_route = None
	edit_title = lambda _self, obj: obj
	new_route = None
	delete_route = None
	page_title = None

	def __call__ (self, request):
		models = self._model.query.order_by(self._model.id.desc()).all()
		return {
			'models': models,
			'edit_route': self.edit_route,
			'edit_title': self.edit_title,
			'new_route': self.new_route,
			'delete_route': self.delete_route,
			'page_title': self.page_title or (u"%s list" % unicode(self._model.__name__))
		}

	def include_to_config (self, config):
		config.add_route(self.route_name, self.route_path)
		config.add_view(self, route_name = self.route_name, renderer = self.renderer, permission = self.permission)

class DeleteView (CrudView):
	redirect_route = None

	def __call__ (self, request):
		#TODO csrf
		self._model.query.filter_by(id = request.matchdict['id']).delete()
		return HTTPFound(location = request.route_url(self.redirect_route))

	def include_to_config (self, config):
		config.add_route(self.route_name, self.route_path)
		config.add_view(self, route_name = self.route_name, permission = self.permission)


class Crud (object):
	model = None
	form = None

	new = None
	edit = None
	create = None
	update = None
	list = None
	delete = None

	@classmethod
	def include_to_config (cls, config):
		for view_class in (cls.new, cls.edit, cls.create, cls.update, cls.list, cls.delete):
			view_class(cls.model, cls.form).include_to_config(config)


def make_view_classes (pathname, db_session_, permission_ = 'admin',
		new = NewView, edit = True, create = True, update = True, list_ = True, delete = True):
	classes = []

	class CommonParams (object):
		renderer = 'sapyens.crud:templates/admin/edit.mako'
		permission = permission_

	list_route_ = '%s.list' % pathname
	delete_route_ = '%s.delete' % pathname

	if new:
		class New (CommonParams, new):
			route_name = '%s.new' % pathname
			route_path = '/%s/new' % pathname
			submit_path_route = '%s.create' % pathname
			list_route = list_route_
		classes.append(New)

	if edit:
		class Edit (CommonParams, EditView):
			route_name = '%s.edit' % pathname
			route_path = '/%s/edit/{id:\d+}' % pathname
			submit_path_route = '%s.update' % pathname
			list_route = list_route_
		classes.append(Edit)

	if create:
		class Create (CommonParams, CreateView):
			route_name = '%s.create' % pathname
			route_path = '/%s/create' % pathname
			redirect_route = Edit.route_name #TODO !
			list_route = list_route_
			db_session = db_session_
			def _make_GET_redirect_route (self, request):
				return request.route_url(New.route_name)
		classes.append(Create)

	if update:
		class Update (CommonParams, UpdateView):
			route_name = '%s.update' % pathname
			route_path = '/%s/update/{id:\d+}' % pathname
			redirect_route = '%s.edit' % pathname
			list_route = list_route_
			db_session = db_session_
			def _make_GET_redirect_route (self, request):
				return request.route_url(Edit.route_name, id = request.matchdict['id'])
		classes.append(Update)

	if list_:
		class List (CommonParams, ListView):
			renderer = 'sapyens.crud:templates/admin/list.mako'
			route_name = list_route_
			edit_route = Edit.route_name #TODO !
			route_path = '/%s/list' % pathname
			db_session = db_session_
			new_route = New.route_name
			delete_route = delete_route_
		classes.append(List)

	if delete:
		class Delete (CommonParams, DeleteView):
			route_name = delete_route_
			route_path = '/%s/delete/{id:\d+}' % pathname
			redirect_route = List.route_name
		classes.append(Delete)

	return classes
