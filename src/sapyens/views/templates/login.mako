<!DOCTYPE html>
<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />

		<title>log in</title>

        <script src="//ajax.googleapis.com/ajax/libs/jquery/1.7.2/jquery.min.js" type="text/javascript" charset="UTF-8"></script>
    </head>
    <body>
        <script type="text/javascript">
			$(function () {
				$('#username').focus();
			});
		</script>

		<form action="" method="post">
			%if auth_failed:
				<div style="color: red;">auth failed</div>
			%endif

			<input type="hidden" name="redirect_url" value="${redirect_url}" />

			<br /><label>username <input id="username" type="text" name="username" value="${username}" /></label>
			<br /><label>password <input type="password" name="password" value="${password}" /></label>
			<br /><input type="submit" value="log in" />
		</form>
    </body>
</html>
