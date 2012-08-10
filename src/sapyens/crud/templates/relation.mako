<%page args="field"/>

<%
	add_relation_item_modal_class = 'add-%s-relation-item-modal' % field.name
	add_relation_item_func_name = 'add_%s_relation_item' % field.name
%>


<script>
	function ${add_relation_item_func_name} (obj_id, obj_title) {
		'use strict';

		if ($('#relation-items input').length) {
			var next_i = parseInt($('#relation-items input').last().attr('name').match(/(\d+)$/)[1]) + 1;
		} else {
			var next_i = 0;
		}

		$('<li>'
			+ '<a class="btn btn-small js-unlink-relation-item" href="#"><i class="icon-remove"></i></a>'
			+ ' ' + obj_title
			+ '<input name="${field.name}-' + next_i + '" type="hidden" value="' + obj_id + '">'
			+ '</li>'
		).appendTo($('#relation-items'));

		$('#${add_relation_item_modal_class}').modal('hide');

		return false;
	}

	$(function () {
		'use strict';

		##TODO add name to classes?
		$('body').on('click', '.js-unlink-relation-item', function () {
			$(this).closest('li').remove();
			return false;
		});

		$('body').on('click', '.js-show-add-relation-item', function () {
			$('#${add_relation_item_modal_class}').modal();
			return false;
		});

		% for subfield in field:
			##TODO escape quotes
			${add_relation_item_func_name}(${subfield.data.id}, "${subfield.data.title}");
		% endfor
	});
</script>

<div>
	<div>${field.label.text}</div>

	<ul class="unstyled" id="relation-items">
		## is filled from js
		##TODO show loader img
	</ul>

	<div><a class="btn btn-small js-show-add-relation-item" href="#"><i class="icon-plus"></i> add</a></div>
</div>

<div class="modal hide" id="${add_relation_item_modal_class}">
	<div class="modal-header">
		<button type="button" class="close" data-dismiss="modal">×</button>
		<h3>${field.label.text}: choose an item to link with</h3>
	</div>
	<div class="modal-body">
		<p>
			<ul>
				% for obj in field.widget.all_objects():
					<li>
						<a href="#" onclick="return ${add_relation_item_func_name}(${obj.id}, '${obj.title}');">${obj.title}</a>
					</li>
				% endfor
			</ul>
		</p>
	</div>
</div>
