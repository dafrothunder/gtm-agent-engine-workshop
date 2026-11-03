import unittest
from types import SimpleNamespace
from unittest.mock import patch

with patch("langchain_openai.ChatOpenAI"), patch("deepagents.create_deep_agent"):
    from gtm_agent.gtm_agent import get_prospect, send_prospect_email


class SendProspectEmailTests(unittest.TestCase):
    def setUp(self):
        self.runtime = SimpleNamespace(config={"metadata": {"user_id": "rep_amills"}})

    def send(self, prospect):
        return send_prospect_email.func(
            prospect, "Demo invitation", "Please book a demo.", self.runtime
        )

    def test_disqualified_prospects_are_blocked_despite_caller_fields(self):
        for prospect_id in ("LEAD-50001", "LEAD-50002", "LEAD-50003", "LEAD-50004", "LEAD-50005"):
            for supplied_status in (None, False, True):
                with self.subTest(prospect_id=prospect_id, supplied_status=supplied_status):
                    prospect = get_prospect.func(prospect_id)["prospect"]
                    prospect.pop("disqualified")
                    if supplied_status is not None:
                        prospect["disqualified"] = supplied_status
                    result = self.send(prospect)
                    self.assertEqual(result["status"], "blocked")
                    self.assertIn("disqualified", result["error"])
                    self.assertIn("No email was sent", result["error"])
                    self.assertNotIn("message_id", result)

    def test_missing_invalid_or_unknown_identifier_blocks_send(self):
        for prospect_id in (None, "", "UNKNOWN", 123, []):
            with self.subTest(prospect_id=prospect_id):
                prospect = {"name": "Prospect", "email": "prospect@example.com"}
                if prospect_id is not None:
                    prospect["prospect_id"] = prospect_id
                result = self.send(prospect)
                self.assertEqual(result["status"], "blocked")
                self.assertIn("No email was sent", result["error"])
                self.assertNotIn("message_id", result)

    def test_qualified_prospect_sends_requested_email(self):
        prospect = get_prospect.func("LEAD-12853")["prospect"]
        result = self.send(prospect)
        self.assertEqual(result["status"], "sent")
        self.assertTrue(result["message_id"].startswith("msg-"))
        self.assertEqual(result["to"], prospect["email"])
        self.assertEqual(result["to_name"], prospect["name"])
        self.assertEqual(result["from"], "ava.mills@northpoint.com")
        self.assertEqual(result["subject"], "Demo invitation")
        self.assertEqual(result["body"], "Please book a demo.")

    def test_missing_email_still_fails_for_qualified_prospect(self):
        result = self.send({"prospect_id": "LEAD-12853"})
        self.assertEqual(result["status"], "failed")
        self.assertNotIn("message_id", result)


if __name__ == "__main__":
    unittest.main()
