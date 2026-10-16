import tempfile
from pathlib import Path
from unittest import mock

from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .models import Training


class TrainingTests(TestCase):
    def setUp(self):
        # Pięć szkoleń dodaje migracja 0002
        self.camp = Training.objects.create(
            kind=Training.Kind.CAMP, title='Camp Mazury', slug='camp-mazury', date_text='12–14 czerwca 2026',
            place='Ełk', price=1200, points='Trzy treningi dziennie\n\nAnaliza wideo',
        )
        self.hidden = Training.objects.create(title='Kurs w przygotowaniu', slug='w-przygotowaniu', is_active=False)

    def test_page_lists_courses_and_camps(self):
        response = self.client.get(reverse('trainings:list'))

        self.assertContains(response, 'Trener Personalny — Kurs Certyfikowany')
        self.assertContains(response, 'id="camp-mazury"')
        self.assertContains(response, '12–14 czerwca 2026')
        self.assertContains(response, '1200 zł')
        self.assertEqual(response.context['camps'], [self.camp])

    def test_hidden_entry_is_visible_only_to_staff(self):
        self.assertNotContains(self.client.get(reverse('trainings:list')), 'Kurs w przygotowaniu')

        self.client.force_login(User.objects.create_superuser('admin@example.com', 'haslo-testowe-123'))
        response = self.client.get(reverse('trainings:list'))

        self.assertContains(response, 'Kurs w przygotowaniu')
        self.assertContains(response, 'Ukryte — podgląd')

    def test_json_for_homepage_skips_hidden(self):
        self.client.force_login(User.objects.create_superuser('admin@example.com', 'haslo-testowe-123'))

        items = self.client.get(reverse('trainings:list_json')).json()['items']

        titles = [item['title'] for item in items]
        self.assertIn('Camp Mazury', titles)
        self.assertNotIn('Kurs w przygotowaniu', titles)
        self.assertEqual(items[titles.index('Camp Mazury')]['url'], '/szkolenia/#camp-mazury')

    def test_points_and_contact_link(self):
        self.assertEqual(self.camp.point_list, ['Trzy treningi dziennie', 'Analiza wideo'])
        self.assertEqual(self.camp.contact_url, 'mailto:info@trainingculture.pl?subject=Camp%3A%20Camp%20Mazury')

    def test_old_static_address_redirects(self):
        response = self.client.get('/szkolenia.html')
        self.assertRedirects(response, reverse('trainings:list'), status_code=301)


class GalleryTests(TestCase):
    def test_gallery_lists_images_from_folder(self):
        with tempfile.TemporaryDirectory() as folder:
            for name in ('b.jpeg', 'WhatsApp Image 1.jpg', 'notatka.txt'):
                (Path(folder) / name).touch()
            with mock.patch('trainings.views.GALLERY_DIR', Path(folder)):
                response = self.client.get(reverse('trainings:list'))

        self.assertEqual(
            [photo['src'] for photo in response.context['gallery']],
            ['/images/szkolenia/WhatsApp%20Image%201.jpg', '/images/szkolenia/b.jpeg'],
        )
        self.assertContains(response, 'id="gallery-data"')
