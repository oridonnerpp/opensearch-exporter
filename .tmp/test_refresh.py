import unittest
from unittest.mock import patch
from fetch import refresh_aws_credentials, fetch_data
from botocore.exceptions import NoCredentialsError

class TestCredentialsRefresh(unittest.TestCase):

    @patch('refresh.boto3.Session')
    def test_credentials_refresh_success(self, mock_session):
        # Mocking the boto3.Session to simulate successful credentials refresh
        mock_session.return_value.get_credentials.return_value = mock_session
        refresh_aws_credentials()

        # Assertions to check if the credentials were refreshed successfully
        self.assertEqual(mock_session.get_credentials.call_count, 2)
        self.assertEqual(mock_session.get_credentials().token.call_count, 2)
        # Add more assertions if needed

    @patch('refresh.boto3.Session')
    @patch('refresh.client.search')
    def test_fetch_data_with_invalid_credentials(self, mock_search, mock_session):
        # Mocking the boto3.Session and OpenSearch client to simulate invalid credentials
        mock_session.return_value.get_credentials.return_value = mock_session
        mock_search.side_effect = NoCredentialsError()

        # Call fetch_data and check if it refreshes credentials before retrying
        with self.assertRaises(NoCredentialsError):
            fetch_data()

        # Assertions to check if the credentials were refreshed before retrying
        self.assertEqual(mock_session.get_credentials.call_count, 2)
        self.assertEqual(mock_session.get_credentials().token.call_count, 2)
        # Add more assertions if needed

if __name__ == '__main__':
    unittest.main()
