<%inherit file="${context.get('base_template')}" />


<%!
	page_title = u"Admin section"
%>

<%block name="title">${page_title}</%block>


<h3>${page_title}</h3>

<ul>
	%for crud in sorted(cruds, key = lambda crud: crud.get_title()):
		<li><a href="${request.route_path(crud.list.route_name)}">${crud.get_title()}</a></li>
	%endfor
</ul>