<!DOCTYPE html>
<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
        ##<meta charset="UTF-8" />

		<title>
			<%block name="title">untitled</%block> — admin — ...
		</title>

        <link rel="stylesheet" href="//netdna.bootstrapcdn.com/twitter-bootstrap/2.0.4/css/bootstrap-combined.min.css" charset="UTF-8" />

        <%block name="links"></%block>

        <script src="//ajax.googleapis.com/ajax/libs/jquery/1.7.2/jquery.min.js" type="text/javascript" charset="UTF-8"></script>
		<script src="//netdna.bootstrapcdn.com/twitter-bootstrap/2.0.4/js/bootstrap.min.js" type="text/javascript" charset="UTF-8"></script>
    </head>
    <body>
        ${next.body()}
    </body>
</html>
