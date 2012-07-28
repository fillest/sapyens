<a href="${request.route_path(new_route)}">create</a>

% if models:
	<ul>
		% for obj in models:
			<li>
				<a href="${request.route_path(delete_route, id = obj.id)}" onclick="return confirm('Are you sure?');" class="btn btn-mini">
					<i class="icon-remove"></i>
				</a>
				<a href="${request.route_path(edit_route, id = obj.id)}">${edit_title(obj)}</a>
			</li>
		% endfor
	</ul>
% else:
	No objects found.
% endif
