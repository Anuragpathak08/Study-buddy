from django.shortcuts import render,HttpResponse,redirect,get_object_or_404
from .forms import UserProfileChangeForm
from .models import *
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required



@login_required(login_url='login_signup')
def home(request):
    return render(request, 'home.html')


def login_signup(request):
    error_message = None
    signup_error = None

    if request.method == 'POST':
        # Handle login form submission
        if 'username' in request.POST and 'password' in request.POST:
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                error_message = 'Invalid username or password.'

        # Handle signup form submission
        elif 'username' in request.POST and 'email' in request.POST and 'password1' in request.POST and 'password2' in request.POST:
            username = request.POST['username']
            email = request.POST['email']
            password1 = request.POST['password1']
            password2 = request.POST['password2']

            # Validate passwords
            if password1 != password2:
                signup_error = 'Passwords do not match.'
            elif User.objects.filter(username=username).exists():
                signup_error = 'Username already exists.'
            elif User.objects.filter(email=email).exists():
                signup_error = 'Email already exists.'
            else:
                try:
                    # Create the user
                    user = User.objects.create_user(username=username, email=email, password=password1)
                    user.save()
                    return redirect('login_signup')  # Redirect to login after successful signup
                except Exception as e:
                    signup_error = f"Error creating user: {str(e)}"

    return render(request, 'login_signup.html', {'error_message': error_message, 'signup_error': signup_error})

def logout_view(request):
    logout(request)  # Log the user out
    return redirect('login_signup')



from django.core.paginator import Paginator

@login_required(login_url='login_signup')
def chat(request, chat_id):
    # Get the chat object
    chat = get_object_or_404(Chat, id=chat_id)

    # Ensure the user is part of this chat
    if request.user not in [chat.user1, chat.user2]:
        return redirect('home')  # Redirect unauthorized users to the home page

    # Determine the other user in the chat
    chat_user = chat.user2 if request.user == chat.user1 else chat.user1

    # Fetch all messages in the chat and paginate them
    messages = Message.objects.filter(chat=chat).select_related('sender').order_by('created_at')
    paginator = Paginator(messages, 50)  # Show 50 messages per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'chat.html', {
        'chat': chat,
        'chat_user': chat_user.username,
        'messages': page_obj,  })

@login_required(login_url='login_signup')
def send_message(request, chat_id):
    if request.method == 'POST':
        chat = get_object_or_404(Chat, id=chat_id)
        message_text = request.POST.get('message')

        # Save the new message
        Message.objects.create(
            chat=chat,
            sender=request.user,
            message_text=message_text
        )

    return redirect('chat', chat_id=chat_id)

@login_required(login_url='login_signup')
def chat_list(request):
    # Fetch all one-on-one chats involving the logged-in user
    one_on_one_chats = Chat.objects.filter(user1=request.user) | Chat.objects.filter(user2=request.user)

    # Fetch all groups where the logged-in user is a member
    user_groups = Group.objects.filter(memberships__user=request.user)

    return render(request, 'chat_list.html', {
        'one_on_one_chats': one_on_one_chats,
        'user_groups': user_groups
    })


@login_required(login_url='login_signup')
def new_chat(request):
    # Fetch all users except the logged-in user
    users_list = User.objects.exclude(id=request.user.id)
    return render(request, 'newchat.html', {'users_list': users_list})

@login_required(login_url='login_signup')
def start_chat(request, user_id):
    # Get the selected user
    user2 = get_object_or_404(User, id=user_id)

    # Check if a chat already exists between the two users
    chat = Chat.objects.filter(user1=request.user, user2=user2).first()
    if not chat:
        chat = Chat.objects.filter(user1=user2, user2=request.user).first()

    # If no chat exists, create a new one
    if not chat:
        chat = Chat.objects.create(user1=request.user, user2=user2)

    # Redirect to the chat page
    return redirect('chat', chat_id=chat.id)


@login_required(login_url='login_signup')
def new_group(request):
    # Fetch all users except the logged-in user
    users = User.objects.exclude(id=request.user.id)
    return render(request, 'newgroup.html', {'users': users})

@login_required(login_url='login_signup')
def create_group(request):
    if request.method == 'POST':
        group_name = request.POST.get('group_name')
        selected_user_ids = request.POST.getlist('selected_users')

        # Create the group
        group = Group.objects.create(name=group_name, created_by=request.user)

        # Add the creator to the group
        GroupMembership.objects.create(user=request.user, group=group)

        # Add selected users to the group
        for user_id in selected_user_ids:
            user = User.objects.get(id=user_id)
            GroupMembership.objects.create(user=user, group=group)

        # Redirect to the group chat page
        return redirect('group_chat', group_id=group.id)

    return redirect('new_group')


@login_required(login_url='login_signup')
def group_chat(request, group_id):
    # Get the group object
    group = get_object_or_404(Group, id=group_id)

    # Ensure the user is part of this group
    if not GroupMembership.objects.filter(user=request.user, group=group).exists():
        return redirect('home')

    # Fetch all messages in the group
    messages = GroupMessage.objects.filter(group=group).order_by('created_at')

    return render(request, 'group_chat.html', {
        'group': group,
        'messages': messages
    })

@login_required(login_url='login_signup')
def send_group_message(request, group_id):
    if request.method == 'POST':
        group = get_object_or_404(Group, id=group_id)
        message_text = request.POST.get('message')

        # Save the new message
        GroupMessage.objects.create(
            group=group,
            sender=request.user,
            message_text=message_text
        )

    return redirect('group_chat', group_id=group_id)


@login_required(login_url='login_signup')
def profile(request):
    # Get or create the user's profile
    user_profile, created = User_Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Handle form submission
        avatar = request.FILES.get('avatar', None)
        bio = request.POST.get('bio', '')
        location = request.POST.get('location', '')

        # Update the profile fields
        if avatar:
            user_profile.avatar = avatar
        user_profile.bio = bio
        user_profile.location = location
        user_profile.save()

        return redirect('profile')  # Redirect to the updated profile page

    return render(request, 'profile.html', {'user_profile': user_profile})