from django.shortcuts import redirect, render

# these views only return the html pages.
# all data is loaded by javascript (static/frontend/app.js) from the /api/ endpoints


def home(request):
    return redirect('queries-page')


def login_page(request):
    return render(request, 'frontend/login.html')


def register_page(request):
    return render(request, 'frontend/register.html')


def queries_page(request):
    return render(request, 'frontend/queries.html')


def query_new_page(request):
    return render(request, 'frontend/query_form.html')


def query_edit_page(request, pk):
    return render(request, 'frontend/query_form.html', {'pk': pk})


def query_detail_page(request, pk):
    return render(request, 'frontend/query_detail.html', {'pk': pk})
