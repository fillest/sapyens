<%inherit file="${context.get('base_template')}" />


<%block name="title">${page_title}</%block>


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
            <input name="userid" type="text" id="userid" placeholder="" value="${data['userid']}">
        </div>
    </div>
    <div class="control-group">
        <label class="control-label" for="password">Password</label>
        <div class="controls">
            <input name="password" type="password" id="password" placeholder="" value="${data['password']}">
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