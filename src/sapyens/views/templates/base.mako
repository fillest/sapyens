<!DOCTYPE html>
<html>
	<head>
		<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />

		<title><%block name="title">override this</%block></title>

		<link rel="stylesheet" href="http://cdn.fillest.ru/bootstrap.2.3.2/css/bootstrap.min.css" charset="UTF-8" />
		<%block name="links"></%block>

		<script src="http://cdn.fillest.ru/jquery-1.9.1.min.js" type="text/javascript" charset="UTF-8"></script>
		<script src="http://cdn.fillest.ru/bootstrap.2.3.2/js/bootstrap.min.js" type="text/javascript" charset="UTF-8"></script>
		<%block name="scripts"></%block>
	</head>
	<body>
		${next.body()}
	</body>
</html>