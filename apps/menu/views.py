from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from apps.accounts.decorators import admin_required
from .models import MealCategory, Meal
from .forms import MealForm, MealCategoryForm
from apps.audit.services import log_action, get_client_ip


@login_required
def meal_list(request):
    categories = MealCategory.objects.prefetch_related('meals').all()
    return render(request, 'menu/meal_list.html', {'categories': categories})


@login_required
@admin_required
def meal_create(request):
    if request.method == 'POST':
        form = MealForm(request.POST, request.FILES)
        if form.is_valid():
            meal = form.save()
            log_action(
                user=request.user,
                action='MEAL_CREATED',
                description=f'Meal {meal.name} created with price ${meal.price:.2f}.',
                entity_type='Meal',
                entity_id=meal.id,
                ip_address=get_client_ip(request)
            )
            messages.success(request, f'Meal "{meal.name}" added successfully.')
            return redirect('menu:meal_list')
    else:
        form = MealForm()
    return render(request, 'menu/meal_form.html', {'form': form, 'title': 'Add New Meal'})


@login_required
@admin_required
def meal_edit(request, meal_id):
    meal = get_object_or_404(Meal, id=meal_id)
    if request.method == 'POST':
        form = MealForm(request.POST, request.FILES, instance=meal)
        if form.is_valid():
            form.save()
            log_action(
                user=request.user,
                action='MEAL_UPDATED',
                description=f'Meal {meal.name} updated.',
                entity_type='Meal',
                entity_id=meal.id,
                ip_address=get_client_ip(request)
            )
            messages.success(request, f'Meal "{meal.name}" updated successfully.')
            return redirect('menu:meal_list')
    else:
        form = MealForm(instance=meal)
    return render(request, 'menu/meal_form.html', {'form': form, 'title': f'Edit Meal: {meal.name}'})


@login_required
@admin_required
@require_POST
def meal_toggle_availability(request, meal_id):
    meal = get_object_or_404(Meal, id=meal_id)
    meal.is_available = not meal.is_available
    meal.save(update_fields=['is_available'])
    state = 'available' if meal.is_available else 'unavailable'
    messages.info(request, f'Meal "{meal.name}" is now {state}.')
    return redirect('menu:meal_list')


@login_required
@admin_required
def category_list(request):
    categories = MealCategory.objects.all()
    if request.method == 'POST':
        form = MealCategoryForm(request.POST)
        if form.is_valid():
            cat = form.save()
            messages.success(request, f'Category "{cat.name}" created.')
            return redirect('menu:category_list')
    else:
        form = MealCategoryForm()
    return render(request, 'menu/category_list.html', {'categories': categories, 'form': form})


@login_required
def api_meals(request):
    q = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')
    meals = Meal.objects.filter(is_available=True, is_archived=False)
    if category_id:
        meals = meals.filter(category_id=category_id)
    if q:
        meals = meals.filter(name__icontains=q)
    data = [
        {
            'id': m.id,
            'name': m.name,
            'price': float(m.price),
            'category': m.category.name,
            'image': m.image.url if m.image else None,
            'prep_time': m.preparation_time_minutes,
        }
        for m in meals
    ]
    return JsonResponse({'meals': data})

