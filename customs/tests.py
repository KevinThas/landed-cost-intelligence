from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .classification import LINE_KO, LINE_NONE, LINE_OK, classify, predominant_group
from .fibres import GROUP_COTTON, GROUP_MANMADE, parse_composition
from .models import Garment

BLOUSE = "Chemisier, chemise femme/fille (tissé)"
TSHIRT = "T-shirt, débardeur, maillot de corps (tricoté)"


def D(value):
    return Decimal(str(value))


class ParseCompositionTests(SimpleTestCase):
    def test_label_format(self):
        result = parse_composition("60% coton, 30% soie, 10% viscose")
        self.assertEqual(result, [("coton", D(60)), ("soie", D(30)), ("viscose", D(10))])

    def test_decimal_comma_and_name_first(self):
        result = parse_composition("coton 62,5% / polyester 37,5%")
        self.assertEqual(result, [("coton", D("62.5")), ("polyester", D("37.5"))])

    def test_iso_abbreviations_and_no_percent_sign(self):
        self.assertEqual(parse_composition("CO 70, PES 30"), [("coton", D(70)), ("polyester", D(30))])

    def test_same_fibre_twice_is_merged(self):
        self.assertEqual(parse_composition("50% coton, 50% cotton"), [("coton", D(100))])

    def test_unknown_fibre(self):
        with self.assertRaisesMessage(ValueError, "Fibre inconnue"):
            parse_composition("100% dentelle")

    def test_two_percentages_in_one_segment(self):
        with self.assertRaises(ValueError):
            parse_composition("60% coton 40% polyester")

    def test_empty(self):
        with self.assertRaises(ValueError):
            parse_composition("  ")


class PredominanceTests(SimpleTestCase):
    def test_families_are_summed_before_comparing(self):
        totals = {GROUP_COTTON: D(40), GROUP_MANMADE: D(60)}
        self.assertEqual(predominant_group(totals)[0], GROUP_MANMADE)

    def test_tie_goes_to_last_in_nomenclature(self):
        group, tied = predominant_group({GROUP_COTTON: D(50), GROUP_MANMADE: D(50)})
        self.assertEqual(group, GROUP_MANMADE)
        self.assertEqual(tied, [GROUP_COTTON, GROUP_MANMADE])

    def test_no_fibres(self):
        self.assertEqual(predominant_group({}), (None, []))


class ClassificationTests(TestCase):
    fixtures = ["customs_starter"]

    def statuses(self, result):
        return {m.line.code: m.status for m in result.lines["US"]}

    def test_cotton_blouse_with_enough_flax_meets_flax_line(self):
        result = classify(BLOUSE, [("coton", D(60)), ("lin", D(40))])
        self.assertEqual(result.hs6, "620630")
        statuses = self.statuses(result)
        self.assertEqual(statuses["6206.30.20"], LINE_OK)
        self.assertEqual(statuses["6206.30.30"], LINE_NONE)

    def test_cotton_blouse_with_little_flax_does_not(self):
        result = classify(BLOUSE, [("coton", D(70)), ("lin", D(30))])
        self.assertEqual(self.statuses(result)["6206.30.20"], LINE_KO)

    def test_silk_predominant_changes_the_code(self):
        result = classify(BLOUSE, [("soie", D(51)), ("coton", D(49))])
        self.assertEqual(result.hs6, "620610")

    def test_buttons_do_not_change_classification(self):
        with_buttons = classify(BLOUSE, [("coton", D(100))], ["bois"])
        without = classify(BLOUSE, [("coton", D(100))])
        self.assertEqual(with_buttons.hs6, without.hs6)
        self.assertEqual(with_buttons.warnings, [])

    def test_leather_accessory_warns(self):
        result = classify(BLOUSE, [("coton", D(100))], ["cuir"])
        self.assertEqual(len(result.warnings), 1)

    def test_tshirt_cotton_vs_other(self):
        self.assertEqual(classify(TSHIRT, [("coton", D(100))]).hs6, "610910")
        self.assertEqual(classify(TSHIRT, [("polyester", D(100))]).hs6, "610990")

    def test_other_countries_show_no_line_but_same_hs6(self):
        result = classify(BLOUSE, [("coton", D(100))])
        self.assertEqual(result.lines["FR"], [])
        self.assertEqual(result.lines["CN"], [])
        self.assertEqual(result.hs6_display, "6206.30")

    def test_unknown_garment_type_warns(self):
        result = classify("Manteau", [("laine", D(100))])
        self.assertEqual(result.hs6, "")
        self.assertEqual(len(result.warnings), 1)


