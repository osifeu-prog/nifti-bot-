import unittest
import core

class TestNiftiPureFunctions(unittest.TestCase):
    def test_ton_address_validation(self):
        valid = "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp"
        self.assertTrue(core.is_valid_ton(valid))
        self.assertFalse(core.is_valid_ton("bad"))

    def test_financial_math(self):
        self.assertEqual(core.platform_fee(10.0), 2.0)
        self.assertEqual(core.seller_amount(10.0), 8.0)

    def test_market_empty_fallback(self):
        core.load_lang()
        text = core.t("market_empty", "en")
        self.assertTrue(len(text) > 0)

    def test_settings_menu_key_exists(self):
        core.load_lang()
        self.assertIn("settings_menu", core.LANG["en"])

    def test_all_languages_loaded(self):
        core.load_lang()
        self.assertGreaterEqual(len(core.LANG), 8)

    def test_translation_fallback(self):
        core.load_lang()
        self.assertEqual(core.t("non_existent", "en"), "non_existent")

if __name__ == "__main__":
    unittest.main()
