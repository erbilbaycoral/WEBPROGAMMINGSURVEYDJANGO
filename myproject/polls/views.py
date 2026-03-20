from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

from .models import Choice, Question

from django.db import IntegrityError
from django.contrib import messages

def register_request(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        try:
            if form.is_valid():
                user = form.save()
                login(request, user)
                return redirect("polls:index")
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{error}")
        except IntegrityError:
            messages.error(request, "Bu kullanıcı adı alınmış veya sunucu hatası oluştu. Lütfen tekrar deneyin.")
    else:
        form = UserCreationForm()
    return render(request, "polls/register.html", {"form": form})

def landing_page(request):
    return render(request, "polls/landing.html")

class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        """
        Return published questions filtered by region.
        """
        queryset = Question.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")
        
        if self.request.user.is_authenticated:
            try:
                user_country = self.request.user.profile.country_preference
            except Exception:
                user_country = 'Türkiye'
            queryset = queryset.filter(country=user_country)
        else:
            queryset = queryset.filter(country='Türkiye')
        
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(question_text__icontains=q)
            
        region = self.request.GET.get('region')
        if region:
            queryset = queryset.filter(region=region)
        return queryset[:20]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import REGION_CHOICES
        context['region_choices'] = REGION_CHOICES
        return context


class DetailView(generic.DetailView):
    model = Question
    template_name = "polls/detail.html"

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())


class ResultsView(generic.DetailView):
    model = Question
    template_name = "polls/results.html"


def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "Bir seçenek seçmediniz.",
            },
        )
    else:
        selected_choice.votes += 1
        selected_choice.save()
        return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))

from django.contrib.auth.decorators import login_required

@login_required
def create_poll(request):
    from .models import REGION_CHOICES, COUNTRY_CHOICES, QUESTION_TYPE_CHOICES
    if request.method == 'POST':
        question_text = request.POST.get('question_text')
        country = request.POST.get('country')
        question_type = request.POST.get('question_type') or 'Genel'
        
        if country != 'Türkiye':
            question_type = 'Genel'
            region = 'Genel'
        else:
            region = request.POST.get('region') if question_type == 'Bölgesel' else 'Genel'
            
        choices = request.POST.getlist('choice')
        
        if question_text and country and any(c.strip() for c in choices):
            try:
                q = Question.objects.create(
                    question_text=question_text,
                    pub_date=timezone.now(),
                    author=request.user,
                    country=country,
                    question_type=question_type,
                    region=region
                )
                for c in choices:
                    if c.strip():
                        Choice.objects.create(question=q, choice_text=c.strip())
                messages.success(request, "Anketiniz başarıyla oluşturuldu!")
                return redirect('polls:index')
            except Exception as e:
                messages.error(request, f"Bir hata oluştu: {e}")
        else:
            messages.error(request, "Lütfen gerekli alanları doldurun.")
            
    return render(request, 'polls/create_poll.html', {
        'region_choices': REGION_CHOICES,
        'country_choices': COUNTRY_CHOICES,
        'type_choices': QUESTION_TYPE_CHOICES
    })

from django.contrib.auth import update_session_auth_hash
from django.contrib import messages

@login_required
def account_settings(request):
    from .models import COUNTRY_CHOICES
    user = request.user
    
    try:
        profile = user.profile
    except Exception:
        from .models import UserProfile
        profile = UserProfile.objects.create(user=user)

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_profile':
            user.email = request.POST.get('email', '')
            user.save()
            profile.phone_number = request.POST.get('phone_number', '')
            profile.country_preference = request.POST.get('country_preference', 'Türkiye')
            profile.save()
            messages.success(request, 'Profil bilgileri güncellendi.')
            
        elif action == 'update_username':
            new_username = request.POST.get('username')
            now = timezone.now()
            if profile.last_username_change:
                diff = now - profile.last_username_change
                if diff.days < 30:
                    messages.error(request, f'Kullanıcı adını değiştirmek için {30 - diff.days} gün daha beklemelisiniz.')
                    return redirect('polls:settings')
            
            from django.contrib.auth.models import User
            if User.objects.filter(username=new_username).exclude(id=user.id).exists():
                messages.error(request, 'Bu kullanıcı adı zaten alınmış.')
            elif new_username:
                user.username = new_username
                user.save()
                profile.last_username_change = now
                profile.save()
                messages.success(request, 'Kullanıcı adı başarıyla değiştirildi.')
                
        elif action == 'update_password':
            from django.contrib.auth.forms import PasswordChangeForm
            form = PasswordChangeForm(user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Şifreniz başarıyla değiştirildi.')
            else:
                for error in form.errors.values():
                    messages.error(request, error)
        
        return redirect('polls:settings')
        
    return render(request, 'polls/settings.html', {'country_choices': COUNTRY_CHOICES})

@login_required
def my_polls(request):
    questions = Question.objects.filter(author=request.user).order_by('-pub_date')
    return render(request, 'polls/my_polls.html', {'questions': questions})

@login_required
def toggle_privacy(request, question_id):
    question = get_object_or_404(Question, id=question_id, author=request.user)
    if request.method == 'POST':
        question.is_private_results = not question.is_private_results
        question.save()
        messages.success(request, f'"{question.question_text}" anketi gizliliği güncellendi.')
    return redirect('polls:my_polls')