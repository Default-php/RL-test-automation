from django import forms

from web.services import available_dataset_choices


class DatasetRunForm(forms.Form):
    dataset_choice = forms.ChoiceField(
        label="Built-in dataset",
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    uploaded_file = forms.FileField(
        label="Upload JSON dataset",
        required=False,
        widget=forms.FileInput(
            attrs={"class": "form-control", "accept": ".json,application/json"}
        ),
    )
    training_episodes = forms.IntegerField(
        label="Training episodes",
        initial=2000,
        min_value=1,
        max_value=10000,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    evaluation_episodes = forms.IntegerField(
        label="Evaluation episodes",
        initial=100,
        min_value=1,
        max_value=1000,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    execution_budget = forms.IntegerField(
        label="Execution budget",
        initial=3,
        min_value=1,
        max_value=50,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    seed = forms.IntegerField(
        label="Environment seed",
        initial=42,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    agent_seed = forms.IntegerField(
        label="Agent seed",
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["dataset_choice"].choices = [
            ("", "Select a dataset")
        ] + available_dataset_choices()

    def clean(self):
        cleaned_data = super().clean()
        dataset_choice = cleaned_data.get("dataset_choice")
        uploaded_file = cleaned_data.get("uploaded_file")

        if not dataset_choice and not uploaded_file:
            raise forms.ValidationError("Select a built-in dataset or upload a JSON file.")

        if dataset_choice and uploaded_file:
            raise forms.ValidationError("Use either a built-in dataset or an uploaded file.")

        if uploaded_file and not uploaded_file.name.lower().endswith(".json"):
            self.add_error("uploaded_file", "The uploaded file must use the .json extension.")

        return cleaned_data
