from unittest.mock import patch

from rest_framework import status

from multi_tenancy.models import Plan, TeamBilling
from posthog.api.test.base import TransactionBaseTest
from posthog.models import Team, User


class TestTeamSignup(TransactionBaseTest):
    def setUp(self):
        super().setUp()
        User.objects.create(
            email="firstuser@posthog.com",
        )  # to ensure consistency in tests

    @patch("posthog.api.team.EE_AVAILABLE", False)
    @patch("messaging.tasks.process_team_signup_messaging.delay")
    @patch("posthog.api.team.posthoganalytics.identify")
    @patch("posthog.api.team.posthoganalytics.capture")
    def test_api_sign_up(self, mock_capture, mock_identify, mock_messaging):
        """
        Overridden from posthog.api.test.test_team to patch Redis call. Original test will not be run
        on multitenancy.
        """
        response = self.client.post(
            "/api/team/signup/",
            {
                "first_name": "John",
                "email": "hedgehog@posthog.com",
                "password": "notsecure",
                "company_name": "Hedgehogs United, LLC",
                "email_opt_in": False,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user: User = User.objects.order_by("-pk")[0]
        team: Team = user.team_set.all()[0]
        self.assertEqual(
            response.data,
            {
                "id": user.pk,
                "distinct_id": user.distinct_id,
                "first_name": "John",
                "email": "hedgehog@posthog.com",
            },
        )

        # Assert that the user was properly created
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.email, "hedgehog@posthog.com")
        self.assertEqual(user.email_opt_in, False)

        # Assert that the team was properly created
        self.assertEqual(team.name, "Hedgehogs United, LLC")

        # Assert that the sign up event & identify calls were sent to PostHog analytics
        mock_capture.assert_called_once_with(
            user.distinct_id,
            "user signed up",
            properties={"is_first_user": False, "is_team_first_user": True},
        )

        mock_identify.assert_called_once_with(
            user.distinct_id,
            properties={
                "email": "hedgehog@posthog.com",
                "realm": "cloud",
                "ee_available": False,
            },
        )

        # Assert that the user is logged in
        response = self.client.get("/api/user/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["email"], "hedgehog@posthog.com")

        # Assert that the password was correctly saved
        self.assertTrue(user.check_password("notsecure"))

        # Check that the process_team_signup_messaging task was fired
        mock_messaging.assert_called_once_with(user_id=user.pk, team_id=team.pk)

    @patch("posthoganalytics.capture")
    @patch("messaging.tasks.process_team_signup_messaging.delay")
    def test_default_user_sign_up(self, mock_messaging, mock_capture):
        """
        Most of the behavior is tested on the main repo @ posthog.api.test.test_team,
        goal of this test is to assert that the signup_messaging logic is called.
        """

        response = self.client.post(
            "/api/team/signup/",
            {
                "first_name": "John",
                "email": "hedgehog5@posthog.com",
                "password": "notsecure",
                "email_opt_in": False,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user: User = User.objects.order_by("-pk")[0]
        team: Team = user.team_set.all()[0]

        # Assert that the user was properly created
        self.assertEqual(user.email, "hedgehog5@posthog.com")

        # Assert that the sign up event & identify calls were sent to PostHog analytics
        mock_capture.assert_called_once_with(
            user.distinct_id,
            "user signed up",
            properties={"is_first_user": False, "is_team_first_user": True},
        )

        # Assert that the user is logged in
        response = self.client.get("/api/user/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["email"], "hedgehog5@posthog.com")

        # Check that the process_team_signup_messaging task was fired
        mock_messaging.assert_called_once_with(user_id=user.pk, team_id=team.pk)

    @patch("posthoganalytics.capture")
    @patch("messaging.tasks.process_team_signup_messaging.delay")
    def test_user_can_sign_up_with_a_custom_plan(self, mock_messaging, mock_capture):
        plan = Plan.objects.create(key="startup", default_should_setup_billing=True)

        response = self.client.post(
            "/api/team/signup/",
            {
                "first_name": "John",
                "email": "hedgehog@posthog.com",
                "password": "notsecure",
                "company_name": "Hedgehogs United, LLC",
                "plan": "startup",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user: User = User.objects.order_by("-pk")[0]
        team: Team = user.team_set.all()[0]

        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.email, "hedgehog@posthog.com")
        self.assertEqual(team.name, "Hedgehogs United, LLC")

        team_billing: TeamBilling = team.teambilling
        self.assertEqual(team_billing.plan, plan)
        self.assertEqual(team_billing.should_setup_billing, True)

        # Check that the process_team_signup_messaging task was fired
        mock_messaging.assert_called_once_with(user_id=user.pk, team_id=team.pk)

        # Check that we send the sign up event to PostHog analytics
        mock_capture.assert_called_once_with(
            user.distinct_id,
            "user signed up",
            properties={"is_first_user": False, "is_team_first_user": True},
        )

    @patch("posthoganalytics.capture")
    @patch("messaging.tasks.process_team_signup_messaging.delay")
    def test_user_can_sign_up_with_an_invalid_plan(self, mock_messaging, mock_capture):

        response = self.client.post(
            "/api/team/signup/",
            {
                "first_name": "Jane",
                "email": "hedgehog6@posthog.com",
                "password": "notsecure",
                "plan": "NOTVALID",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user: User = User.objects.order_by("-pk")[0]
        team: Team = user.team_set.all()[0]

        self.assertEqual(user.first_name, "Jane")
        self.assertEqual(user.email, "hedgehog6@posthog.com")
        self.assertFalse(
            TeamBilling.objects.filter(team=team).exists(),
        )  # TeamBilling is not created yet

        # Check that we send the sign up event to PostHog analytics
        mock_capture.assert_called_once_with(
            user.distinct_id,
            "user signed up",
            properties={"is_first_user": False, "is_team_first_user": True},
        )

        # Check that the process_team_signup_messaging task was fired
        mock_messaging.assert_called_once_with(user_id=user.pk, team_id=team.pk)

    @patch("messaging.tasks.process_team_signup_messaging.delay")
    @patch("posthog.api.team.posthoganalytics.identify")
    @patch("posthog.api.team.posthoganalytics.capture")
    def test_sign_up_multiple_teams_multi_tenancy(
        self, mock_capture, mock_identify, mock_messaging,
    ):

        # Create a user first to make sure additional users can be created
        User.objects.create(email="i_was_first@posthog.com")

        response = self.client.post(
            "/api/team/signup/",
            {
                "first_name": "John",
                "email": "multi@posthog.com",
                "password": "eruceston",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user: User = User.objects.order_by("-pk")[0]
        self.assertEqual(
            response.data,
            {
                "id": user.pk,
                "distinct_id": user.distinct_id,
                "first_name": "John",
                "email": "multi@posthog.com",
            },
        )

        # Assert that the user was properly created
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.email, "multi@posthog.com")

        # Assert that the sign up event & identify calls were sent to PostHog analytics
        mock_capture.assert_called_once_with(
            user.distinct_id,
            "user signed up",
            properties={"is_first_user": False, "is_team_first_user": True},
        )

        mock_identify.assert_called_once_with(
            user.distinct_id,
            properties={
                "email": "multi@posthog.com",
                "realm": "cloud",
                "ee_available": True,
            },
        )

        # Assert that the user is logged in
        response = self.client.get("/api/user/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["email"], "multi@posthog.com")

        # Assert that the password was correctly saved
        self.assertTrue(user.check_password("eruceston"))

        # Check that the process_team_signup_messaging task was fired
        mock_messaging.assert_called_once_with(
            user_id=user.pk, team_id=user.team_set.all()[0].pk,
        )
