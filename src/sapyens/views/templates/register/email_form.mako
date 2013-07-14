%if form.errors:
    <div class="alert alert-error">
        <ul>
            %for field_name, field_errors in form.errors.items():
                %for error in field_errors:
                    <li>${form[field_name].label.text}: ${error}</li>
                %endfor
            %endfor
        </ul>
    </div>
%endif

<form class="form-horizontal" action="" method="post">
    <div class="control-group">
        ${form.email.label(class_ = "control-label")}
        <div class="controls">
            ${form.email}
        </div>
    </div>
    <div class="control-group">
        ${form.password.label(class_ = "control-label")}
        <div class="controls">
            ${form.password}
        </div>
    </div>

    <div class="control-group">
        <div class="controls">
            ##<label class="checkbox">
            ##    <input type="checkbox"> Remember me
            ##</label>

            <button type="submit" class="btn">Register</button>
        </div>
    </div>
</form>