<%!
	import wtforms.widgets
%>


<a href="${request.route_path(list_route)}">list</a>


##TODO move to view
<% flash_msgs = request.session.pop_flash() %>
% if flash_msgs:
	<ul>
		% for msg in flash_msgs:
			<li style="color: green;">${msg}</li>
		% endfor
	</ul>
% endif


<form action="${submit_path}" method="post">
	##%if not caster.is_valid:
	##	<strong>invalid</strong> ${caster.errors}
	##%endif

	##<ul>
		% for field in form:
			##<li>
				% if field.errors:
					<ul>
						% for error in field.errors:
							<li style="color: red;">${error}</li>
						% endfor
					</ul>
				% endif

				% if isinstance(field.widget, basestring):
					<%include file="${field.widget}" args="field = field" />
				% else:
					% if not isinstance(field.widget, wtforms.widgets.HiddenInput):
						${field.label}
					% endif

					${field}
				% endif
			##</li>
		% endfor
	##</ul>

	<input type="submit" value="save" />
</form>
