

<%def name="generate_sort_button(field_name, order, verbose_name)">
	% if params.sorter.can_sort(field_name, order):
	  <a href='${params.get_sort_url(request, field_name, order)}'> ${ verbose_name } </a>
	%else:
		${ verbose_name }
	% endif
</%def>


<%def name="render_header(grid)">
    <tr>
 
    % for field_name in grid.fields_to_display:
        <td> ${ field_name } |
		${ generate_sort_button(field_name, None, 'off') }		|
		${ generate_sort_button(field_name, 'desc', 'desc') }	|
		${ generate_sort_button(field_name, 'asc', 'asc') }		
		 </td>
    % endfor
    </tr>
</%def>

<%def name="render_grid(grid)">
	  ${ render_header(grid) }
	  ${ render_body(grid) }
</%def>

<%def name="render_body(grid)">
  <tbody>
  % for obj in items:
  	<tr>	
	% for field_name in grid.fields_to_display:
		<td>
			${ grid.render_field(field_name, obj) } 
		</td>		
	% endfor
    </tr>
  % endfor
</%def>

${ grid.query.pager() }