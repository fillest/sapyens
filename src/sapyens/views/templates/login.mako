<%inherit file="${context.get('base_template')}" />


<%block name="title">${page_title}</%block>


<h2>${page_title}</h2>


% if enable_services:
    <h4>using...</h4>

    <div style="margin-left: 2em;">
        <%include file="sapyens.views:templates/register/services.mako"/>
    </div>

    % if enable_email_form:
        <h4>or using...</h4>
    % endif
% endif

% if enable_email_form:
    <script type="text/javascript">
        $(function () {
            $('#userid').focus();
        });
    </script>


    %if request.authenticated_userid:
       <div class="alert alert-warning">You are already logged in as ${request.authenticated_userid}.</div>
        %if is_forbidden:
           <div class="alert alert-error">Requested page requires more permissions than you currently have.</div>
        %endif
    %endif

    %if auth_failed:
        <div class="alert alert-error">Incorrect email or password.</div>
    %endif

    <form class="form-horizontal" action="" method="post">
        <input name="_login_submit" type="hidden" value="1">

        <div class="control-group">
            <label class="control-label" for="userid">Email</label>
            <div class="controls">
                <input name="userid" id="userid" type="text" value="${data['userid']}">
            </div>
        </div>
        <div class="control-group">
            <label class="control-label" for="password">Password</label>
            <div class="controls">
                <input name="password" id="password" type="password" value="${data['password']}">
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
% endif