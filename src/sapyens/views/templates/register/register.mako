<%inherit file="${context.get('base_template')}" />


<%block name="title">${page_title}</%block>


<h2>${page_title}</h2>


% if include_services:
    <h4>using...</h4>

    <div style="margin-left: 2em;">
    	<%include file="sapyens.views:templates/register/services.mako"/>
   	</div>

   	% if include_email_form:
    	<h4>or using...</h4>
    % endif
% endif

% if include_email_form:
	<%include file="sapyens.views:templates/register/email_form.mako"/>
% endif