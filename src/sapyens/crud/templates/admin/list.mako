<%inherit file="${context.get('base_template')}" />


<%block name="title">${page_title}</%block>


<h3>${page_title}</h3>

<%include file="sapyens.crud:templates/list.mako"/>
