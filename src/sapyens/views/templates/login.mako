<%inherit file="sapyens.views:templates/base.mako" />


<%block name="title">Log in</%block>


<script type="text/javascript">
    $(function () {
        $('#userid').focus();
    });
</script>


%if auth_failed:
    <div class="alert alert-error">Incorrect email or password</div>
%endif

<form class="form-horizontal" action="" method="post">
    <input type="hidden" name="redirect_url" value="${data['redirect_url']}" />

    <div class="control-group">
        <label class="control-label" for="userid">Email</label>
        <div class="controls">
            <input name="userid" type="text" id="userid" placeholder="Email" value="${data['userid']}">
        </div>
    </div>
    <div class="control-group">
        <label class="control-label" for="password">Password</label>
        <div class="controls">
            <input name="password" type="password" id="password" placeholder="Пароль" value="${data['password']}">
        </div>
    </div>

    <div class="control-group">
        <div class="controls">
            ##<label class="checkbox">
            ##    <input type="checkbox"> Remember me
            ##</label>

            <button type="submit" class="btn">Log in</button>
        </div>
    </div>
</form>