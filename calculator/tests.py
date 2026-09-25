from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Calculation, TariffCategory


class CalculatorTests(TestCase):
    def setUp(self):
        self.client.force_login(get_user_model().objects.create_user("u", password="not-a-real-password"))
        self.category = TariffCategory.objects.create(
            name="Catégorie de test", mfn_base_rate="0.05", section_301_rate="0.10", additional_surtax_rate="0.10",
        )

    def post(self, **overrides):
        data = {
            "category": self.category.pk, "product_name": "Test", "fob_unit_price": "10", "quantity": "100",
            "freight_cost_total": "300", "amazon_referral_pct": "0.15", "amazon_fba_fee_per_unit": "3",
            "target_sale_price": "30",
        }
        data.update(overrides)
        return self.client.post(reverse("calculate"), data)

    def test_engine_matches_hand_calculation(self):
        # coût produit 1000 ; droits 25 % = 250 ; landed 1550 ; 15,50 / pièce
        # break-even (15,5 + 3) / 0,85 ; marge 30 - 15,5 - 3 - 4,5 = 7 ; ROI 7 / 15,5
        self.post()
        calculation = Calculation.objects.get()
        self.assertEqual(calculation.product_cost_total, Decimal("1000"))
        self.assertEqual(calculation.duty_amount, Decimal("250"))
        self.assertEqual(calculation.landed_cost_total, Decimal("1550"))
        self.assertEqual(calculation.landed_cost_per_unit, Decimal("15.5"))
        self.assertEqual(round(calculation.breakeven_price, 2), Decimal("21.76"))
        self.assertEqual(calculation.margin_per_unit, Decimal("7"))
        self.assertEqual(round(calculation.roi_pct, 2), Decimal("45.16"))

    def test_result_shows_the_rate_as_a_percentage(self):
        response = self.client.get(reverse("calculation_result", args=[self.post() and Calculation.objects.get().pk]))
        self.assertContains(response, "taux total effectif : 25 %")

    def test_rate_typed_as_percent_instead_of_fraction_is_refused_with_advice(self):
        response = self.post(amazon_referral_pct="15")
        self.assertEqual(Calculation.objects.count(), 0)
        self.assertContains(response, "écrivez 0,15 pour 15 %")

    def test_absurd_values_are_refused(self):
        for field, value in [("quantity", "0"), ("fob_unit_price", "-10"), ("fob_unit_price", "0"),
                             ("freight_cost_total", "-1"), ("amazon_fba_fee_per_unit", "-1"),
                             ("target_sale_price", "0"), ("amazon_referral_pct", "-0.1")]:
            self.post(**{field: value})
            self.assertEqual(Calculation.objects.count(), 0, f"{field}={value} aurait dû être refusé")

    def test_valid_extremes_are_accepted(self):
        self.post(freight_cost_total="0", amazon_fba_fee_per_unit="0", target_sale_price="", amazon_referral_pct="0")
        self.assertEqual(Calculation.objects.count(), 1)

    def test_unknown_result_is_a_404_not_a_server_error(self):
        self.assertEqual(self.client.get(reverse("calculation_result", args=[9999])).status_code, 404)

    def test_calculator_lives_under_calcul_and_history_lists_calculations(self):
        self.assertEqual(reverse("calculate"), "/calcul/")
        self.post()
        self.assertContains(self.client.get(reverse("calculation_history")), "Test")


class HomePageTests(TestCase):
    def test_home_redirects_to_garment_classification(self):
        self.client.force_login(get_user_model().objects.create_user("u", password="not-a-real-password"))
        response = self.client.get("/")
        self.assertRedirects(response, reverse("garment_create"), fetch_redirect_response=False)