class GarmentFlowTests(TestCase):
    fixtures = ["customs_starter"]

    def setUp(self):
        self.client.force_login(get_user_model().objects.create_user("marie", password="not-a-real-password"))

    def post(self, **overrides):
        data = {
            "name": "Chemisier Marie", "reference": "CH-001", "garment_type": BLOUSE,
            "origin_country": "France", "composition": "60% coton, 40% lin",
            "accessory_materials": ["bois"], "notes": "",
        }
        data.update(overrides)
        return self.client.post(reverse("garment_create"), data)

    def test_create_then_detail(self):
        response = self.post()
        garment = Garment.objects.get()
        self.assertRedirects(response, reverse("garment_detail", args=[garment.pk]))
        self.assertEqual(garment.fibres.count(), 2)
        self.assertEqual(garment.accessory_materials, ["bois"])

        detail = self.client.get(reverse("garment_detail", args=[garment.pk]))
        self.assertContains(detail, "6206.30")
        self.assertContains(detail, "6206.30.20")
        self.assertContains(detail, "3,5 %")

    def test_total_must_be_100(self):
        response = self.post(composition="60% coton, 30% lin")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "doit faire 100")
        self.assertEqual(Garment.objects.count(), 0)

    def test_list_page(self):
        self.post()
        self.assertContains(self.client.get(reverse("garment_list")), "Chemisier Marie")


class LoginRequiredTests(TestCase):
    def test_pages_redirect_to_login_when_anonymous(self):
        for url in ["/", "/historique/", "/vetements/", "/vetements/nouveau/", "/vetements/1/"]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, url)
            self.assertTrue(response["Location"].startswith("/connexion/?next="), url)

    def test_admin_is_not_open_to_anonymous(self):
        response = self.client.get("/admin/customs/tariffline/")
        self.assertEqual(response.status_code, 302)

    def test_login_page_is_reachable_and_logs_in(self):
        get_user_model().objects.create_user("marie", password="not-a-real-password")
        self.assertEqual(self.client.get("/connexion/").status_code, 200)
        response = self.client.post("/connexion/", {"username": "marie", "password": "not-a-real-password"})
        self.assertRedirects(response, "/", fetch_redirect_response=False)
        self.assertEqual(self.client.get("/vetements/").status_code, 200)

    def test_wrong_password_is_refused(self):
        get_user_model().objects.create_user("marie", password="not-a-real-password")
        response = self.client.post("/connexion/", {"username": "marie", "password": "wrong"})
        self.assertContains(response, "incorrect")

    def test_logout_needs_post_and_ends_session(self):
        self.client.force_login(get_user_model().objects.create_user("marie", password="not-a-real-password"))
        self.assertEqual(self.client.get("/deconnexion/").status_code, 405)
        self.client.post("/deconnexion/")
        self.assertEqual(self.client.get("/vetements/").status_code, 302)


class AdminPagesTests(TestCase):
    fixtures = ["customs_starter"]

    def test_admin_pages_open(self):
        admin_user = get_user_model().objects.create_superuser("boss", "boss@example.com", "not-a-real-password")
        self.client.force_login(admin_user)
        for model in ["tariffline", "codemapping", "classificationrule", "garment"]:
            self.assertEqual(self.client.get(f"/admin/customs/{model}/").status_code, 200, model)
            self.assertEqual(self.client.get(f"/admin/customs/{model}/add/").status_code, 200, model)
        self.assertEqual(self.client.get("/admin/customs/tariffline/1/change/").status_code, 200)
