from django import forms


class LoginForm(forms.Form):
    username = forms.CharField(label='Username', max_length=100)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)


class MeasurementForm(forms.Form):
    measurement = forms.CharField(label='Measurement')
    measurement_name = forms.CharField(label='Measurement Name')


class UploadFileForm(forms.Form):
    file = forms.FileField()
    tag = forms.CharField(label='Tag')
    label = forms.CharField(label='Label')
    availability = forms.BooleanField(label='Should the image be available for all users?', required=False,
                                      initial=False)
    measurement_type = forms.ChoiceField(label='Measurement Type',
                                         choices=[('general', 'General'), ('background', 'Background'), ('background_later', 'Enhanced Background')], required=False)
    docker_logger = forms.BooleanField(label='Is the measured data stored in extra files?', required=False,
                                       initial=False)
    docker_path = forms.CharField(label='Path of directory, where data is stored.', required=False)

    def clean(self):
        super(UploadFileForm, self).clean()

        docker_logger = self.cleaned_data.get('docker_logger')
        docker_path = self.cleaned_data.get('docker_path')
        # check if file is a zip file
        file = self.cleaned_data.get('file')
        if not file:
            self._errors['file'] = self.error_class(['File is required.'])
            return self.cleaned_data

        if not file.name.endswith('.zip'):
            self._errors['file'] = self.error_class(['File is not a zip file.'])

        if docker_logger and not docker_path:
            self._errors['docker logging info'] = self.error_class(
                ['If you are saving measured data in extra place, then please provide a path.'])
        return self.cleaned_data


class MeasurementHead(forms.Form):
    measurement_name = forms.CharField(label='Measurement Name')
    measurement_modem = forms.CharField(label='Measurement Device')
    apn = forms.CharField(label='APN')
    ip_type = forms.CharField(label='IP Type')
