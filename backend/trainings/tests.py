import tempfile
from pathlib import Path
from unittest import mock

from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .models import Photo, Training


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


# Najmniejszy poprawny GIF — Pillow sprawdza, czy plik jest obrazkiem
GIF = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'


class StaffEditTests(TestCase):
    def setUp(self):
        self.media = tempfile.TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        override = self.settings(MEDIA_ROOT=self.media.name)
        override.enable()
        self.addCleanup(override.disable)
        self.admin = User.objects.create_superuser('admin@example.com', 'haslo-testowe-123')

    def post_data(self, **extra):
        return {'kind': 'camp', 'title': 'Camp Łeba', 'description': 'Tydzień nad morzem', 'is_active': 'on', 'order': 0, **extra}

    def test_only_staff_can_add(self):
        url = reverse('trainings:add')
        self.assertRedirects(self.client.get(url), f"{reverse('accounts:login')}?next={url}")

        self.client.force_login(User.objects.create_user('jan@example.com', 'haslo-testowe-123'))
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_admin_adds_camp_with_photo(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        self.client.force_login(self.admin)
        photo = SimpleUploadedFile('morze.gif', GIF, content_type='image/gif')
        response = self.client.post(reverse('trainings:add'), self.post_data(image=photo))

        camp = Training.objects.get(title='Camp Łeba')
        self.assertRedirects(response, '/szkolenia/#camp-leba', fetch_redirect_response=False)
        self.assertEqual(camp.kind, Training.Kind.CAMP)
        self.assertTrue(camp.image.name.startswith('szkolenia/morze'))
        self.assertContains(self.client.get(reverse('trainings:list')), camp.image.url)

    def test_same_title_gets_unique_slug_and_edit_keeps_it(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('trainings:add'), self.post_data())
        self.client.post(reverse('trainings:add'), self.post_data())
        slugs = sorted(Training.objects.filter(title='Camp Łeba').values_list('slug', flat=True))
        self.assertEqual(slugs, ['camp-leba', 'camp-leba-2'])

        camp = Training.objects.get(slug='camp-leba')
        self.client.post(reverse('trainings:edit', args=[camp.pk]), self.post_data(title='Camp Łeba 2027'))
        camp.refresh_from_db()
        self.assertEqual((camp.title, camp.slug), ('Camp Łeba 2027', 'camp-leba'))

    def test_add_form_presets_camp_and_page_shows_buttons(self):
        self.client.force_login(self.admin)
        form = self.client.get(reverse('trainings:add') + '?rodzaj=camp').context['form']
        self.assertEqual(form.initial['kind'], 'camp')

        page = self.client.get(reverse('trainings:list'))
        self.assertContains(page, '+ Dodaj szkolenie')
        self.assertContains(page, '+ Dodaj camp')
        self.assertContains(page, 'Edytuj wpis')
        self.assertContains(page, reverse('trainings:delete', args=[Training.objects.first().pk]))

    def test_buttons_hidden_for_visitors(self):
        page = self.client.get(reverse('trainings:list'))
        self.assertNotContains(page, '+ Dodaj')
        self.assertNotContains(page, 'Edytuj wpis')

    def test_admin_deletes_entry(self):
        camp = Training.objects.create(kind='camp', title='Do usunięcia', slug='do-usuniecia')
        self.client.force_login(self.admin)

        self.assertEqual(self.client.get(reverse('trainings:delete', args=[camp.pk])).status_code, 405)
        self.client.post(reverse('trainings:delete', args=[camp.pk]))
        self.assertFalse(Training.objects.filter(pk=camp.pk).exists())

    def test_replacing_and_removing_photo_cleans_old_file(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        self.client.force_login(self.admin)
        self.client.post(reverse('trainings:add'), self.post_data(image=SimpleUploadedFile('a.gif', GIF)))
        camp = Training.objects.get(title='Camp Łeba')
        first = camp.image.path
        edit = reverse('trainings:edit', args=[camp.pk])

        self.client.post(edit, self.post_data())  # bez nowego pliku — zdjęcie zostaje
        camp.refresh_from_db()
        self.assertEqual(camp.image.path, first)

        self.client.post(edit, self.post_data(image=SimpleUploadedFile('b.gif', GIF)))
        camp.refresh_from_db()
        self.assertIn('/b', camp.image.name)
        self.assertFalse(Path(first).exists())

        second = camp.image.path
        self.client.post(edit, self.post_data(remove_image='on'))
        camp.refresh_from_db()
        self.assertFalse(camp.image)
        self.assertFalse(Path(second).exists())


class PhotoUploadTests(TestCase):
    def setUp(self):
        self.media = tempfile.TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        override = self.settings(MEDIA_ROOT=self.media.name)
        override.enable()
        self.addCleanup(override.disable)
        # Puste foldery public/ — testujemy tylko zdjęcia wgrane na stronie
        empty = tempfile.TemporaryDirectory()
        self.addCleanup(empty.cleanup)
        for name in ('GALLERY_DIR', 'CAMP_PHOTO_DIR'):
            patcher = mock.patch(f'trainings.views.{name}', Path(empty.name))
            patcher.start()
            self.addCleanup(patcher.stop)
        self.admin = User.objects.create_superuser('admin@example.com', 'haslo-testowe-123')

    def gif(self, name):
        from django.core.files.uploadedfile import SimpleUploadedFile
        return SimpleUploadedFile(name, GIF, content_type='image/gif')

    def test_only_staff_can_upload(self):
        self.client.force_login(User.objects.create_user('jan@example.com', 'haslo-testowe-123'))
        response = self.client.post(reverse('trainings:gallery_upload'), {'images': [self.gif('a.gif')]})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Photo.objects.exists())

    def test_admin_uploads_several_photos_and_deletes_one(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('trainings:gallery_upload'), {'images': [self.gif('a.gif'), self.gif('b.gif')]})
        self.assertRedirects(response, '/szkolenia/#galeria', fetch_redirect_response=False)

        first, second = Photo.objects.all()
        page = self.client.get(reverse('trainings:list'))
        self.assertEqual([p['src'] for p in page.context['gallery']], [first.image.url, second.image.url])
        self.assertContains(page, reverse('trainings:photo_delete', args=[first.pk]))

        path = Path(first.image.path)
        self.client.post(reverse('trainings:photo_delete', args=[first.pk]))
        self.assertEqual(list(Photo.objects.all()), [second])
        self.assertFalse(path.exists())

    def test_upload_rejects_non_image(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        self.client.force_login(self.admin)
        response = self.client.post(
            reverse('trainings:gallery_upload'), {'images': [SimpleUploadedFile('x.jpg', b'to nie obrazek')]}, follow=True,
        )
        self.assertFalse(Photo.objects.exists())
        self.assertEqual(len(list(response.context['messages'])), 1)

    def test_camp_cover_replaces_previous_and_can_be_removed(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('trainings:camp_cover_upload'), {'image': self.gif('a.gif')})
        old_path = Path(Photo.objects.get().image.path)
        self.client.post(reverse('trainings:camp_cover_upload'), {'image': self.gif('b.gif')})

        cover = Photo.objects.get()
        self.assertEqual(cover.place, Photo.Place.CAMP_COVER)
        self.assertFalse(old_path.exists())
        page = self.client.get(reverse('trainings:list'))
        self.assertEqual(page.context['camp_photo'], cover.image.url)
        self.assertEqual(page.context['gallery'], [])  # kafelek nie trafia do galerii

        self.client.post(reverse('trainings:photo_delete', args=[cover.pk]))
        self.assertEqual(self.client.get(reverse('trainings:list')).context['camp_photo'], '')

    def test_visitors_see_no_upload_controls(self):
        page = self.client.get(reverse('trainings:list'))
        self.assertNotContains(page, 'Dodaj zdjęcia')
        self.assertNotContains(page, 'Zmień zdjęcie')
