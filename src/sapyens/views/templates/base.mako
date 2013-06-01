<!DOCTYPE html>
<html>
	<head>
		<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />

		<title><%block name="title">override this</%block></title>

		<link rel="stylesheet" href="${request.static_url('sapyens:static/bootstrap/css/bootstrap.min.css')}" charset="UTF-8" />
		<%block name="links"></%block>

		<script src="${request.static_url('sapyens:static/js/jquery.min.js')}" type="text/javascript" charset="UTF-8"></script>
		<script src="${request.static_url('sapyens:static/bootstrap/js/bootstrap.min.js')}" type="text/javascript" charset="UTF-8"></script>
		<%block name="scripts"></%block>
	</head>
	<body>
		${next.body()}
	</body>
</html>