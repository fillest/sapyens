<%!
	import wtforms.widgets
%>


<style type="text/css">
	.sapyens-crud-form input {width: 700px;}
</style>


<div>
	<a href="${request.route_path(list_route)}">View list</a>
</div>


##TODO move to view
<% flash_msgs = request.session.pop_flash() %>
% if flash_msgs:
	% for msg in flash_msgs:
		<div class="alert alert-success">${msg}</div>
	% endfor
% endif

<form action="${submit_path}" method="post" class="sapyens-crud-form form-horizontal">
	<fieldset>
		<legend>${page_title}</legend>

		% for field in form:
			% if isinstance(field.widget, wtforms.widgets.HiddenInput):
				${field}
			% else:
				<div class="control-group ${'error' if field.errors else ''}">
					% if isinstance(field.widget, basestring):
						##TODO move errors to include somehow?
						% if field.errors:
							<ul>
								% for error in field.errors:
									<li style="color: red;">${error}</li>
								% endfor
							</ul>
						% endif

						<%include file="${field.widget}" args="field = field" />
					% else:
						${field.label(class_ = 'control-label')}
						
						<div class="controls">
							${field}

							% if field.errors:
								% for error in field.errors:
									<span class="help-block">${error}</span>
								% endfor
							% endif
						</div>
					% endif
				</div>
			% endif
		% endfor

		<div class="form-actions">
			<button type="submit" class="btn btn-primary">Save</button>
		</div>
	</fieldset>
</form>
