from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from web.forms import DatasetRunForm
from web.services import (
    DatasetValidationError,
    load_builtin_dataset,
    load_report,
    load_uploaded_dataset,
    report_path,
    run_prioritization,
    save_report,
)


def home(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = DatasetRunForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                test_cases, dataset_name = _load_dataset_from_form(form)
                result = run_prioritization(
                    test_cases=test_cases,
                    dataset_name=dataset_name,
                    training_episodes=form.cleaned_data["training_episodes"],
                    evaluation_episodes=form.cleaned_data["evaluation_episodes"],
                    execution_budget=form.cleaned_data["execution_budget"],
                    seed=form.cleaned_data["seed"],
                    agent_seed=form.cleaned_data["agent_seed"],
                )
                report_id = save_report(result)
            except DatasetValidationError as exc:
                form.add_error(None, str(exc))
            else:
                return redirect("web:results", report_id=report_id)
    else:
        form = DatasetRunForm()

    return render(request, "web/home.html", {"form": form})


def results(request: HttpRequest, report_id: str) -> HttpResponse:
    try:
        report = load_report(report_id)
    except FileNotFoundError as exc:
        raise Http404("Report not found.") from exc

    return render(request, "web/results.html", {"report": report})


def download_report(request: HttpRequest, report_id: str) -> HttpResponse:
    try:
        path = report_path(report_id)
    except FileNotFoundError as exc:
        raise Http404("Report not found.") from exc

    response = HttpResponse(path.read_text(encoding="utf-8"), content_type="application/json")
    response["Content-Disposition"] = f'attachment; filename="{path.name}"'
    return response


def _load_dataset_from_form(form: DatasetRunForm):
    uploaded_file = form.cleaned_data.get("uploaded_file")
    if uploaded_file:
        return load_uploaded_dataset(uploaded_file)

    return load_builtin_dataset(form.cleaned_data["dataset_choice"])
