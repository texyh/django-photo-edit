from cloudinary import api

from django.shortcuts import render
from django.views.generic import View
from django.views.generic.base import TemplateView
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import Http404

from photoapp.models import FacebookUser, Photo
from context_processors import Image_Effects


class LoginRequiredMixin(object):

    '''View mixin which requires that the user is authenticated.'''

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(
            request, *args, **kwargs)


class HomeView(TemplateView):

    template_name = 'photoapp/index.html'


class FacebookLogin(View):

    def post(self, request, *args, **kwargs):

        user_id = request.POST["id"]
        try:
            fb_user = FacebookUser.objects.get(facebook_id=user_id)
            user = User.objects.get(id=fb_user.contrib_user_id)
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            return HttpResponse("success", content_type="text/plain")

        except ObjectDoesNotExist:

            # proceed to create the user
            first_name = request.POST["first_name"]
            last_name = request.POST["last_name"]
            picture = request.POST["picture[data][url]"]

            # Create the user
            user = User(
                username=u"%s, %s" % (first_name, last_name),
                email=request.POST["email"],
                first_name=first_name,
                last_name=last_name
            )
            user.save()

            # Create the facebook user
            fb_user = FacebookUser(facebook_id=user_id,
                                   contrib_user=user,
                                   contrib_picture=picture)

            user.backend = 'django.contrib.auth.backends.ModelBackend'

            fb_user.save()

            login(request, user)
            return HttpResponse("success", content_type="text/plain")


class SignOutView(View, LoginRequiredMixin):

    '''Logout User from session.'''

    def get(self, request, *args, **kwargs):
        logout(request)
        return HttpResponseRedirect(
            reverse_lazy('homepage'))


class PhotoAppView(TemplateView, LoginRequiredMixin):

    template_name = 'photoapp/photoapp.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context['facebook'] = FacebookUser.objects.get(
            contrib_user_id=request.user.id)
        context['photos'] = Photo.objects.all()
        context['Image_Effects'] = Image_Effects
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):

        title = request.POST["title"]
        image = request.FILES["image"]

        photo = Photo(title=title, user_id=request.user.id, image=image)
        photo.save()

        return HttpResponse("success", content_type="text/plain")


class EditPhotoView(TemplateView, LoginRequiredMixin):

    template_name = 'photoapp/editphoto.html'

    def get(self, request, *args, **kwargs):
        context = {}
        photoid = self.kwargs.get('id')

        try:
            photo = Photo.objects.get(id=photoid)
        except Photo.DoesNotExist:
            raise Http404

        effects = self.kwargs.get('effects')
        context['facebook'] = FacebookUser.objects.get(
            contrib_user_id=request.user.id)
        context['Image_Effects'] = Image_Effects
        context['photo'] = photo
        context['effects'] = Image_Effects[effects]
        return self.render_to_response(context)


class DeletePhotoView(View, LoginRequiredMixin):

    def get(self, request, *args, **kwargs):

        photoid = self.kwargs.get('id')
        public_id = self.kwargs.get('public_id')

        try:
            photo = Photo.objects.get(id=photoid)
        except Photo.DoesNotExist:
            raise Http404
        response, result = self.apidelete(public_id)

        if response == 'deleted':
            photo = Photo.objects.get(id=photoid)
            photo.delete()

            msg = "Photo sucessfully deleted."
            messages.add_message(request, messages.SUCCESS, msg)
            return HttpResponseRedirect(reverse_lazy('photoview'))

        else:
            msg = "server error please, try deleting again."
            messages.add_message(request, messages.ERROR, msg)
            return HttpResponseRedirect(reverse_lazy('photoview'))

    def apidelete(self, public_id):
            return api.delete_resources([public_id])


def custom_404(request):
    return render(request, 'photoapp/404.html')


def custom_500(request):
    return render(request, 'photoapp/500.html')
