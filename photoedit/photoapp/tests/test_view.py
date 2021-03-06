'''Script used to test app functionality. '''

from io import BytesIO
from PIL import Image

from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.importlib import import_module
from django.core.urlresolvers import reverse_lazy

from photoapp.models import FacebookUser, Photo
from photoapp.views import FacebookLogin, PhotoAppView


def create_test_image():
    file = BytesIO()
    image = Image.new('RGBA', size=(50, 50), color=(155, 0, 0))
    image.save(file, 'png')
    file.name = 'test.png'
    file.seek(0)
    return file


class UserSetupTestCase(TestCase):

    '''Test Setup used by subclasses, parameters already defined.'''

    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.user1 = User.objects.create(
            first_name='John',
            last_name='doe',
            username='Johndoe',
            email='johndoe@doe.com')
        self.facebook_user1 = FacebookUser.objects.create(
            facebook_id=1,
            contrib_user=self.user1)

        self.data = {
            'first_name': 'andela',
            'last_name': 'andela',
            'email': 'email@email.com',
            'id': 2,
            'picture[data][url]': 'https://fbkamaihd.net/hprofile'
        }
        self.file = create_test_image()

        self.photo = Photo.objects.create(title='title',
                                          user_id=1,
                                          image=self.file.name)


class UserActionTestCase(UserSetupTestCase):

    '''Test User can perform authentication action. '''

    def test_non_existing_user_login(self):

        request = self.factory.post('/photoapp/login/', self.data)
        engine = import_module(settings.SESSION_ENGINE)
        session_key = None
        request.session = engine.SessionStore(session_key)

        # assert that user loggedIn successfully
        response = FacebookLogin.as_view()(request)
        self.assertEquals(response.status_code, 200)

    def test_existing_user_login(self):
        data = {
            'first_name': 'John',
            'last_name': 'doe',
            'email': 'johndoe@doe.com',
            'id': 1,
            'picture[data][url]': 'https://fbkamdsaihd.net/hprofile'
        }
        request = self.factory.post('/photoapp/login/', data)
        engine = import_module(settings.SESSION_ENGINE)
        session_key = None
        request.session = engine.SessionStore(session_key)
        response = FacebookLogin.as_view()(request)
        self.assertEquals(response.status_code, 200)

    def test_model_creation(self):

        # assert that user does not exist in the database
        facebook_user2 = FacebookUser.objects.filter(id=2)
        self.assertEqual(len(facebook_user2), 0)

        # assert that user was successfully created and saved in db
        user2 = User.objects.create_user(
            username=self.data['first_name'],
            email=self.data['email'])
        facebook_user2 = FacebookUser.objects.create(
            facebook_id=self.data['id'], contrib_user=user2)
        facebook_user2 = FacebookUser.objects.filter(id=2)
        self.assertEqual(len(facebook_user2), 1)

    def test_user_signout(self):

        response = self.client.get(reverse_lazy('signout'))
        self.assertEquals(response.status_code, 302)

    def test_user_view_homepage(self):

        response = self.client.get(reverse_lazy('homepage'))
        self.assertEquals(response.status_code, 200)

    def test_user_view_photopage(self):
        request = self.factory.get(reverse_lazy('photoview'))
        request.user = self.user1
        response = PhotoAppView.as_view()(request)
        self.assertEquals(response.status_code, 200)
